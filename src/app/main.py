# Smart Expense Analyzer - FastAPI Backend
# Run: uvicorn src.app.main:app --reload --port 8000

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# PYDANTIC MODELS - Request/Response schemas
# =============================================================================

# --- Request Models ---

class PlaidExchangeRequest(BaseModel):
    """Request to exchange Plaid public token"""
    public_token: str = Field(..., description="Plaid public token from Link")


class ProcessTransactionsRequest(BaseModel):
    """Request to process transactions for a user"""
    user_id: str = Field(..., description="User's unique identifier")
    limit: int = Field(default=50, ge=1, le=500, description="Max transactions to process")


class ChatRequest(BaseModel):
    """Request to chat with AI agent"""
    user_id: str = Field(..., description="User's unique identifier")
    message: str = Field(..., min_length=1, max_length=1000, description="User's message/question")


# --- Response Models ---

class StatusResponse(BaseModel):
    """Standard status response"""
    status: str = Field(..., description="'success' or 'error'")
    message: str = Field(default="", description="Status message")


class AgentStatusResponse(BaseModel):
    """Response for agent status endpoint"""
    supervisor: str = Field(default="unknown")
    agent1_available: bool = Field(default=False, description="Data Processor availability")
    agent2_available: bool = Field(default=False, description="Financial Analyst availability")
    query_agent_available: bool = Field(default=False, description="Query Agent availability")
    timestamp: str = Field(default="", description="Status check timestamp")


class RecommendationItem(BaseModel):
    """Single recommendation"""
    type: str
    title: str
    description: str
    potential_savings: float = 0
    annual_savings: float = 0
    priority: int = 3
    urgency: str = "medium"
    category: Optional[str] = None


class RecommendationsResponse(BaseModel):
    """Response for recommendations endpoint"""
    status: str
    user_id: str
    total_recommendations: int = 0
    potential_monthly_savings: float = 0
    potential_annual_savings: float = 0
    recommendations: List[Dict[str, Any]] = []
    agent: str = "financial_analyst"


class DailySummaryResponse(BaseModel):
    """Response for daily summary endpoint"""
    status: str
    user_id: str
    summary_date: str
    total_spent: float = 0
    transaction_count: int = 0
    top_category: str = "None"
    spending_by_category: Dict[str, float] = {}
    budget_alerts: List[str] = []
    summary_text: str = ""


class ChatResponse(BaseModel):
    """Response for chat endpoint"""
    status: str
    user_id: str
    message: Optional[str] = None
    answer: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    agent: str = "supervisor"


class ProcessingResponse(BaseModel):
    """Response for transaction processing"""
    status: str
    message: str
    processed_count: int = 0
    agent: str = "data_processor"


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str = "1.0.0"
    timestamp: str
    services: Dict[str, str] = {}


# =============================================================================
# FASTAPI APP INITIALIZATION
# =============================================================================

app = FastAPI(
    title="Smart Expense Analyzer API",
    description="""
    AI-powered financial assistant API that provides:
    - Transaction processing and categorization (Agent 1)
    - Financial recommendations and summaries (Agent 2)
    - Natural language financial queries (Agent 3 - Supervisor)
    
    Built with Google ADK, Gemini LLM, and MCP Tools.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# =============================================================================
# CORS MIDDLEWARE
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server
        "http://localhost:8501",      # Streamlit
        "http://localhost:8080",      # Docker Streamlit
        "http://127.0.0.1:8501",
        "*"                           # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HELPER: GET SUPERVISOR
# =============================================================================

def get_supervisor():
    """Lazy load the Supervisor agent"""
    try:
        from agents.agent3_supervisor import get_supervisor as _get_supervisor
        return _get_supervisor()
    except Exception as e:
        logger.error(f"Failed to load Supervisor: {e}")
        return None


# =============================================================================
# HEALTH & STATUS ENDPOINTS
# =============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns the status of the API and connected services.
    """
    services = {"api": "healthy"}
    
    # Check supervisor availability
    supervisor = get_supervisor()
    if supervisor:
        services["supervisor"] = "healthy"
        status = supervisor.get_status()
        services["agent1"] = "healthy" if status.get("agent1_available") else "unavailable"
        services["agent2"] = "healthy" if status.get("agent2_available") else "unavailable"
    else:
        services["supervisor"] = "unavailable"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        services=services
    )


