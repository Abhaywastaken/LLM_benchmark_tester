// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IAMM {
    function spotPrice() external view returns (uint256);
}

contract LendingPool1ac1 {
    IAMM public amm;
    mapping(address => uint256) public collateral;

    constructor(address amm_) {
        amm = IAMM(amm_);
    }

    function depositCollateral() external payable {
        collateral[msg.sender] += msg.value;
    }

    function maxBorrow(address user) public view returns (uint256) {
        // BUG: uses manipulable AMM spot price directly as oracle.
        uint256 price = amm.spotPrice();
        return collateral[user] * price * 70 / 100 / 1e18;
    }

    function borrow(uint256 amount) external {
        require(amount <= maxBorrow(msg.sender), "too much borrow");
        // simplified demo: token transfer omitted
    }
}
