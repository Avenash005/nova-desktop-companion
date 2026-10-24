"""
Hardware-Aware LoRA/QLoRA Fine-Tuning Pipeline for NOVA Desktop Companion
========================================================================
Fine-tunes Qwen2.5-1.5B-Instruct using LoRA/QLoRA on consumer NVIDIA GPUs
(optimized for NVIDIA GeForce RTX 4060 with 8GB VRAM on Windows).

Features:
- Validates dataset schema and ChatML formatting.
- Configures LoRA adapters on attention and MLP projections.
- Hardware-aware memory management (fp16/bf16, gradient checkpointing, small batch size).
- Tracks peak GPU memory and records training metrics to training_summary.json.
- Supports --smoke_test for rapid pipeline validation.
- Exports complete adapter weights and tokenizer artifacts for inference.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any


def load_jsonl(filepath: str) -> List[Dict[str, Any]]:
    """Load JSONL dataset file and validate records."""
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if "messages" in data and len(data["messages"]) >= 2:
                    records.append(data)
                else:
                    print(f"[Warning] Skipping malformed record on line {idx}")
            except json.JSONDecodeError as e:
                print(f"[Warning] Invalid JSON on line {idx}: {e}")
    return records


def print_gpu_diagnostics():
    """Display GPU diagnostics and VRAM availability."""
    import torch
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        free_vram_gb = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / (1024**3)
        print(f"[Hardware] GPU: {gpu_name}")
        print(f"[Hardware] Total VRAM: {total_vram_gb:.2f} GB | Currently Free: {free_vram_gb:.2f} GB")
        print(f"[Hardware] CUDA Version: {torch.version.cuda} | Device Capability: {torch.cuda.get_device_capability(0)}")
        return True
    else:
        print("[Hardware] Warning: No CUDA GPU detected. Running on CPU.")
        return False


def run_training(
    model_id: str = "Qwen/Qwen2.5-1.5B-Instruct",
    train_data_path: str = "training/dataset/train.jsonl",
    val_data_path: str = "training/dataset/validation.jsonl",
    output_dir: str = "models/nova_adapter",
    epochs: int = 3,
    batch_size: int = 1,
    gradient_accumulation_steps: int = 4,
    learning_rate: float = 2e-4,
    max_length: int = 512,
    lora_r: int = 16,
    lora_alpha: int = 32,
    lora_dropout: float = 0.05,
    use_4bit: bool = False,
    smoke_test: bool = False,
):
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForSeq2Seq
    )
    from peft import (
        LoraConfig,
        get_peft_model,
        TaskType
    )

    start_time = time.time()
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("  NOVA FINE-TUNING PIPELINE (LoRA/QLoRA)")
    print("=" * 60)
    has_gpu = print_gpu_diagnostics()

    if smoke_test:
        print("[Config] RUNNING IN SMOKE TEST MODE (2 steps, fast verification)")
        epochs = 1

    # 1. Load Dataset
    print(f"\n[1/5] Loading datasets...")
    train_records = load_jsonl(train_data_path)
    val_records = load_jsonl(val_data_path)
    print(f"      Loaded {len(train_records)} training and {len(val_records)} validation samples.")

    # 2. Load Tokenizer
    print(f"\n[2/5] Loading tokenizer for {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 3. Format inputs with ChatML template
    print(f"\n[3/5] Preprocessing and tokenizing conversation turns...")
    def preprocess_conversations(records):
        features = []
        for r in records:
            messages = r["messages"]
            formatted_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            tokenized = tokenizer(
                formatted_text,
                max_length=max_length,
                truncation=True,
                padding="max_length"
            )
            tokenized["labels"] = tokenized["input_ids"][:]
            features.append(tokenized)
        return features

    from datasets import Dataset
    train_dataset = Dataset.from_list(preprocess_conversations(train_records))
    val_dataset = Dataset.from_list(preprocess_conversations(val_records))

    # 4. Load Base Model and Apply LoRA
    print(f"\n[4/5] Loading base model: {model_id}...")
    torch_dtype = torch.float16 if has_gpu else torch.float32

    model_kwargs = {
        "trust_remote_code": True,
        "torch_dtype": torch_dtype,
    }
    if has_gpu:
        model_kwargs["device_map"] = "auto"

    if use_4bit and has_gpu:
        from transformers import BitsAndBytesConfig
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch_dtype,
            bnb_4bit_use_double_quant=True
        )
        model_kwargs["quantization_config"] = bnb_config
        print("      4-bit QLoRA quantization enabled.")

    base_model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
    base_model.gradient_checkpointing_enable()
    if hasattr(base_model, "enable_input_require_grads"):
        base_model.enable_input_require_grads()


    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none"
    )

    model = get_peft_model(base_model, lora_config)
    trainable_params, all_param = model.get_nb_trainable_parameters()
    print(f"      Trainable parameters: {trainable_params:,} / {all_param:,} ({100 * trainable_params / all_param:.3f}%)")

    # 5. Training Setup
    print(f"\n[5/5] Initializing Trainer...")
    max_steps = 2 if smoke_test else -1
    training_args = TrainingArguments(
        output_dir=str(out_path / "checkpoints"),
        num_train_epochs=epochs,
        max_steps=max_steps,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        learning_rate=learning_rate,
        fp16=has_gpu,
        logging_steps=1 if smoke_test else 5,
        eval_strategy="steps" if smoke_test else "epoch",
        eval_steps=1 if smoke_test else None,
        save_strategy="steps" if smoke_test else "epoch",
        save_total_limit=2,
        dataloader_drop_last=False,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8, return_tensors="pt")
    )

    print("\n[Train] Starting training run...")
    train_result = trainer.train()

    # Peak VRAM
    peak_vram_mb = 0
    if has_gpu:
        peak_vram_mb = round(torch.cuda.max_memory_allocated(0) / (1024**2), 2)
        print(f"[Train] Peak GPU Memory: {peak_vram_mb} MB")

    total_duration = round(time.time() - start_time, 2)
    print(f"[Train] Training completed in {total_duration} seconds.")

    # Save Adapter Artifacts
    print(f"\n[Save] Saving LoRA adapter to {output_dir}...")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    summary = {
        "status": "COMPLETED",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "base_model": model_id,
        "adapter_dir": output_dir,
        "smoke_test": smoke_test,
        "hyperparameters": {
            "epochs": epochs,
            "batch_size": batch_size,
            "gradient_accumulation_steps": gradient_accumulation_steps,
            "learning_rate": learning_rate,
            "max_length": max_length,
            "lora_r": lora_r,
            "lora_alpha": lora_alpha,
            "lora_dropout": lora_dropout
        },
        "metrics": {
            "training_loss": round(train_result.training_loss, 4) if hasattr(train_result, "training_loss") else None,
            "total_training_time_sec": total_duration,
            "peak_vram_mb": peak_vram_mb,
            "trainable_parameters": trainable_params,
            "total_parameters": all_param
        }
    }

    summary_file = out_path / "training_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[Save] Training summary saved to {summary_file}")
    print("=" * 60 + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description="NOVA LoRA Fine-Tuning Pipeline")
    parser.add_argument("--model_id", default="Qwen/Qwen2.5-1.5B-Instruct", help="Base model identifier")
    parser.add_argument("--train_data", default="training/dataset/train.jsonl", help="Train dataset JSONL")
    parser.add_argument("--val_data", default="training/dataset/validation.jsonl", help="Validation dataset JSONL")
    parser.add_argument("--output_dir", default="models/nova_adapter", help="Output adapter directory")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch_size", type=int, default=1, help="Per-device batch size")
    parser.add_argument("--grad_accum", "--gradient_accumulation_steps", dest="grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", "--learning_rate", dest="lr", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--max_length", type=int, default=512, help="Max sequence token length")
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA rank r")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA alpha scaling")
    parser.add_argument("--use_4bit", action="store_true", help="Use 4-bit QLoRA")
    parser.add_argument("--smoke_test", action="store_true", help="Run short smoke test (2 steps)")
    args = parser.parse_args()

    run_training(
        model_id=args.model_id,
        train_data_path=args.train_data,
        val_data_path=args.val_data,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        max_length=args.max_length,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        use_4bit=args.use_4bit,
        smoke_test=args.smoke_test
    )


if __name__ == "__main__":
    main()
