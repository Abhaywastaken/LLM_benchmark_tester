import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

GENERATED_DIR = DATA_DIR / "generated"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
RESULTS_DIR = DATA_DIR / "results"

for directory in [GENERATED_DIR, GROUND_TRUTH_DIR, RESULTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")


class Settings:
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")

    openrouter_model_llama: str = os.getenv(
        "OPENROUTER_MODEL_LLAMA",
        "meta-llama/llama-3.3-70b-instruct:free",
    )

    openrouter_model_deepseek: str = os.getenv(
        "OPENROUTER_MODEL_DEEPSEEK",
        "deepseek/deepseek-v4-flash:free",
    )

    openrouter_model_gemma: str = os.getenv(
        "OPENROUTER_MODEL_GEMMA",
        "google/gemma-4-31b-it:free",
    )

    openrouter_model_nemotron: str = os.getenv(
        "OPENROUTER_MODEL_NEMOTRON",
        "nvidia/nemotron-3-super-120b-a12b:free",
    )

    openrouter_model_gpt_oss: str = os.getenv(
        "OPENROUTER_MODEL_GPT_OSS",
        "openai/gpt-oss-120b:free",
    )

    cases_per_test: int = int(os.getenv("BENCHMARK_CASES_PER_TEST", "2"))


settings = Settings()