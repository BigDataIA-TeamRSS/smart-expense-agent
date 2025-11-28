# Smart Expense Analyzer & Budget Optimization Agent

Cloud-native **multi-agent financial assistant** that ingests bank and card transactions, detects hidden financial leaks (unused subscriptions, unusual patterns), and generates **actionable savings recommendations** — built with **FastAPI, Google Gemini, Google ADK, PostgreSQL, Streamlit, and GCP**.

> Built as an end-to-end data & AI system: ingestion → big-data pipelines → multi-agent LLM reasoning → dashboards → cloud deployment.  


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
