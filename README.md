Smart Expense Analyzer & Budget Optimization Agent

A cloud-ready multi-agent financial assistant that ingests bank/card transactions, detects hidden financial leaks (unused subscriptions, unusual patterns), and generates actionable savings recommendations — built with FastAPI, Google Gemini, Google ADK, PostgreSQL, Streamlit, and GCP.

End-to-end pipeline: Ingestion → Storage → Agent processing → Insights → UI → Cloud deployment

🧠 High-level architecture
flowchart LR
  %% =========================
  %% Ingestion
  %% =========================
  subgraph Ingestion
    A[Plaid API / CSV Upload / PDF Upload] --> B[FastAPI Ingestion API]
  end

  %% =========================
  %% Storage
  %% =========================
  B --> C[(PostgreSQL)]

  %% =========================
  %% Agents
  %% =========================
  subgraph Agents["Agents (Google ADK + Gemini)"]
    C --> D[Agent 1: Data Processor / Categorizer]
    D --> C
    C --> E[Agent 2: Fraud / Anomaly Detector]
    E --> C
    C --> F[Agent 3: Supervisor / Orchestrator]
  end

  %% =========================
  %% UI
  %% =========================
  F --> G[Streamlit Frontend]
  G --> F

✅ Key features

Transaction ingestion via Plaid + PDF statement upload fallback

Categorization + merchant standardization

Fraud / anomaly signals with explanation

Subscription detection (recurring merchants + next expected charge)

Stores results in PostgreSQL (users, accounts, transactions, processed_transactions, subscriptions)

Supervisor/Orchestrator runs agents sequentially and conditionally (hybrid approach to reduce LLM cost/time)

📦 Tech stack

Backend: FastAPI

Agents: Google ADK + Gemini

Database: PostgreSQL

UI: Streamlit

Cloud: Google Cloud Platform (Cloud Run / Cloud SQL / Artifact Registry as applicable)

📄 Project Journey & Evaluation

Project journey document and evaluation metrics are documented here:

https://docs.google.com/document/d/1KmrxmxGym_lHdfGtqH5DG3xLF2kJER-gWYvkwhIMetw/edit?usp=sharing

👥 Team Contributions
Member	Contribution	Percentage
Somil Shah	Plaid integration, PDF parsing, DB connection, MCP toolbox setup, Streamlit, ADK Agent 2 work	33.3%
Riya Kapadnis	Streamlit support, DB schema design, deploying agents to cloud, cloud deployment	33.3%
Siddhi Dhamale	Data preparation, Streamlit UI, ADK agent + orchestration, processing pipeline, FastAPI, cloud deployment	33.3%
📋 Attestation

We attest that we haven’t used any other students’ work in this assignment and abide by the policies listed in the student handbook.
