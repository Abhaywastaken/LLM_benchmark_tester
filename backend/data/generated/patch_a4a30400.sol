// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract RewardPool0400 {
    mapping(address => uint256) public shares;
    uint256 public totalShares;
    uint256 public rewardPool;

    function stake() external payable {
        shares[msg.sender] += msg.value;
        totalShares += msg.value;
    }

    function addRewards() external payable {
        rewardPool += msg.value;
    }

    function claimRewards() external {
        require(shares[msg.sender] > 0, "no shares");

        uint256 payout = rewardPool * shares[msg.sender] / totalShares;

        // BUG: rewardPool is not reduced and user can repeatedly claim.
        (bool ok, ) = msg.sender.call{value: payout}("");
        require(ok, "reward transfer failed");
    }
}