@app.get("/api/agents/status", response_model=AgentStatusResponse, tags=["Agents"])
async def get_agent_status():
    """
    Get the current status of all AI agents.
    
    Returns availability of:
    - Agent 1: Data Processor
    - Agent 2: Financial Analyst  
    - Agent 3: Supervisor
    - Query Agent
    """
    supervisor = get_supervisor()
    
    if not supervisor:
        return AgentStatusResponse(
            supervisor="unavailable",
            agent1_available=False,
            agent2_available=False,
            query_agent_available=False,
            timestamp=datetime.now().isoformat()
        )
    
    status = supervisor.get_status()
    return AgentStatusResponse(
        supervisor=status.get("supervisor", "unknown"),
        agent1_available=status.get("agent1_available", False),
        agent2_available=status.get("agent2_available", False),
        query_agent_available=status.get("query_agent_available", False),
        timestamp=status.get("timestamp", datetime.now().isoformat())
    )


# =============================================================================
# AGENT ENDPOINTS
# =============================================================================

@app.post("/api/agents/process", response_model=ProcessingResponse, tags=["Agents"])
async def process_transactions(request: ProcessTransactionsRequest):
    """
    Trigger Agent 1 to process new transactions for a user.
    
    This will:
    1. Fetch unprocessed transactions
    2. Categorize each transaction using AI
    3. Detect fraud/anomalies
    4. Identify subscriptions
    5. Mark transactions as processed
    
    **Note:** This is a synchronous operation that may take a few seconds.
    """
    logger.info(f"Processing transactions for user: {request.user_id}")
    
    supervisor = get_supervisor()
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor agent not available")
    
    try:
        result = supervisor.handle_request(request.user_id, "process transactions")
        
        return ProcessingResponse(
            status=result.get("status", "error"),
            message=result.get("message", "Processing complete"),
            processed_count=result.get("processed_count", 0),
            agent="data_processor"
        )
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/recommendations/{user_id}", response_model=RecommendationsResponse, tags=["Agents"])
async def get_recommendations(user_id: str):
    """
    Get personalized financial recommendations for a user.
    
    Agent 2 will analyze:
    - Budget health across categories
    - Savings opportunities
    - Subscription optimization
    - Spending trends
    
    Returns actionable recommendations with potential savings amounts.
    """
    logger.info(f"Getting recommendations for user: {user_id}")
    
    supervisor = get_supervisor()
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor agent not available")
    
    try:
        result = supervisor.handle_request(user_id, "generate recommendations")
        
        return RecommendationsResponse(
            status=result.get("status", "error"),
            user_id=user_id,
            total_recommendations=result.get("total_recommendations", 0),
            potential_monthly_savings=result.get("potential_monthly_savings", 0),
            potential_annual_savings=result.get("potential_annual_savings", 0),
            recommendations=result.get("recommendations", []),
            agent=result.get("agent", "financial_analyst")
        )
    except Exception as e:
        logger.error(f"Recommendations failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/summary/{user_id}", response_model=DailySummaryResponse, tags=["Agents"])
async def get_daily_summary(
    user_id: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format. Defaults to today.")
):
    """
    Get a daily spending summary for a user.
    
    Returns:
    - Total amount spent
    - Number of transactions
    - Spending breakdown by category
    - Budget alerts
    - Subscriptions charged that day
    """
    logger.info(f"Getting daily summary for user: {user_id}, date: {date}")
    
    supervisor = get_supervisor()
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor agent not available")
    
    try:
        # Build request with optional date
        request_text = "daily summary"
        if date:
            request_text = f"daily summary for {date}"
        
        result = supervisor.handle_request(user_id, request_text)
        
        return DailySummaryResponse(
            status=result.get("status", "error"),
            user_id=user_id,
            summary_date=result.get("summary_date", date or datetime.now().date().isoformat()),
            total_spent=result.get("total_spent", 0),
            transaction_count=result.get("transaction_count", 0),
            top_category=result.get("top_category", "None"),
            spending_by_category=result.get("spending_by_category", {}),
            budget_alerts=result.get("budget_alerts", []),
            summary_text=result.get("summary_text", result.get("response", ""))
        )
    except Exception as e:
        logger.error(f"Summary failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/chat", response_model=ChatResponse, tags=["Agents"])
