# Algo Trading Learning Project — Context Document

> This file provides full context for any Claude session (Claude Code, Claude Project, or otherwise) 
> working on this project. Reference it at the start of each session.

---

## About the Developer

- **Name:** John
- **Background:** Software engineer with strong Python skills and extensive experience in systems integrations, data pipelines, and automation
- **Relevant experience:**
  - ETL/data pipeline design (Snowflake, Tray.io, REST APIs)
  - SuiteScript (NetSuite) development
  - Salesforce integrations
  - AWS (personal account available)
  - JavaScript (functional, not primary language)
- **Trading experience:** Beginner — strong interest in economics and finance, but new to algorithmic trading
- **Current situation:** Recently laid off, 10 weeks of severance. Using this window to explore algo trading as a learning project. **Severance is not risk capital** — no live trading with real money until confidence is established through simulation.

---

## Project Goals

1. **Learn** how algorithmic trading and market microstructure work
2. **Build** a functioning backtest and paper trading environment
3. **Develop and evaluate** at least one simple trading strategy end-to-end
4. **Decide** at week 10 whether to continue deeper into this space
5. **NOT** to make money in the short term — simulation and learning first, always

---

## Agreed Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Trading Engine | NautilusTrader | Core platform — open source, Rust core, Python API |
| Market Data (start) | Binance API (free) | Free crypto historical data for early weeks |
| Market Data (later) | Databento or Polygon.io | Low-cost paid tiers; Databento has native Nautilus integration |
| Data Storage | TimescaleDB | Open-source Postgres time-series extension — replaces Snowflake |
| Orchestration | Python scripts + cron (start), Airflow or n8n (later) | Replaces Tray.io |
| Research Environment | JupyterLab | Local or EC2-hosted |
| Broker (paper trading) | Interactive Brokers (paper account) | Free paper trading; NautilusTrader has native IB adapter |
| Monitoring | Grafana | Dashboards for backtest results and live sim metrics |
| Infrastructure | AWS (personal account) | EC2 + S3; target ~$50-80/month |
| Version Control | GitHub | All code tracked here |

---

## Infrastructure Plan

### AWS Targets
- **t3.medium EC2** (~$30/mo) — runs TimescaleDB, JupyterLab, and Airflow (consolidated to start)
- **S3** — cheap storage for raw historical data files
- Scale up compute temporarily for intensive backtests, then back down

### Asset Class Approach
- **Start with crypto** — free data (Binance API), open APIs, no data costs, good for learning mechanics
- **Move to equities/futures** once fundamentals are solid and data budget is defined

---

## 10-Week Learning Arc

| Weeks | Focus |
|---|---|
| 1–2 | Market structure fundamentals + NautilusTrader setup + first backtest (EMA Cross example) |
| 3–4 | Data acquisition — pull Binance historical data, load into TimescaleDB and Nautilus format |
| 5–6 | Strategy iteration — understand backtesting pitfalls (overfitting, look-ahead bias, transaction costs) |
| 7–8 | Paper trading / live simulation via Interactive Brokers paper account |
| 9–10 | Reflect, document, evaluate — decide whether to continue and how |

---

## Week 1 Immediate Goals

1. Install NautilusTrader locally (Python virtual environment)
2. Stand up EC2 instance with TimescaleDB + JupyterLab
3. Pull free Binance historical crypto data and load into Nautilus format
4. Run the built-in EMA Cross backtest successfully end-to-end

---

## Key Decisions Already Made

- ✅ No real money trading until simulation period establishes confidence
- ✅ Start with crypto for zero data cost
- ✅ Open source stack only (lost access to Snowflake and Tray.io at previous employer)
- ✅ AWS for infrastructure (personal account exists)
- ✅ NautilusTrader as the core engine
- ✅ TimescaleDB as the time-series data store
- ✅ Interactive Brokers for paper trading when ready

---

## How to Use This File

**In Claude Code:**
```
claude "Read CONTEXT.md first, then let's work on [specific task]"
```

**In a new Claude chat / Claude Project:**
> "Here is my project context document — please read it before we continue."
> *(paste or attach this file)*

---

## Project Repository Structure (Target)

```
algo-trading/
├── CONTEXT.md          # This file
├── README.md           # Project overview
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

*Last updated: Based on initial planning conversation in claude.ai, May 2026*
