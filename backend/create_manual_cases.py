import json
from pathlib import Path

MANUAL_CASES_DIR = Path("data/manual_cases")
MANUAL_CASES_DIR.mkdir(parents=True, exist_ok=True)


CASES = [
    {
        "case_id": "manual_oracle_manipulation_001",
        "contract_name": "VulnerableAMMSpotPriceOracle",
        "test_type": "defi_trading_logic",
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableAMMSpotPriceOracle {
    uint256 public reserveETH;
    uint256 public reserveUSDC;

    mapping(address => uint256) public collateralETH;
    mapping(address => uint256) public debtUSDC;

    constructor(uint256 initialETH, uint256 initialUSDC) {
        reserveETH = initialETH;
        reserveUSDC = initialUSDC;
    }

    function depositCollateral() external payable {
        collateralETH[msg.sender] += msg.value;
    }

    function spotPriceETH() public view returns (uint256) {
        require(reserveETH > 0, "empty reserve");
        return reserveUSDC * 1e18 / reserveETH;
    }

    function maxBorrow(address user) public view returns (uint256) {
        uint256 ethPrice = spotPriceETH();
        return collateralETH[user] * ethPrice * 70 / 100 / 1e18;
    }

    function borrowUSDC(uint256 amount) external {
        require(amount <= maxBorrow(msg.sender), "too much borrow");
        debtUSDC[msg.sender] += amount;
    }

    function swapETHForUSDC() external payable returns (uint256 amountOut) {
        require(msg.value > 0, "no ETH");

        uint256 ethIn = msg.value;
        amountOut = ethIn * reserveUSDC / reserveETH;

        reserveETH += ethIn;
        reserveUSDC -= amountOut;
    }
}
""",
        "bugs": [
            {
                "id": "BUG-ORACLE-001",
                "type": "oracle_manipulation",
                "severity": "critical",
                "line_hint": "spotPriceETH() and maxBorrow() use live AMM reserves as the oracle",
                "expected_keywords": [
                    "oracle manipulation",
                    "spot price",
                    "AMM oracle",
                    "flash loan",
                    "TWAP",
                    "manipulable price"
                ],
                "exploit_summary": "An attacker can manipulate AMM reserves temporarily, inflate collateral value, and borrow too much.",
                "suggested_fix": "Use TWAP, Chainlink-style oracle, time-weighted prices, or sanity checks."
            }
        ],
    },
    {
        "case_id": "manual_slippage_bypass_002",
        "contract_name": "VulnerableDEXSlippageBypass",
        "test_type": "defi_trading_logic",
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableDEXSlippageBypass {
    mapping(address => uint256) public tokenXBalance;
    mapping(address => uint256) public tokenYBalance;

    uint256 public reserveX = 1_000_000 ether;
    uint256 public reserveY = 1_000_000 ether;

    function depositTokenX(uint256 amount) external {
        tokenXBalance[msg.sender] += amount;
    }

    function getAmountOut(uint256 amountIn) public view returns (uint256) {
        uint256 amountInWithFee = amountIn * 997 / 1000;
        return reserveY * amountInWithFee / (reserveX + amountInWithFee);
    }

    function swapXForY(uint256 amountIn) external returns (uint256 amountOut) {
        require(tokenXBalance[msg.sender] >= amountIn, "insufficient X");

        amountOut = getAmountOut(amountIn);

        tokenXBalance[msg.sender] -= amountIn;
        tokenYBalance[msg.sender] += amountOut;

        reserveX += amountIn;
        reserveY -= amountOut;
    }
}
""",
        "bugs": [
            {
                "id": "BUG-SLIPPAGE-001",
                "type": "missing_slippage_protection",
                "severity": "high",
                "line_hint": "swapXForY() has no minAmountOut parameter",
                "expected_keywords": [
                    "slippage",
                    "minAmountOut",
                    "sandwich",
                    "front-running",
                    "MEV",
                    "price impact"
                ],
                "exploit_summary": "Users cannot enforce a minimum output amount, making them vulnerable to sandwich/front-running losses.",
                "suggested_fix": "Add a minAmountOut parameter and revert if amountOut is below that value."
            }
        ],
    },
    {
        "case_id": "manual_funding_rate_manipulation_003",
        "contract_name": "VulnerablePerpFunding",
        "test_type": "defi_trading_logic",
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerablePerpFunding {
    mapping(address => int256) public positionSize;
    mapping(address => int256) public fundingDebt;

    int256 public fundingRate;
    int256 public lastMarkPrice;
    int256 public lastIndexPrice;

    function openPosition(int256 size) external {
        positionSize[msg.sender] += size;
        fundingDebt[msg.sender] += size * fundingRate;
    }

    function updateFundingRate(int256 markPrice, int256 indexPrice) external {
        lastMarkPrice = markPrice;
        lastIndexPrice = indexPrice;

        fundingRate = (markPrice - indexPrice) / 100;
    }

    function settleFunding(address trader) external {
        int256 payment = positionSize[trader] * fundingRate;
        fundingDebt[trader] += payment;
    }
}
""",
        "bugs": [
            {
                "id": "BUG-FUNDING-001",
                "type": "funding_rate_manipulation",
                "severity": "critical",
                "line_hint": "updateFundingRate() is external and accepts arbitrary prices",
                "expected_keywords": [
                    "funding rate",
                    "oracle manipulation",
                    "access control",
                    "mark price",
                    "index price",
                    "manipulable"
                ],
                "exploit_summary": "Anyone can update the funding rate with arbitrary mark and index prices.",
                "suggested_fix": "Restrict updates to trusted keepers and use robust oracle/TWAP price feeds."
            }
        ],
    },
    {
        "case_id": "manual_bad_liquidation_004",
        "contract_name": "VulnerableLiquidation",
        "test_type": "security_audit",
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableLiquidation {
    mapping(address => uint256) public collateralAmount;
    mapping(address => uint256) public debtAmount;

    uint256 public constant LIQUIDATION_THRESHOLD = 80;

    function depositCollateral(uint256 amount) external {
        collateralAmount[msg.sender] += amount;
    }

    function borrow(uint256 amount) external {
        debtAmount[msg.sender] += amount;
    }

    function isLiquidatable(address user) public view returns (bool) {
        if (collateralAmount[user] == 0) {
            return true;
        }

        uint256 ratio = debtAmount[user] * 100 / collateralAmount[user];

        return ratio > LIQUIDATION_THRESHOLD;
    }

    function liquidate(address user) external {
        require(isLiquidatable(user), "not liquidatable");

        collateralAmount[user] = 0;
        debtAmount[user] = 0;
    }
}
""",
        "bugs": [
            {
                "id": "BUG-LIQUIDATION-001",
                "type": "incorrect_liquidation_check",
                "severity": "high",
                "line_hint": "isLiquidatable() compares raw collateral and debt amounts without pricing",
                "expected_keywords": [
                    "liquidation",
                    "collateral ratio",
                    "price oracle",
                    "decimals",
                    "normalization",
                    "debt"
                ],
                "exploit_summary": "The liquidation check compares raw amounts without oracle prices or decimal normalization.",
                "suggested_fix": "Use oracle prices, normalize token decimals, and compare collateral value against debt value."
            }
        ],
    },
    {
        "case_id": "manual_reward_accounting_005",
        "contract_name": "VulnerableRewardTradingPool",
        "test_type": "patch_quality",
        "solidity_code": """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableRewardTradingPool {
    mapping(address => uint256) public stakeBalance;
    mapping(address => uint256) public rewardsClaimed;

    uint256 public totalStake;
    uint256 public rewardPool;

    function stake() external payable {
        require(msg.value > 0, "no stake");

        stakeBalance[msg.sender] += msg.value;
        totalStake += msg.value;
    }

    function addTradingRewards() external payable {
        rewardPool += msg.value;
    }

    function claimRewards() external {
        require(totalStake > 0, "no stake");
        require(stakeBalance[msg.sender] > 0, "not staker");

        uint256 reward = rewardPool * stakeBalance[msg.sender] / totalStake;

        rewardsClaimed[msg.sender] += reward;

        (bool ok, ) = msg.sender.call{value: reward}("");
        require(ok, "transfer failed");
    }

    function withdrawStake(uint256 amount) external {
        require(stakeBalance[msg.sender] >= amount, "too much");

        stakeBalance[msg.sender] -= amount;
        totalStake -= amount;

        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");
    }
}
""",
        "bugs": [
            {
                "id": "BUG-REWARD-001",
                "type": "reward_accounting_error",
                "severity": "high",
                "line_hint": "claimRewards() calculates rewards from current stake without snapshots or reward index",
                "expected_keywords": [
                    "reward accounting",
                    "flash loan",
                    "stake before claim",
                    "reward snapshot",
                    "reward index",
                    "double claim"
                ],
                "exploit_summary": "A user can stake immediately before claiming rewards and withdraw after, extracting unfair rewards.",
                "suggested_fix": "Use accumulated reward-per-share accounting, staking duration rules, or snapshot balances before reward distribution."
            }
        ],
    },
]


def main():
    for case in CASES:
        case_id = case["case_id"]

        sol_path = MANUAL_CASES_DIR / f"{case_id}.sol"
        json_path = MANUAL_CASES_DIR / f"{case_id}.json"

        sol_path.write_text(case["solidity_code"], encoding="utf-8")

        json_payload = {
            "case_id": case["case_id"],
            "test_type": case["test_type"],
            "contract_name": case["contract_name"],
            "bugs": case["bugs"],
        }

        json_path.write_text(json.dumps(json_payload, indent=2), encoding="utf-8")

    print(f"Created {len(CASES)} manual cases in {MANUAL_CASES_DIR}")


if __name__ == "__main__":
    main()