async def chat_with_agent(request: ChatRequest):
    """
    Send a natural language message to the AI Supervisor.
    
    The Supervisor will:
    1. Detect your intent
    2. Route to the appropriate agent
    3. Return a helpful response
    
    **Example questions:**
    - "Which subscription costs the most?"
    - "What's my biggest expense category?"
    - "Show unusual spending"
    - "Generate recommendations"
    - "Run full pipeline"
    """
    logger.info(f"Chat request from user {request.user_id}: {request.message[:50]}...")
    
    supervisor = get_supervisor()
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor agent not available")
    
    try:
        result = supervisor.handle_request(request.user_id, request.message)
        
        return ChatResponse(
            status=result.get("status", "error"),
            user_id=request.user_id,
            message=result.get("message"),
            answer=result.get("answer") or result.get("response"),
            data=result.get("data"),
            agent=result.get("agent", "supervisor")
        )
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/pipeline/{user_id}", tags=["Agents"])
async def run_full_pipeline(user_id: str):
    """
    Run the complete processing pipeline for a user.
    
    This executes:
    1. **Agent 1:** Process all new transactions
    2. **Agent 2:** Generate recommendations
    
    Returns combined results from both stages.
    """
    logger.info(f"Running full pipeline for user: {user_id}")
    
    supervisor = get_supervisor()
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor agent not available")
    
    try:
        result = supervisor.run_full_pipeline(user_id)
        return result
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PLAID ENDPOINTS (existing)
# =============================================================================

@app.post("/api/plaid/exchange", response_model=StatusResponse, tags=["Plaid"])
async def exchange_token(request: PlaidExchangeRequest):
    """
    Exchange Plaid public token for access token.
    
    Call this after the user completes Plaid Link to get
    permanent access to their bank account.
    """
    try:
        from src.app.plaid_handler import exchange_public_token
        access_token, item_id = exchange_public_token(request.public_token)
        
        return StatusResponse(
            status="success",
            message=f"Bank connected successfully. Item ID: {item_id}"
        )
    except ImportError:
        raise HTTPException(status_code=501, detail="Plaid integration not configured")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/plaid/transactions", tags=["Plaid"])
async def fetch_plaid_transactions(
    access_token: str = Query(..., description="Plaid access token"),
    days: int = Query(default=30, ge=1, le=365, description="Number of days to fetch")
):
    """
    Fetch transactions from Plaid for a connected account.
    
    Returns raw transactions from the bank. Use `/api/agents/process`
    to process these with AI categorization.
    """
    try:
        from src.app.plaid_handler import get_transactions
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        transactions = get_transactions(access_token, start_date, end_date)
        
        return {
            "status": "success",
            "count": len(transactions),
            "start_date": start_date,
            "end_date": end_date,
            "transactions": transactions
        }
    except ImportError:
        raise HTTPException(status_code=501, detail="Plaid integration not configured")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/", tags=["System"])
async def root():
    """API root - returns basic info and links to docs"""
    return {
        "name": "Smart Expense Analyzer API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/health",
        "endpoints": {
            "agents": {
                "status": "GET /api/agents/status",
                "process": "POST /api/agents/process",
                "recommendations": "GET /api/agents/recommendations/{user_id}",
                "summary": "GET /api/agents/summary/{user_id}",
                "chat": "POST /api/agents/chat",
                "pipeline": "POST /api/agents/pipeline/{user_id}"
            },
            "plaid": {
                "exchange": "POST /api/plaid/exchange",
                "transactions": "GET /api/plaid/transactions"
            }
        }
    }


# =============================================================================
# RUN SERVER (for direct execution)
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
