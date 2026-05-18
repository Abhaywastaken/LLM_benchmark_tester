import json
import uuid
from typing import Dict, List

from app.config import RESULTS_DIR, settings
from app.generator import generate_cases, save_cases
from app.llm_clients import call_model, get_model_registry
from app.manual_loader import load_manual_cases
from app.models import BenchmarkRun, ScoreBreakdown
from app.prompts import AUDIT_PROMPT_TEMPLATE
from app.scorer import score_answer


def run_benchmark() -> BenchmarkRun:
    run_id = f"run_{uuid.uuid4().hex[:8]}"

    manual_cases = load_manual_cases()

    if manual_cases:
        print(f"Using {len(manual_cases)} manual benchmark cases.")
        cases = manual_cases
    else:
        print("No manual cases found. Falling back to generated cases.")
        cases = generate_cases(settings.cases_per_test)
        save_cases(cases)

    scores: List[ScoreBreakdown] = []
    raw_answers: Dict[str, str] = {}

    registry = get_model_registry()

    for case in cases:
        prompt = AUDIT_PROMPT_TEMPLATE.format(solidity_code=case.solidity_code)

        for model_id in registry.keys():
            print(f"Running {model_id} on {case.case_id}...")

            answer = call_model(model_id, prompt)

            raw_key = f"{model_id}::{case.case_id}"
            raw_answers[raw_key] = answer

            score = score_answer(
                model_id=model_id,
                case=case,
                answer=answer,
            )

            scores.append(score)

    run = BenchmarkRun(
        run_id=run_id,
        cases=cases,
        scores=scores,
        raw_answers=raw_answers,
    )

    output_path = RESULTS_DIR / f"{run_id}.json"
    output_path.write_text(
        json.dumps(run.model_dump(), indent=2),
        encoding="utf-8",
    )

    latest_path = RESULTS_DIR / "latest.json"
    latest_path.write_text(
        json.dumps(run.model_dump(), indent=2),
        encoding="utf-8",
    )

    return run


def load_latest_results() -> dict:
    latest_path = RESULTS_DIR / "latest.json"

    if not latest_path.exists():
        return {
            "message": "No benchmark results yet. Click Run Benchmark first.",
            "run_id": None,
            "scores": [],
            "cases": [],
            "raw_answers": {},
        }

    return json.loads(latest_path.read_text(encoding="utf-8"))