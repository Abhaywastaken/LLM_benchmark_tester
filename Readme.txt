# EvoAudit Bench

EvoAudit Bench is a lightweight benchmark for testing how well large language models can audit Solidity smart contracts and reason about EVM security risks.

The project sends vulnerable Solidity contracts to multiple LLMs, compares their responses against hidden ground-truth vulnerabilities, scores each model, and displays the results in a browser dashboard.

---

## Project Goal

Smart contracts often manage real financial value. A single vulnerability in a DeFi protocol, lending market, DEX, or reward pool can lead to major losses.

This project answers the question:

> Which LLMs are actually reliable at finding smart contract security and DeFi trading logic vulnerabilities?

EvoAudit Bench evaluates models on whether they can:

- Identify the correct vulnerability
- Explain how the issue can be exploited
- Suggest a realistic fix
- Avoid false positives
- Perform consistently across different smart contract categories

---

## Features

- Browser-based dashboard
- FastAPI backend
- React frontend
- OpenRouter model support
- Manual Solidity benchmark cases
- Dynamic Solidity case generation
- Hidden ground-truth vulnerability tracking
- Automatic scoring
- Raw model answer inspection
- Model leaderboard
- Score breakdown by test type
- CSV/report-friendly output files

---

## Models Tested

The benchmark is configured to use OpenRouter-hosted models:

- Meta: Llama 3.3 70B
- DeepSeek: V4 Flash
- Google: Gemma 4 31B
- NVIDIA: Nemotron 3 Super
- OpenAI: GPT-OSS-120B

Model IDs are configured in `backend/.env`.

---

## Benchmark Test Types

The project supports three benchmark categories:

| Test Type | Purpose | Example Issues |
|---|---|---|
| `security_audit` | Tests standard Solidity security reasoning | reentrancy, access control, liquidation errors |
| `defi_trading_logic` | Tests DeFi and trading-specific reasoning | oracle manipulation, slippage, funding-rate manipulation |
| `patch_quality` | Tests whether the model can identify root cause and propose fixes | reward accounting, state update errors |

---

## Manual Smart Contract Cases

The current benchmark uses five manually designed Solidity contracts.

These contracts are intentionally vulnerable and are used to evaluate model performance in a controlled and reproducible way.

| Contract | Vulnerability | Severity |
|---|---|---|
| `VulnerableAMMSpotPriceOracle` | AMM spot-price oracle manipulation | Critical |
| `VulnerableDEXSlippageBypass` | Missing slippage protection | High |
| `VulnerablePerpFunding` | Funding-rate manipulation | Critical |
| `VulnerableLiquidation` | Incorrect liquidation check | High |
| `VulnerableRewardTradingPool` | Reward accounting error | High |

---

## How It Works

```text
Solidity smart contract
        ↓
Prompt sent to LLM
        ↓
Model returns audit findings
        ↓
Scorer compares answer to ground truth
        ↓
Dashboard displays scores and raw answers

## Project Structure

evoaudit-bench/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── llm_clients.py
│   │   ├── prompts.py
│   │   ├── scorer.py
│   │   ├── benchmark.py
│   │   ├── generator.py
│   │   └── manual_loader.py
│   │
│   ├── data/
│   │   ├── manual_cases/
│   │   ├── generated/
│   │   ├── ground_truth/
│   │   └── results/
│   │
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   ├── create_manual_cases.py
│   ├── run_benchmark.py
│   └── run_benchmark_csv.py
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        └── style.css