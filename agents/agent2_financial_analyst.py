"""
Agent 2: Financial Analyst - Google ADK Implementation
File: agents/agent2_financial_analyst.py

Uses Google ADK (Agent Development Kit) to create an LLM-powered financial analyst
that generates personalized recommendations and summaries.
"""

import logging
import uuid
import asyncio
from typing import Dict, Any, Optional

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from google.adk.sessions import Session

# Import ADK-compatible tool functions
from agent_tools.financial_analyst_tools import (
    analyze_budget_health,
    find_savings_opportunities,
    optimize_subscriptions,
    predict_spending_trends,
    generate_daily_summary,
    save_recommendation
)

logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
APP_NAME = "agent2_financial_analyst_app"
MODEL_NAME = "gemini-2.0-flash"  # Using same model pattern as Agent 1

# --- AGENT DEFINITION ---
# Define Agent 2 using Google ADK LlmAgent
agent2_financial_analyst = LlmAgent(
    name="agent2_financial_analyst",
    model=MODEL_NAME,
    description="""Agent 2: Financial Analyst - Analyzes spending patterns and generates 
    personalized financial recommendations. Can analyze budgets, find savings opportunities,
    optimize subscriptions, predict spending trends, and generate daily summaries.""",
    instruction="""You are a helpful financial analyst assistant. Your job is to help users
    understand their spending patterns and find ways to save money.
    
    When asked to generate recommendations:
    1. First analyze budget health to find overspending
    2. Then find savings opportunities in discretionary categories  
    3. Check subscription spending for optimization
    4. Look at spending trends to predict future issues
    5. Combine all insights into actionable recommendations
    
    When asked for a daily summary:
    1. Generate the daily summary for the requested date
    2. Present it in a clear, friendly format
    
    Always be encouraging and specific with your advice. Focus on actionable steps
    the user can take to improve their financial health.
    Give ouput in s structured , proper format to display on UI""",
    tools=[
        FunctionTool(analyze_budget_health),
        FunctionTool(find_savings_opportunities),
        FunctionTool(optimize_subscriptions),
        FunctionTool(predict_spending_trends),
        FunctionTool(generate_daily_summary),
        FunctionTool(save_recommendation),
    ]
)

# --- RUNNER SETUP ---
# InMemoryRunner handles session management internally
agent2_runner = InMemoryRunner(
    agent=agent2_financial_analyst,
    app_name=APP_NAME
)


