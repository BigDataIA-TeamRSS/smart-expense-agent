"""FastAPI application for Smart Expense Analyzer - Cloud Run deployment"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Import routers
from src.app.routers import (
    auth,
    accounts,
    transactions,
    plaid,
    statements,
    analytics,
    ai_agents
)

# Import exception handlers
from src.app.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown tasks"""
    # Startup
    yield
    # Shutdown (if needed)


# Create FastAPI app
app = FastAPI(
    title="Smart Expense Analyzer API",
    description="Financial analysis API with Plaid integration and AI insights",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration - Allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication & Users"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(plaid.router, prefix="/api/plaid", tags=["Plaid"])
app.include_router(statements.router, prefix="/api/statements", tags=["Statements"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(ai_agents.router, prefix="/api/ai", tags=["AI Agents"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Smart Expense Analyzer API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
