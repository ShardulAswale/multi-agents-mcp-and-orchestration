"""Bonus Unit 1: validated, explicitly opt-in LoRA function-calling pipeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_fixture_weather",
        "description": "Return training weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}


def runtime_precision(torch_module):
    """Return CUDA/BF16/FP16 flags without selecting emulated BF16 on Turing."""
    cuda = torch_module.cuda.is_available()
    capability = torch_module.cuda.get_device_capability(0) if cuda else (0, 0)
    bf16 = bool(cuda and capability[0] >= 8 and torch_module.cuda.is_bf16_supported())
    return cuda, bf16, bool(cuda and not bf16)


def function_call_record(user: str, arguments: dict, observation: str, answer: str) -> dict:
    """Create one OpenAI-style Thought/Act/Observe training conversation."""
    if not all(isinstance(value, str) and value.strip() for value in (user, observation, answer)):
        raise ValueError("user, observation, and answer must be non-empty strings")
    if not isinstance(arguments, dict) or set(arguments) != {"city"}:
        raise ValueError("arguments must contain only city")
    city = arguments["city"]
    if not isinstance(city, str) or not city.strip():
        raise ValueError("city must be a non-empty string")
    call_id = "fixture-weather-1"
    return {
        "messages": [
            {"role": "system", "content": "Use tools for weather facts."},
            {"role": "user", "content": user.strip()},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": call_id,
                    "type": "function",
                    "function": {
                        "name": "get_fixture_weather",
                        "arguments": json.dumps({"city": city.strip()}, sort_keys=True),
                    },
                }],
            },
            {"role": "tool", "tool_call_id": call_id, "content": observation.strip()},
            {"role": "assistant", "content": answer.strip()},
        ],
        "tools": [TOOL_SCHEMA],
    }


TRAINING_RECORDS = (
    function_call_record(
        "What is the London training weather?", {"city": "London"},
        "London fixture: cloudy, 14 C.", "The London fixture is cloudy at 14 C.",
    ),
    function_call_record(
        "What is the Paris training weather?", {"city": "Paris"},
        "Paris fixture: clear, 17 C.", "The Paris fixture is clear at 17 C.",
    ),
)


def validate_records(records) -> list[dict]:
    """Reject malformed conversations before any model download or training."""
    records = list(records)
    if not records:
        raise ValueError("at least one training record is required")
    for record in records:
        messages = record.get("messages") if isinstance(record, dict) else None
        roles = [message.get("role") for message in messages or []]
        if roles != ["system", "user", "assistant", "tool", "assistant"]:
            raise ValueError("each record must follow system/user/assistant/tool/assistant")
        calls = messages[2].get("tool_calls", [])
        if len(calls) != 1 or calls[0].get("id") != messages[3].get("tool_call_id"):
            raise ValueError("tool call and observation IDs must match")
        json.loads(calls[0]["function"]["arguments"])
    return records


def build_lora_config():
    """Build the small adapter configuration; importing this does not train."""
    from peft import LoraConfig
    return LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.05, bias="none",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        task_type="CAUSAL_LM",
    )


def build_sft_config(output_dir: str):
    """Select CPU, FP16, or BF16 from the installed PyTorch capabilities."""
    import torch
    from trl import SFTConfig

    cuda, bf16, fp16 = runtime_precision(torch)
    return SFTConfig(
        output_dir=output_dir, dataset_text_field="text", max_steps=20,
        per_device_train_batch_size=1, gradient_accumulation_steps=4,
        learning_rate=2e-4, logging_steps=1, save_strategy="no",
        report_to="none", use_cpu=not cuda, bf16=bf16,
        fp16=fp16, optim="adamw_torch",
        dataloader_pin_memory=cuda, gradient_checkpointing=False,
        activation_checkpointing=False,
    )


def train(records, output_dir: str, model_id: str = DEFAULT_MODEL_ID):
    """Run the explicit local training job after the caller confirms it."""
    from datasets import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    from trl import SFTTrainer

    records = validate_records(records)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    rendered = [
        {"text": tokenizer.apply_chat_template(
            record["messages"], tools=record["tools"], tokenize=False
        )}
        for record in records
    ]
    cuda, bf16, _ = runtime_precision(torch)
    dtype = torch.bfloat16 if bf16 else torch.float16 if cuda else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        model_id, device_map="auto", dtype=dtype
    )
    config = build_sft_config(output_dir)
    trainer = SFTTrainer(
        model=model, args=config, train_dataset=Dataset.from_list(rendered),
        processing_class=tokenizer, peft_config=build_lora_config(),
    )
    trainer.train()
    trainer.save_model(output_dir)
    return Path(output_dir)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL_ID)
    parser.add_argument("--output", default=".course-private/function-calling-lora")
    parser.add_argument("--confirm-train", action="store_true",
                        help="permit model download and local GPU/CPU training")
    args = parser.parse_args(argv)
    records = validate_records(TRAINING_RECORDS)
    if not args.confirm_train:
        print(f"Validated {len(records)} records; training was not started.")
        return 0
    import torch
    runtime = "CUDA" if torch.cuda.is_available() else "CPU"
    print(f"Training runtime: {runtime}")
    destination = train(records, args.output, args.model)
    print(f"Saved adapter to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
