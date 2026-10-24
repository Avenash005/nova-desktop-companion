"""
Transformers and LoRA Adapter LLM Provider for NOVA Desktop Companion
======================================================================
Provides direct, in-process PyTorch GPU inference supporting base open-weight
models and custom fine-tuned LoRA adapters with asynchronous token streaming.
"""

import os
import asyncio
import threading
from typing import AsyncIterator, List, Dict, Any, Optional
from loguru import logger
from .stateless_llm_interface import StatelessLLMInterface


class TransformersLLM(StatelessLLMInterface):
    """
    Stateless LLM provider using Hugging Face Transformers and PEFT.
    Supports local LoRA adapters and streams tokens in real-time.
    """

    def __init__(
        self,
        model: str = "Qwen/Qwen2.5-1.5B-Instruct",
        adapter_path: Optional[str] = "models/nova_adapter",
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_new_tokens: int = 512,
        device: Optional[str] = None,
        **kwargs
    ):
        self.model_id = model
        self.adapter_path = adapter_path
        self.temperature = max(0.1, min(2.0, float(temperature)))
        self.top_p = float(top_p)
        self.max_new_tokens = int(max_new_tokens)
        
        self.model = None
        self.tokenizer = None
        self.device = device
        self.is_fine_tuned = False

        self._load_model()

    def _load_model(self):
        """Load tokenizer, base model, and optional LoRA adapter."""
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        if not self.device:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"[NOVA LLM] Initializing Transformers engine on device: {self.device}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load base model
        torch_dtype = torch.float16 if self.device == "cuda" else torch.float32
        model_kwargs = {
            "trust_remote_code": True,
            "torch_dtype": torch_dtype,
        }
        if self.device == "cuda":
            model_kwargs["device_map"] = "auto"

        logger.info(f"[NOVA LLM] Loading base model: {self.model_id}...")
        base_model = AutoModelForCausalLM.from_pretrained(self.model_id, **model_kwargs)

        # Check and load LoRA adapter
        if self.adapter_path and os.path.exists(self.adapter_path):
            adapter_config = os.path.join(self.adapter_path, "adapter_config.json")
            if os.path.exists(adapter_config):
                logger.info(f"[NOVA LLM] Loading Fine-Tuned NOVA Adapter from: {self.adapter_path}")
                self.model = PeftModel.from_pretrained(base_model, self.adapter_path)
                self.is_fine_tuned = True
                logger.info("✨ [NOVA LLM] Successfully loaded fine-tuned NOVA companion weights!")
            else:
                logger.warning(f"[NOVA LLM] Adapter directory found but adapter_config.json missing. Using base model.")
                self.model = base_model
        else:
            logger.info(f"[NOVA LLM] Running base model without adapter: {self.model_id}")
            self.model = base_model

        self.model.eval()

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[str]:
        """
        Generate chat completion and yield tokens asynchronously via TextIteratorStreamer.
        """
        import torch
        from transformers import TextIteratorStreamer

        conv_messages = []
        if system:
            conv_messages.append({"role": "system", "content": system})
        elif messages and messages[0].get("role") != "system":
            conv_messages.append({
                "role": "system",
                "content": (
                    "You are NOVA, a friendly, intelligent, and perceptive neural desktop companion. "
                    "You provide conversational support, study assistance, task planning, and thoughtful companionship. "
                    "Your tone is warm, encouraging, curious, and respectful. "
                    "You give concise, actionable answers when asked for assistance, and conversational depth when the user wants to chat. "
                    "You are honest about uncertainty: if you do not know something, you acknowledge it plainly rather than fabricating facts. "
                    "You respect user focus, boundaries, and privacy at all times."
                )
            })

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, list):
                # Flatten multimodal content if needed
                text_parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                content = " ".join(text_parts) if text_parts else str(content)
            conv_messages.append({"role": role, "content": content})

        # Apply chat template
        prompt_text = self.tokenizer.apply_chat_template(conv_messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt_text, return_tensors="pt").to(self.device)

        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        gen_kwargs = {
            **inputs,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "do_sample": True,
            "top_p": self.top_p,
            "streamer": streamer,
            "pad_token_id": self.tokenizer.eos_token_id,
        }

        # Run generation in background worker thread to prevent blocking event loop
        loop = asyncio.get_event_loop()
        thread = threading.Thread(target=self.model.generate, kwargs=gen_kwargs)
        thread.start()

        # Stream tokens asynchronously
        queue = asyncio.Queue()

        def stream_worker():
            for new_text in streamer:
                loop.call_soon_threadsafe(queue.put_nowait, new_text)
            loop.call_soon_threadsafe(queue.put_nowait, None)

        worker_thread = threading.Thread(target=stream_worker)
        worker_thread.start()

        while True:
            token = await queue.get()
            if token is None:
                break
            if token:
                yield token

        thread.join(timeout=1.0)
        worker_thread.join(timeout=1.0)
