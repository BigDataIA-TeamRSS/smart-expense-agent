# Smart Expense Analyzer & Budget Optimization Agent

Cloud-native **multi-agent financial assistant** that ingests bank and card transactions, detects hidden financial leaks (unused subscriptions, unusual patterns), and generates **actionable savings recommendations** — built with **FastAPI, Google Gemini, Google ADK, PostgreSQL, Streamlit, and GCP**.

> Built as an end-to-end data & AI system: ingestion → big-data pipelines → multi-agent LLM reasoning → dashboards → cloud deployment.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Docker Setup](#-docker-setup)
- [Agent System](#-agent-system)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## ✨ Features

### Core Capabilities

- **Multi-Source Transaction Ingestion**

  - Plaid API integration for automatic bank transaction sync
  - PDF statement upload and parsing using Google Gemini
  - CSV/JSON transaction import
- **AI-Powered Transaction Processing**

  - Automatic transaction categorization
  - Merchant name standardization
  - Subscription detection and tracking
  - Fraud and anomaly detection
  - Bill cycle identification
- **Financial Analytics & Insights**

  - Spending pattern analysis
  - Budget recommendations
  - Savings opportunity identification
  - Daily/weekly/monthly summaries
  - Category-wise spending breakdowns
- **Multi-Agent Architecture**

  - Agent 1: Data Processor (categorization, enrichment)
  - Agent 2: Financial Analyst (recommendations, insights)
  - Query Agent: Natural language database queries
- **Modern Web Interface**

  - Streamlit-based dashboard
  - Real-time transaction views
  - Interactive analytics
  - Bank connection management

---

## 🧠 Architecture

```mermaid
flowchart TB
    subgraph Ingestion["📥 Data Ingestion"]
        A[Plaid API] --> B[FastAPI Backend]
        C[PDF Upload] --> D[Gemini Parser]
        D --> B
        E[CSV/JSON] --> B
    end

    B --> F[(Cloud SQL PostgreSQL)]
  
    subgraph Agents["🤖 Multi-Agent System"]
        F --> G[Agent 1: Data Processor]
        G --> F
        F --> H[Agent 2: Financial Analyst]
        H --> F
        F --> I[Query Agent]
        I --> F
        J[Root Orchestrator] --> G
        J --> H
        J --> I
    end

    subgraph Frontend["🖥️ User Interface"]
        K[Streamlit Dashboard] --> J
        K --> F
    end

    subgraph Infrastructure["☁️ Cloud Infrastructure"]
        L[Google Cloud SQL] --> F
        M[Toolbox Service] --> G
        M --> H
        M --> I
        N[Google ADK] --> J
    end
```

### Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **AI/ML**: Google Gemini 2.5 Flash, Google ADK (Agent Development Kit)
- **Database**: PostgreSQL (Cloud SQL)
- **Frontend**: Streamlit
- **Infrastructure**: Google Cloud Platform (GCP)
- **Integration**: Plaid API, MCP Toolbox
- **Containerization**: Docker, Docker Compose

---

## 📦 Prerequisites

- **Python**: 3.11 or higher
- **PostgreSQL**: 16+ (or Cloud SQL instance)
- **Google Cloud Account**: For Cloud SQL and service account
- **Plaid Account**: For bank integration (sandbox or production)
- **Docker & Docker Compose**: For containerized deployment
- **Google Gemini API Key**: For PDF parsing and AI agents

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/BigDataIA-TeamRSS/smart-expense-agent.git
cd smart-expense-agent
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Plaid Configuration
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox  # or 'production'

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Database Configuration
USE_POSTGRESQL=true
USE_CLOUD_SQL=true
CLOUD_SQL_CONNECTION_NAME=project:region:instance
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_NAME=smart_expense_db

# Optional: Local PostgreSQL
# DB_CONNECTION_STRING=postgresql://user:password@localhost:5432/dbname
```

### 5. Database Setup

If using Cloud SQL, ensure your instance is created and accessible. For local development:

```bash
# Create database
createdb smart_expense_db

# Run migrations (if using Alembic)
alembic upgrade head
```

---

## ⚙️ Configuration

### Cloud SQL Setup

1. **Create Cloud SQL Instance**:

   ```bash
   gcloud sql instances create smart-expense-db \
     --database-version=POSTGRES_16 \
     --tier=db-f1-micro \
     --region=us-central1
   ```
2. **Create Database**:

   ```bash
   gcloud sql databases create smart_expense_db \
     --instance=smart-expense-db
   ```
3. **Service Account**:

   - Create a service account in GCP
   - Grant Cloud SQL Client role
   - Download JSON key to `.secret/service-account.json`

### Plaid Setup

1. Sign up at [Plaid Dashboard](https://dashboard.plaid.com/)
2. Get your `client_id` and `secret`
3. For development, use `sandbox` environment
4. Add credentials to `.env` file

### Toolbox Configuration

The MCP Toolbox service requires a `tools.yaml` file. Update `mcp_toolbox/tools.yaml` with your Cloud SQL connection details:

```yaml
sources:
  expense-db:
    kind: cloud-sql-postgres
    project: your-gcp-project-id
    region: us-central1
    instance: smart-expense-db
    database: smart_expense_db
    user: postgres
    password: your_password
```

---

## 🐳 Docker Setup

### Running with Docker Compose

1. **Navigate to docker directory**:

   ```bash
   cd docker
   ```
2. **Start services**:

   ```bash
   docker compose up
   ```

This will start:

- **Toolbox Service**: MCP Toolbox server on port 5000
- Connects to Cloud SQL using service account credentials

### Docker Compose Configuration

The `docker/docker-compose.yaml` file includes:

- Toolbox service with Cloud SQL authentication
- Volume mounts for configuration files
- Network configuration

**Important**: Ensure `.secret/service-account.json` exists before starting.

---

## 💻 Usage

### Running the Streamlit Frontend

```bash
streamlit run ui/main.py
```

Access the dashboard at `http://localhost:8501`

### Running the FastAPI Backend

```bash
cd src/app
uvicorn main:app --reload
```

API will be available at `http://localhost:8000`

### Using the Agent System

#### Via Streamlit UI

1. Navigate to "AI Agents" page
2. Enter your user ID
3. Ask questions like:
   - "Process transactions for user [user_id]"
   - "Generate savings recommendations for user [user_id]"
   - "Show me daily summary for user [user_id]"

#### Via Python Script

```python
from agents.agent1_data_processor import process_user_transactions_agent1

# Process transactions
result = process_user_transactions_agent1("user-uuid-here")
print(result)
```

#### Via ADK Web Interface

```bash
cd mcp_toolbox
adk run mcp_toolbox
```

---

## 🤖 Agent System

### Agent 1: Data Processor

**Purpose**: Process and enrich raw transaction data

**Capabilities**:

- Fetch unprocessed transactions
- Categorize transactions using AI
- Standardize merchant names
- Detect subscriptions (recurring payments)
- Flag anomalies and potential fraud
- Save processed data to database

**Tools Used**:

- `fetch-unprocessed-transactions`
- `insert-processed-transaction`
- `upsert-subscription`
- `insert-spending-pattern`

### Agent 2: Financial Analyst

**Purpose**: Generate financial insights and recommendations

**Capabilities**:

- Analyze spending patterns
- Generate budget recommendations
- Identify savings opportunities
- Create daily/weekly summaries
- Compare spending across categories

**Tools Used**:

- `get-user-transactions`
- `get-category-history`
- `get-user-subscriptions`
- `insert-recommendation`

### Query Agent

**Purpose**: Answer analytical questions using natural language

**Capabilities**:

- "Which category do I spend the most on?"
- "What are my top merchants?"
- "Show me my subscriptions"
- "How much did I spend last month?"

**Tools Used**:

- All database query tools
- Natural language to SQL conversion

### Root Orchestrator

Routes user requests to appropriate agents based on intent detection.

---

## 📡 API Documentation

### FastAPI Endpoints

#### Exchange Plaid Token

```http
POST /api/plaid/exchange
Content-Type: application/json

{
  "public_token": "public-sandbox-xxx"
}
```

#### Fetch Transactions

```http
GET /api/plaid/transactions?access_token=xxx
```

### Database Tools (via Toolbox)

All tools are accessible through the MCP Toolbox service. See `mcp_toolbox/tools.yaml` for complete list.

**Key Tools**:

- `fetch-unprocessed-transactions`: Get transactions needing processing
- `insert-processed-transaction`: Save enriched transaction data
- `upsert-subscription`: Save/update subscription information
- `get-user-transactions`: Query transactions by date range
- `get-category-history`: Get spending history by category

---

## 🚢 Deployment

### Cloud Run Deployment

1. **Build and push Docker image**:

   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/smart-expense-agent
   ```
2. **Deploy to Cloud Run**:

   ```bash
   gcloud run deploy smart-expense-agent \
     --image gcr.io/PROJECT_ID/smart-expense-agent \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### Recording Link :
https://northeastern.zoom.us/rec/share/1CP_KYLbs3LGj3PuGKuMISmqay-sbAGC24F2PJEKhdxuS3hnuUIVNdD12r8ln0sk.bAyi8XPQVZzeFTDA?startTime=1765579160000
Passcode: $6r@mE3=

### Environment Variables in Cloud Run

Set all `.env` variables as Cloud Run environment variables:

- `PLAID_CLIENT_ID`
- `PLAID_SECRET`
- `GEMINI_API_KEY`
- `DB_USER`, `DB_PASSWORD`, etc.

### Toolbox Service Deployment

The toolbox service is deployed separately. Update `mcp_toolbox/agent.py` with the correct toolbox URL:

```python
client = ToolboxSyncClient("https://toolbox-service-xxx.us-central1.run.app/")
```

---

## 🔧 Troubleshooting

### Common Issues

1. **Toolbox connection failed**

   - Ensure toolbox service is running: `docker compose up` in `docker/` directory
   - Check `tools.yaml` configuration
   - Verify service account credentials
2. **Cloud SQL connection errors**

   - Verify service account has Cloud SQL Client role
   - Check connection name format: `project:region:instance`
   - Ensure Cloud SQL instance allows connections from your IP
3. **Plaid authentication errors**

   - Verify credentials in `.env`
   - Check Plaid environment (sandbox vs production)
   - Ensure public token is valid
4. **Agent not responding**

   - Check Gemini API key is set
   - Verify toolbox service is accessible
   - Review agent logs for errors

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to all functions
- Write tests for new features
- Update documentation for API changes

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- Google Gemini & ADK for AI capabilities
- Plaid for financial data integration
- Streamlit for rapid UI development
- PostgreSQL & Cloud SQL for robust data storage

---

## 📞 Support

For issues and questions:

- Open an issue on GitHub
- Check existing documentation
- Review agent logs for debugging

---

**Built with ❤️ by Team RSS**


