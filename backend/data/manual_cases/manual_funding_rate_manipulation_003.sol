// SPDX-License-Identifier: MIT
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
