// SPDX-License-Identifier: MIT
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
