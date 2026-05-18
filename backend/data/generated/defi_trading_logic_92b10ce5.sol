// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract SimpleAMM0ce5 {
    uint256 public reserveX;
    uint256 public reserveY;
    uint256 public constant FEE_BPS = 50;

    constructor(uint256 x, uint256 y) {
        reserveX = x;
        reserveY = y;
    }

    function getAmountOut(uint256 amountIn) public view returns (uint256) {
        // BUG: pricing ignores price impact and constant product invariant.
        // It uses a naive spot price based on old reserves.
        uint256 amountAfterFee = amountIn * (10000 - FEE_BPS) / 10000;
        return amountAfterFee * reserveY / reserveX;
    }

    function swapXForY(uint256 amountIn) external returns (uint256 amountOut) {
        amountOut = getAmountOut(amountIn);

        reserveX += amountIn;
        reserveY -= amountOut;
    }
}
