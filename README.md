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


  Evaluations and Project Journey Documented :
  https://docs.google.com/document/d/1KmrxmxGym_lHdfGtqH5DG3xLF2kJER-gWYvkwhIMetw/edit?usp=sharing

  Contributions :
# Team Contributions

| Member | Contribution | Percentage |
|--------|--------------|------------|
| Somil Shah | Data Collecting -  Plaid , PDF Parsing , database connection , MCP toolbox setup, Streamlit , Google ADK-  Agent2 | 33.3% |
| Riya Kapadnis | streamlit , Database Schema Design , Deploying Agents to cloud , Cloud Deployement | 33.3% |
| Siddhi Dhamale | Data Preparation , Streamlit UI, Google ADK- Agent , Data processing pipeline , Cloud Deployement, FastAPI , Orchestration | 33.3% |

## 📋 Attestation

WE ATTEST THAT WE HAVEN'T USED ANY OTHER STUDENTS' WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK.
