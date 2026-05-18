// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IPriceOracle {
    function price() external view returns (uint256);
}

contract OracleVault8484 {
    address public owner;
    IPriceOracle public oracle;
    mapping(address => uint256) public collateral;

    constructor(address initialOracle) {
        owner = msg.sender;
        oracle = IPriceOracle(initialOracle);
    }

    function depositCollateral() external payable {
        collateral[msg.sender] += msg.value;
    }

    // BUG: missing onlyOwner access control
    function setOracle(address newOracle) external {
        oracle = IPriceOracle(newOracle);
    }

    function borrowingPower(address user) external view returns (uint256) {
        return collateral[user] * oracle.price() / 1e18;
    }
}
