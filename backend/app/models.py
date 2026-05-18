from pydantic import BaseModel
from typing import List, Dict, Optional


class Bug(BaseModel):
    id: str
    type: str
    severity: str
    line_hint: str
    expected_keywords: List[str]
    exploit_summary: str
    suggested_fix: str


class BenchmarkCase(BaseModel):
    case_id: str
    test_type: str
    contract_name: str
    solidity_code: str
    bugs: List[Bug]


class ModelFinding(BaseModel):
    bug_type: str
    severity: str
    description: str
    exploit_path: str
    fix: str


class ModelAnswer(BaseModel):
    model_id: str
    case_id: str
    raw_text: str
    findings: List[ModelFinding] = []


class ScoreBreakdown(BaseModel):
    model_id: str
    case_id: str
    test_type: str
    score: float
    detected_bugs: int
    total_bugs: int
    false_positives: int
    notes: List[str]


class BenchmarkRun(BaseModel):
    run_id: str
    cases: List[BenchmarkCase]
    scores: List[ScoreBreakdown]
    raw_answers: Dict[str, str]