class FinancialAnalystLLMAgent:
    """
    Wrapper class for Agent 2: Financial Analyst
    Provides a clean interface for the Supervisor and UI to interact with.
    """
    
    def __init__(self):
        logger.info("Initializing Agent 2: Financial Analyst (ADK)")
        self.agent = agent2_financial_analyst
        self.runner = agent2_runner
        logger.info("✓ Agent 2 initialized with ADK")
    
    def generate_recommendations(self, user_id: str) -> Dict[str, Any]:
        """
        Generate personalized financial recommendations for a user.
        
        Uses a HYBRID approach:
        1. Call tool functions directly to get structured results
        2. Aggregate recommendations from all tools
        3. Use LLM to generate a friendly summary narrative
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            Dictionary with recommendations and savings potential
        """
        logger.info(f"Agent 2: Generating recommendations for user {user_id}")
        
        all_recommendations = []
        
        # Step 1: Call each analysis tool directly to get structured results
        logger.info("Step 1: Analyzing budget health...")
        budget_result = analyze_budget_health(user_id)
        if budget_result.get('status') == 'success':
            recs = budget_result.get('recommendations', [])
            all_recommendations.extend(recs)
            logger.info(f"  → Found {len(recs)} budget recommendations")
        
        logger.info("Step 2: Finding savings opportunities...")
        savings_result = find_savings_opportunities(user_id)
        if savings_result.get('status') == 'success':
            opps = savings_result.get('opportunities', [])
            all_recommendations.extend(opps)
            logger.info(f"  → Found {len(opps)} savings opportunities")
        
        logger.info("Step 3: Optimizing subscriptions...")
        subs_result = optimize_subscriptions(user_id)
        if subs_result.get('status') == 'success':
            recs = subs_result.get('recommendations', [])
            all_recommendations.extend(recs)
            logger.info(f"  → Found {len(recs)} subscription recommendations")
        
        logger.info("Step 4: Predicting trends...")
        trends_result = predict_spending_trends(user_id)
        if trends_result.get('status') == 'success':
            alerts = trends_result.get('alerts', [])
            all_recommendations.extend(alerts)
            logger.info(f"  → Found {len(alerts)} trend alerts")
        
        # Step 2: Calculate totals
        total_monthly_savings = sum(
            r.get('potential_savings', 0) for r in all_recommendations
        )
        total_annual_savings = total_monthly_savings * 12
        high_priority = sum(1 for r in all_recommendations if r.get('priority', 5) <= 2)
        
        logger.info(f"Total: {len(all_recommendations)} recommendations, ${total_monthly_savings:.2f}/month potential savings")
        
        # Step 3: Generate LLM summary (optional enhancement)
        summary_text = ""
        if all_recommendations:
            try:
                summary_prompt = f"""Summarize these financial recommendations in 2-3 friendly sentences:
                
Total recommendations: {len(all_recommendations)}
High priority items: {high_priority}
Potential monthly savings: ${total_monthly_savings:.2f}

Top recommendations:
{chr(10).join(f"- {r.get('title', 'Recommendation')}: {r.get('description', '')[:100]}" for r in all_recommendations[:3])}

Be encouraging and actionable."""
                
                summary_text = self._run_agent(user_id, summary_prompt)
            except Exception as e:
                logger.warning(f"LLM summary failed, using default: {e}")
                summary_text = f"Found {len(all_recommendations)} ways to improve your finances with potential savings of ${total_monthly_savings:.2f}/month!"
        else:
            summary_text = "Great news! Your finances look healthy. Keep up the good work!"
        
        return {
            "status": "success",
            "agent": "Agent 2 - Financial Analyst (ADK)",
            "user_id": user_id,
            "total_recommendations": len(all_recommendations),
            "high_priority": high_priority,
            "potential_monthly_savings": total_monthly_savings,
            "potential_annual_savings": total_annual_savings,
            "recommendations": all_recommendations,
            "response": summary_text,
            "raw_output": summary_text,
            # Include sub-results for debugging
            "details": {
                "budget": budget_result,
                "savings": savings_result,
                "subscriptions": subs_result,
                "trends": trends_result
            }
        }
    
    def generate_daily_summary(self, user_id: str, summary_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a daily spending summary for a user.
        
        Args:
            user_id: The unique identifier of the user
            summary_date: Optional date in YYYY-MM-DD format. Defaults to today.
            
        Returns:
            Dictionary with daily summary information
        """
        from datetime import datetime
        
        if not summary_date:
            summary_date = datetime.now().date().isoformat()
        
        logger.info(f"Agent 2: Generating daily summary for user {user_id} on {summary_date}")
        
        prompt_text = f"""Generate a daily spending summary for user: {user_id}
Date: {summary_date}

Please:
1. Generate the daily summary using the generate_daily_summary tool
2. Format it in a friendly, easy-to-read way
3. Highlight any concerns or positive trends
4. Keep it concise but informative

Execute now."""

        result = self._run_agent(user_id, prompt_text)
        
        return {
            "status": "success",
            "agent": "Agent 2 - Financial Analyst (ADK)",
            "user_id": user_id,
            "summary_date": summary_date,
            "response": result,
            "raw_output": result
        }
    
    def _run_agent(self, user_id: str, prompt: str) -> str:
        """
        Run the ADK agent with a prompt and return the response.
        
        Args:
            user_id: User ID for session management
            prompt: The prompt to send to the agent
            
        Returns:
            The agent's text response
        """
        logger.info(f"Running Agent 2 ADK for user {user_id}")
        
        user_message = Content(
            parts=[Part(text=prompt)],
            role="user"
        )
        
        try:
            # Create unique session
            unique_session_id = str(uuid.uuid4())
            logger.debug(f"Creating session with ID: {unique_session_id}")
            
            # Async session creation
            async def create_session_async() -> Session:
                return await agent2_runner.session_service.create_session(
                    app_name=APP_NAME,
                    user_id=user_id,
                    session_id=unique_session_id
                )
            
            session_object = asyncio.run(create_session_async())
            
            # Run the agent
            events = agent2_runner.run(
                user_id=user_id,
                session_id=session_object.id,
                new_message=user_message
            )
            
            # Collect response from events
            output_text = ""
            for event in events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            output_text = part.text.strip()
            
            if not output_text:
                output_text = "Analysis complete. Check the detailed tool outputs for specific recommendations."
            
            logger.info("✓ Agent 2 completed successfully")
            return output_text
            
        except Exception as e:
            logger.error(f"Agent 2 failed: {e}", exc_info=True)
            return f"Error running financial analysis: {str(e)}"


# --- DIRECT FUNCTION FOR EXTERNAL CALLS ---
def run_financial_analysis(user_id: str, analysis_type: str = "recommendations") -> Dict[str, Any]:
    """
    Convenience function to run financial analysis without instantiating the class.
    
    Args:
        user_id: The user to analyze
        analysis_type: Either "recommendations" or "daily_summary"
        
    Returns:
        Analysis results
    """
    agent = FinancialAnalystLLMAgent()
    
    if analysis_type == "daily_summary":
        return agent.generate_daily_summary(user_id)
    else:
        return agent.generate_recommendations(user_id)


# --- TEST ENTRYPOINT ---
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    user_id = sys.argv[1] if len(sys.argv) > 1 else "test-user-123"
    
    print("\n" + "="*70)
    print("AGENT 2: FINANCIAL ANALYST (ADK) - TEST")
    print("="*70)
    
    agent = FinancialAnalystLLMAgent()
    
    print("\n--- Test 1: Recommendations ---")
    result = agent.generate_recommendations(user_id)
    print(f"Status: {result['status']}")
    print(f"Response:\n{result['response']}")
    
    print("\n--- Test 2: Daily Summary ---")
    result = agent.generate_daily_summary(user_id)
    print(f"Status: {result['status']}")
    print(f"Response:\n{result['response']}")
