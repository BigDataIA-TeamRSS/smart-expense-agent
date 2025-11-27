# Smart Expense Analyzer & Budget Optimization Agent

Cloud-native **multi-agent financial assistant** that ingests bank and card transactions, detects hidden financial leaks (unused subscriptions, unusual patterns), and generates **actionable savings recommendations** — built with **FastAPI, Google Gemini, Google ADK, PostgreSQL, Streamlit, and GCP**.

> Built as an end-to-end data & AI system: ingestion → big-data pipelines → multi-agent LLM reasoning → dashboards → cloud deployment.  

---

## 🚀 What this project showcases

**For recruiters / reviewers, this repo demonstrates:**

- **Data Engineering & ETL**
  - Ingest transactions from Plaid API / CSV exports
  - Clean & normalize messy merchant strings, deduplicate, enrich metadata
  - Store in **PostgreSQL / Timescale** with time-series and aggregates

- **LLM + Multi-Agent Orchestration**
  - 3 Google ADK agents:
    - `Agent 1 – Data Processor`: classification, merchant normalization, subscription detection
    - `Agent 2 – Financial Analyst`: trend analysis, waste detection, budget optimization
    - `Agent 3 – Supervisor`: intent routing, caching, response formatting
  - Uses **Gemini 1.5 Flash & Pro** with structured JSON outputs, confidence scores, and guardrails

- **Cloud-Native Architecture (GCP)**
  - **FastAPI** backend in Docker, deployable to **Cloud Run**
  - **PostgreSQL (Cloud SQL)** as primary store, **Cloud Storage** for reports
  - **Cloud Scheduler** triggers batch jobs for nightly analysis

- **Analytics & UX**
  - **Streamlit** dashboard for:
    - Spending overview & trends
    - Subscription insights
    - Chat-style assistant: *“Where can I save money this month?”*

- **Reliability & Safety**
  - Schema validation via Pydantic
  - Financial guardrails (limits on recommendations, large txn alerts)
  - Evaluation plan for accuracy, latency, and token cost

---

## 🧠 High-level architecture

```mermaid
flowchart LR
  subgraph Ingestion
    A[Plaid API / CSV Upload] --> B[FastAPI Ingestion API]
  end

  B --> C[(PostgreSQL / TimescaleDB)]

  subgraph Agents["Agents – Google ADK + Gemini"]
    C --> D[Agent 1: Data Processor]
    D --> C
    C --> E[Agent 2: Financial Analyst]
    E --> F[Agent 3: Supervisor]
  end

  F --> C
  F --> G[Streamlit Frontend]
  G --> F
