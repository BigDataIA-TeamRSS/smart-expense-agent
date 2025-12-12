"""AI agent endpoints"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.app.dependencies import get_current_user, get_db

router = APIRouter()


class ChatRequest(BaseModel):
    """Request schema for AI chat"""
    message: str


class ChatResponse(BaseModel):
    """Response schema for AI chat"""
    response: str


@router.post("/recommendations")
async def get_recommendations(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get AI-generated financial recommendations"""
    try:
        from mcp_toolbox.agents.agent_financial_analyst import FinancialAnalystLLMAgent
        
        agent = FinancialAnalystLLMAgent()
        recommendations = agent.generate_recommendations(current_user["id"])
        
        return recommendations
    except Exception as e:
        return {
            "error": str(e),
            "recommendations": []
        }


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Chat with AI financial assistant"""
    try:
        from mcp_toolbox.agents.query_agent import QueryAgent
        
        agent = QueryAgent()
        response = agent.query(current_user["id"], request.message)
        
        return ChatResponse(response=response)
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")


@router.post("/daily-summary")
async def get_daily_summary(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Generate daily financial summary"""
    try:
        from mcp_toolbox.agents.agent_financial_analyst import FinancialAnalystLLMAgent
        
        agent = FinancialAnalystLLMAgent()
        summary = agent.generate_daily_summary(current_user["id"])
        
        return summary
    except Exception as e:
        return {
            "error": str(e),
            "summary": ""
        }
