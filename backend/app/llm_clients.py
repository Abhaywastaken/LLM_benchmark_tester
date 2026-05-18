from typing import Dict

from openai import OpenAI

from app.config import settings
from app.prompts import SYSTEM_PROMPT


def call_openrouter(model_name: str, prompt: str) -> str:
    if not settings.openrouter_api_key:
        return "ERROR: Missing OPENROUTER_API_KEY."

    try:
        client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
            max_tokens=1200,
            extra_headers={
                "HTTP-Referer": "http://localhost",
                "X-Title": "EvoAudit Bench",
            },
        )

        if not response:
            return f"ERROR: OpenRouter returned empty response for model {model_name}"

        if not getattr(response, "choices", None):
            return f"ERROR: OpenRouter returned no choices for model {model_name}: {response}"

        first_choice = response.choices[0]

        if not first_choice:
            return f"ERROR: OpenRouter returned empty first choice for model {model_name}: {response}"

        message = getattr(first_choice, "message", None)

        if not message:
            return f"ERROR: OpenRouter returned no message for model {model_name}: {response}"

        content = getattr(message, "content", None)

        if not content:
            return f"ERROR: OpenRouter returned empty content for model {model_name}: {response}"

        return content

    except Exception as e:
        return f"ERROR: OpenRouter call failed for model {model_name}: {str(e)}"


def get_model_registry() -> Dict[str, Dict[str, str]]:
    return {
        "Meta: Llama 3.3 70B": {
            "provider": "openrouter",
            "model": settings.openrouter_model_llama,
        },
        "DeepSeek: V4 Flash": {
            "provider": "openrouter",
            "model": settings.openrouter_model_deepseek,
        },
        "Google: Gemma 4 31B": {
            "provider": "openrouter",
            "model": settings.openrouter_model_gemma,
        },
        "NVIDIA: Nemotron 3 Super": {
            "provider": "openrouter",
            "model": settings.openrouter_model_nemotron,
        },
        "OpenAI: GPT-OSS-120B": {
            "provider": "openrouter",
            "model": settings.openrouter_model_gpt_oss,
        },
    }


def call_model(model_id: str, prompt: str) -> str:
    registry = get_model_registry()

    if model_id not in registry:
        raise ValueError(f"Unknown model_id: {model_id}")

    model_info = registry[model_id]
    provider = model_info["provider"]
    model_name = model_info["model"]

    if provider == "openrouter":
        return call_openrouter(model_name, prompt)

    raise ValueError(f"Unknown provider: {provider}")