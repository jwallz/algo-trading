# Algo Trading Learning Project

A 10-week project to learn algorithmic trading using NautilusTrader, starting with crypto data and building toward paper trading via Interactive Brokers.

**Goal:** Learn how algo trading and market microstructure work — not to make money in the short term. Simulation first, always.

---

## Stack

| Layer | Tool |
|---|---|
| Trading Engine | NautilusTrader |
| Market Data (start) | Binance API (free) |
| Market Data (later) | Databento / Polygon.io |
| Storage | TimescaleDB |
| Research | JupyterLab |
| Broker (paper) | Interactive Brokers paper account |
| Monitoring | Grafana |
| Infrastructure | AWS EC2 + S3 |

---

## Project Structure

```
algo-trading/
├── CONTEXT.md          # Full project context for AI-assisted sessions
├── README.md           # This file
├── data/               # Raw and processed market data
├── strategies/         # Strategy implementations
├── backtests/          # Backtest configs and results
├── notebooks/          # JupyterLab research notebooks
├── infra/              # AWS / EC2 setup scripts
│   ├── ec2_setup.sh
│   └── docker-compose.yml
└── pipelines/          # Data ingestion scripts
```

---

## 10-Week Learning Arc

| Weeks | Focus |
|---|---|
| 1–2 | Market structure fundamentals + NautilusTrader setup + EMA Cross backtest |
| 3–4 | Binance data ingestion → TimescaleDB |
| 5–6 | Strategy iteration — backtesting pitfalls, overfitting, transaction costs |
| 7–8 | Paper trading via Interactive Brokers paper account |
| 9–10 | Reflect, document, decide whether to continue |

---

## Getting Started

See `CONTEXT.md` for full context on decisions made, tech stack rationale, and week-by-week goals.
