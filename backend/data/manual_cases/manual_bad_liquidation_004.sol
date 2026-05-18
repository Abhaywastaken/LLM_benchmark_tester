// SPDX-License-Identifier: MIT
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
