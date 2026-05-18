import json
import random
import uuid
from pathlib import Path
from typing import List

from app.config import GENERATED_DIR, GROUND_TRUTH_DIR
from app.models import BenchmarkCase, Bug


def _case_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def generate_reentrancy_vault() -> BenchmarkCase:
    case_id = _case_id("security")
    contract_name = f"Vault{case_id[-4:]}"

    code = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract {contract_name} {{
    mapping(address => uint256) public balances;

    function deposit() external payable {{
        balances[msg.sender] += msg.value;
    }}

    function withdraw(uint256 amount) external {{
        require(balances[msg.sender] >= amount, "insufficient balance");

        // BUG: external call before state update
        (bool ok, ) = msg.sender.call{{value: amount}}("");
        require(ok, "transfer failed");

        balances[msg.sender] -= amount;
    }}

    function totalBalance() external view returns (uint256) {{
        return address(this).balance;
    }}
}}
"""

    bugs = [
        Bug(
            id="BUG-REENTRANCY-001",
            type="reentrancy",
            severity="critical",
            line_hint="withdraw(): external call occurs before balance is reduced",
            expected_keywords=[
                "reentrancy",
                "external call before state update",
                "checks-effects-interactions",
                "call before balance update",
            ],
            exploit_summary=(
                "An attacker contract can reenter withdraw() during msg.sender.call "
                "before balances[msg.sender] is reduced."
            ),
            suggested_fix=(
                "Update balances before the external call and/or use a reentrancy guard."
            ),
        )
    ]

    return BenchmarkCase(
        case_id=case_id,
        test_type="security_audit",
        contract_name=contract_name,
        solidity_code=code,
        bugs=bugs,
    )


def generate_access_control_oracle() -> BenchmarkCase:
    case_id = _case_id("security")
    contract_name = f"OracleVault{case_id[-4:]}"

    code = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IPriceOracle {{
    function price() external view returns (uint256);
}}

contract {contract_name} {{
    address public owner;
    IPriceOracle public oracle;
    mapping(address => uint256) public collateral;

    constructor(address initialOracle) {{
        owner = msg.sender;
        oracle = IPriceOracle(initialOracle);
    }}

    function depositCollateral() external payable {{
        collateral[msg.sender] += msg.value;
    }}

    // BUG: missing onlyOwner access control
    function setOracle(address newOracle) external {{
        oracle = IPriceOracle(newOracle);
    }}

    function borrowingPower(address user) external view returns (uint256) {{
        return collateral[user] * oracle.price() / 1e18;
    }}
}}
"""

    bugs = [
        Bug(
            id="BUG-ACCESS-001",
            type="missing_access_control",
            severity="critical",
            line_hint="setOracle(): anyone can change the oracle",
            expected_keywords=[
                "access control",
                "onlyOwner",
                "unauthorized",
                "setOracle",
                "owner",
            ],
            exploit_summary=(
                "Any address can replace the price oracle and manipulate borrowing power."
            ),
            suggested_fix="Restrict setOracle() with onlyOwner or role-based access control.",
        )
    ]

    return BenchmarkCase(
        case_id=case_id,
        test_type="security_audit",
        contract_name=contract_name,
        solidity_code=code,
        bugs=bugs,
    )


