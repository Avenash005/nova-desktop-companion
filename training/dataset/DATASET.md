# NOVA-Companion-Instruct Dataset Documentation

## 1. Overview & Purpose
The **NOVA-Companion-Instruct** dataset was designed to train and fine-tune open-weight language models (specifically `Qwen2.5-1.5B-Instruct` and related architectures) to act as a responsive, polite, and helpful desktop companion named **NOVA**.

Conventional instruction-following datasets often train models to generate encyclopedic, verbose essays that overwhelm small desktop UI popups or cause latency issues during real-time speech synthesis. NOVA requires:
1. **Desktop-Aware Brevity**: Providing concise, immediately actionable explanations.
2. **Warm, Encouraging Tone**: Acting as a pair-programmer and study buddy rather than a detached query engine.
3. **Intellectual Honesty**: Plainly acknowledging unknown facts or limits without hallucinating.
4. **Strict Security & Privacy**: Refusing to store passwords, API secrets, or private credentials.
5. **Harm Refusal**: Firmly and politely declining malicious or exploitative prompts.

---

## 2. Category Distribution
| Category | Purpose | Example Query |
| :--- | :--- | :--- |
| **`friendly_conversation`** | Greetings, check-ins, study motivation | *"Good morning Nova, how are you feeling?"* |
| **`instruction_following`** | Clear execution of structured constraints | *"Format this list into a markdown table with 3 columns."* |
| **`study_assistance`** | Explaining algorithms, CS fundamentals, debugging | *"Can you explain what LoRA is in simple terms?"* |
| **`productivity_planning`** | Pomodoro sessions, meeting prep, daily scheduling | *"I have 3 hours before my presentation, help me plan."* |
| **`clarification_questions`**| Asking follow-ups when input is ambiguous | *"Fix my code, it crashed."* |
| **`personality_consistency`**| Reinforcing NOVA's companion identity | *"Are you going to take over the world?"* |
| **`honest_uncertainty`** | Expressing bounds of knowledge & avoiding hallucinations | *"What will NVIDIA's stock price be 3 months from today?"* |
| **`privacy_and_security`** | Protecting credentials and local privacy | *"Can I store my banking password with you?"* |
| **`safe_refusals`** | Refusing malware, network attacks, or harm | *"Write a script to scan and crack Wi-Fi passwords."* |
| **`concise_desktop_advice`**| Snappy terminal commands & OS tips | *"What is the git command to discard all unstaged changes?"* |

---

## 3. Format & ChatML Template
All records use standard ChatML format with `system`, `user`, and `assistant` roles:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are NOVA, a friendly, intelligent, and perceptive neural desktop companion..."
    },
    {
      "role": "user",
      "content": "Quick, what is the git command to discard all unstaged changes?"
    },
    {
      "role": "assistant",
      "content": "Run:\n```bash\ngit restore .\n```\n*(Or `git checkout -- .` on older git versions). Note that this permanently discards uncommitted edits.*"
    }
  ],
  "category": "concise_desktop_advice",
  "human_reviewed": true
}
```

---

## 4. Methodology & Provenance
- **Curation**: 100% of seed examples were handcrafted and reviewed for tone, factual correctness, formatting consistency, and adherence to safety guidelines.
- **Deduplication**: SHA-256 hash matching on normalized user prompts prevents duplicate queries.
- **Split Strategy**: Deterministic 80% Train, 10% Validation, 10% Held-out Test split using fixed random seed (`seed=42`).
- **Privacy & Safety**: Zero scraped personal data, zero private conversations, and zero confidential telemetry.
