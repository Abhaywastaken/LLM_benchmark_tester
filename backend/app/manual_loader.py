import json
from pathlib import Path
from typing import List

from app.config import DATA_DIR
from app.models import BenchmarkCase, Bug

MANUAL_CASES_DIR = DATA_DIR / "manual_cases"


def load_manual_cases() -> List[BenchmarkCase]:
    if not MANUAL_CASES_DIR.exists():
        return []

    cases: List[BenchmarkCase] = []

    for json_path in sorted(MANUAL_CASES_DIR.glob("*.json")):
        payload = json.loads(json_path.read_text(encoding="utf-8"))

        case_id = payload["case_id"]
        sol_path = MANUAL_CASES_DIR / f"{case_id}.sol"

        if not sol_path.exists():
            raise FileNotFoundError(f"Missing Solidity file for case {case_id}: {sol_path}")

        solidity_code = sol_path.read_text(encoding="utf-8")

        bugs = [Bug(**bug) for bug in payload["bugs"]]

        cases.append(
            BenchmarkCase(
                case_id=case_id,
                test_type=payload["test_type"],
                contract_name=payload["contract_name"],
                solidity_code=solidity_code,
                bugs=bugs,
            )
        )

    return cases