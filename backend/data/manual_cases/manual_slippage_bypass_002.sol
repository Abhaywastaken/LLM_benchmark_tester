// SPDX-License-Identifier: MIT
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
