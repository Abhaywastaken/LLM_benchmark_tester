import re
from typing import List

from app.models import BenchmarkCase, ScoreBreakdown


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


ALIASES = {
    "reentrancy": [
        "reentrancy",
        "reentrant",
        "external call before state update",
        "checks-effects-interactions",
        "call before updating",
        "call before balance",
    ],
    "missing_access_control": [
        "access control",
        "missing access control",
        "unauthorized",
        "onlyowner",
        "only owner",
        "owner check",
        "anyone can call",
        "permissionless",
    ],
    "oracle_manipulation": [
        "oracle manipulation",
        "manipulable oracle",
        "spot price",
        "twap",
        "flash loan",
        "price manipulation",
        "amm oracle",
        "manipulable price",
    ],
    "amm_pricing_error": [
        "amm",
        "constant product",
        "x*y=k",
        "x * y = k",
        "price impact",
        "slippage",
        "spot price",
        "incorrect pricing",
        "reserve",
    ],
    "reward_accounting_error": [
        "reward accounting",
        "accounting",
        "double claim",
        "claim repeatedly",
        "repeatedly claim",
        "rewardpool",
        "reward pool",
        "not reduced",
        "claimed",
        "reward index",
        "snapshot",
        "stake before claim",
    ],
    "missing_slippage_protection": [
        "slippage",
        "missing slippage",
        "minamountout",
        "minimum amount out",
        "sandwich",
        "front-running",
        "frontrunning",
        "mev",
        "price impact",
    ],
    "funding_rate_manipulation": [
        "funding rate",
        "funding manipulation",
        "mark price",
        "index price",
        "oracle manipulation",
        "access control",
        "arbitrary price",
        "manipulable",
    ],
    "incorrect_liquidation_check": [
        "liquidation",
        "liquidatable",
        "collateral ratio",
        "health factor",
        "price oracle",
        "decimals",
        "normalization",
        "raw amounts",
        "debt",
    ],
}


def bug_detected(answer_norm: str, bug_type: str, expected_keywords: List[str]) -> bool:
    terms = []

    terms.extend(ALIASES.get(bug_type, []))
    terms.extend(expected_keywords)
    terms.append(bug_type)
    terms.append(bug_type.replace("_", " "))

    for term in terms:
        if term.lower() in answer_norm:
            return True

    return False


def has_explanation(answer_norm: str) -> bool:
    explanation_terms = [
        "attacker",
        "exploit",
        "because",
        "allows",
        "can call",
        "can manipulate",
        "can reenter",
        "leads to",
        "results in",
        "front-run",
        "sandwich",
        "flash loan",
    ]

    return any(term in answer_norm for term in explanation_terms)


def has_fix(answer_norm: str) -> bool:
    fix_terms = [
        "fix",
        "mitigation",
        "recommend",
        "use",
        "update",
        "restrict",
        "onlyowner",
        "only owner",
        "reentrancyguard",
        "checks-effects-interactions",
        "twap",
        "chainlink",
        "minamountout",
        "minimum amount out",
        "normalize",
        "price oracle",
        "reward index",
        "snapshot",
        "access control",
    ]

    return any(term in answer_norm for term in fix_terms)


def count_false_positives(answer: str, case: BenchmarkCase) -> int:
    answer_norm = normalize(answer)

    known_types = {
        "reentrancy",
        "access control",
        "oracle manipulation",
        "constant product",
        "integer overflow",
        "overflow",
        "underflow",
        "front running",
        "front-running",
        "sandwich",
        "flash loan",
        "unchecked call",
        "tx.origin",
        "signature replay",
        "double claim",
        "slippage",
        "liquidation",
        "funding rate",
    }

    expected_terms = set()

    for bug in case.bugs:
        expected_terms.add(bug.type.replace("_", " "))
        for keyword in bug.expected_keywords:
            expected_terms.add(keyword.lower())
        for alias in ALIASES.get(bug.type, []):
            expected_terms.add(alias.lower())

    false_count = 0

    for vuln in known_types:
        if vuln in answer_norm:
            is_expected = any(vuln in term or term in vuln for term in expected_terms)

            if not is_expected:
                false_count += 1

    return false_count


def score_answer(model_id: str, case: BenchmarkCase, answer: str) -> ScoreBreakdown:
    answer_norm = normalize(answer)

    total_score = 0.0
    detected_bugs = 0
    notes: List[str] = []

    if answer_norm.startswith("error:"):
        return ScoreBreakdown(
            model_id=model_id,
            case_id=case.case_id,
            test_type=case.test_type,
            score=0.0,
            detected_bugs=0,
            total_bugs=len(case.bugs),
            false_positives=0,
            notes=[answer[:300]],
        )

    for bug in case.bugs:
        detected = bug_detected(answer_norm, bug.type, bug.expected_keywords)

        if detected:
            detected_bugs += 1
            total_score += 50
            notes.append(f"Detected {bug.type}: +50")

            if has_explanation(answer_norm):
                total_score += 25
                notes.append(f"Explained exploit path for {bug.type}: +25")

            if bug.severity.lower() in answer_norm:
                total_score += 10
                notes.append(f"Correct severity for {bug.type}: +10")

            if has_fix(answer_norm):
                total_score += 15
                notes.append(f"Suggested fix for {bug.type}: +15")
        else:
            notes.append(f"Missed {bug.type}: +0")

    false_positives = count_false_positives(answer, case)
    penalty = false_positives * 10
    total_score -= penalty

    if false_positives:
        notes.append(f"False-positive penalty: -{penalty}")

    total_score = max(0.0, min(100.0, total_score))

    return ScoreBreakdown(
        model_id=model_id,
        case_id=case.case_id,
        test_type=case.test_type,
        score=total_score,
        detected_bugs=detected_bugs,
        total_bugs=len(case.bugs),
        false_positives=false_positives,
        notes=notes,
    )