def generate_amm_pricing_bug() -> BenchmarkCase:
    case_id = _case_id("defi_trading_logic")
    contract_name = f"SimpleAMM{case_id[-4:]}"

    fee_bps = random.choice([25, 30, 50])

    code = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract {contract_name} {{
    uint256 public reserveX;
    uint256 public reserveY;
    uint256 public constant FEE_BPS = {fee_bps};

    constructor(uint256 x, uint256 y) {{
        reserveX = x;
        reserveY = y;
    }}

    function getAmountOut(uint256 amountIn) public view returns (uint256) {{
        // BUG: pricing ignores price impact and constant product invariant.
        // It uses a naive spot price based on old reserves.
        uint256 amountAfterFee = amountIn * (10000 - FEE_BPS) / 10000;
        return amountAfterFee * reserveY / reserveX;
    }}

    function swapXForY(uint256 amountIn) external returns (uint256 amountOut) {{
        amountOut = getAmountOut(amountIn);

        reserveX += amountIn;
        reserveY -= amountOut;
    }}
}}
"""

    bugs = [
        Bug(
            id="BUG-AMM-001",
            type="amm_pricing_error",
            severity="high",
            line_hint="getAmountOut(): uses naive spot price instead of x*y=k formula",
            expected_keywords=[
                "constant product",
                "price impact",
                "AMM",
                "spot price",
                "reserve",
                "slippage",
            ],
            exploit_summary=(
                "Large swaps receive too much output because the formula ignores price impact."
            ),
            suggested_fix=(
                "Use constant-product pricing: amountOut = reserveY - "
                "(reserveX * reserveY)/(reserveX + amountInAfterFee)."
            ),
        )
    ]

    return BenchmarkCase(
        case_id=case_id,
        test_type="defi_trading_logic",
        contract_name=contract_name,
        solidity_code=code,
        bugs=bugs,
    )


def generate_oracle_manipulation_lending() -> BenchmarkCase:
    case_id = _case_id("defi_trading_logic")
    contract_name = f"LendingPool{case_id[-4:]}"

    code = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IAMM {{
    function spotPrice() external view returns (uint256);
}}

contract {contract_name} {{
    IAMM public amm;
    mapping(address => uint256) public collateral;

    constructor(address amm_) {{
        amm = IAMM(amm_);
    }}

    function depositCollateral() external payable {{
        collateral[msg.sender] += msg.value;
    }}

    function maxBorrow(address user) public view returns (uint256) {{
        // BUG: uses manipulable AMM spot price directly as oracle.
        uint256 price = amm.spotPrice();
        return collateral[user] * price * 70 / 100 / 1e18;
    }}

    function borrow(uint256 amount) external {{
        require(amount <= maxBorrow(msg.sender), "too much borrow");
        // simplified demo: token transfer omitted
    }}
}}
"""

    bugs = [
        Bug(
            id="BUG-ORACLE-001",
            type="oracle_manipulation",
            severity="critical",
            line_hint="maxBorrow(): uses AMM spotPrice() directly",
            expected_keywords=[
                "oracle manipulation",
                "spot price",
                "TWAP",
                "flash loan",
                "manipulable",
                "AMM oracle",
            ],
            exploit_summary=(
                "An attacker can manipulate AMM spot price, inflate collateral value, "
                "and borrow more than allowed."
            ),
            suggested_fix=(
                "Use a robust oracle such as TWAP, Chainlink-style feeds, or sanity checks."
            ),
        )
    ]

    return BenchmarkCase(
        case_id=case_id,
        test_type="defi_trading_logic",
        contract_name=contract_name,
        solidity_code=code,
        bugs=bugs,
    )


def generate_patch_test() -> BenchmarkCase:
    case_id = _case_id("patch")
    contract_name = f"RewardPool{case_id[-4:]}"

    code = f"""// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract {contract_name} {{
    mapping(address => uint256) public shares;
    uint256 public totalShares;
    uint256 public rewardPool;

    function stake() external payable {{
        shares[msg.sender] += msg.value;
        totalShares += msg.value;
    }}

    function addRewards() external payable {{
        rewardPool += msg.value;
    }}

    function claimRewards() external {{
        require(shares[msg.sender] > 0, "no shares");

        uint256 payout = rewardPool * shares[msg.sender] / totalShares;

        // BUG: rewardPool is not reduced and user can repeatedly claim.
        (bool ok, ) = msg.sender.call{{value: payout}}("");
        require(ok, "reward transfer failed");
    }}
}}
"""

    bugs = [
        Bug(
            id="BUG-ACCOUNTING-001",
            type="reward_accounting_error",
            severity="high",
            line_hint="claimRewards(): rewardPool/user claim state is not updated",
            expected_keywords=[
                "double claim",
                "accounting",
                "rewardPool",
                "claim",
                "state update",
                "repeatedly claim",
            ],
            exploit_summary=(
                "A user can repeatedly call claimRewards() because claimed rewards are not tracked "
                "and rewardPool is not reduced."
            ),
            suggested_fix=(
                "Track claimed rewards per user or reduce rewardPool and update accounting before transfer."
            ),
        )
    ]

    return BenchmarkCase(
        case_id=case_id,
        test_type="patch_quality",
        contract_name=contract_name,
        solidity_code=code,
        bugs=bugs,
    )


def generate_cases(cases_per_test: int = 3) -> List[BenchmarkCase]:
    generators_by_test = {
        "security_audit": [generate_reentrancy_vault, generate_access_control_oracle],
        "defi_trading_logic": [generate_amm_pricing_bug, generate_oracle_manipulation_lending],
        "patch_quality": [generate_patch_test],
    }

    cases: List[BenchmarkCase] = []

    for test_type, generators in generators_by_test.items():
        for _ in range(cases_per_test):
            generator = random.choice(generators)
            cases.append(generator())

    return cases


def save_cases(cases: List[BenchmarkCase]) -> None:
    for case in cases:
        solidity_path = GENERATED_DIR / f"{case.case_id}.sol"
        truth_path = GROUND_TRUTH_DIR / f"{case.case_id}.json"

        solidity_path.write_text(case.solidity_code, encoding="utf-8")

        truth_payload = {
            "case_id": case.case_id,
            "test_type": case.test_type,
            "contract_name": case.contract_name,
            "bugs": [bug.model_dump() for bug in case.bugs],
        }

        truth_path.write_text(json.dumps(truth_payload, indent=2), encoding="utf-8")