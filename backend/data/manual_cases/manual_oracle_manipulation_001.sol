// SPDX-License-Identifier: MIT
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
