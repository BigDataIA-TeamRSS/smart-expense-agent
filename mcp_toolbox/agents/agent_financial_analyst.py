"""
Agent 2: Financial Analyst - LLM-Enhanced
File: mcp_toolbox/agents/agent_financial_analyst.py

COPY THIS ENTIRE FILE - REPLACES YOUR CURRENT agent_financial_analyst.py
"""

from mcp_toolbox.tools.financial_analyst import FinancialAnalystAgent
from google import genai
from google.genai import types
import json


class FinancialAnalystLLMAgent:

    def __init__(self):
        self.tool_agent = FinancialAnalystAgent()
        
        try:
            self.llm_client = genai.Client()
            self.use_llm = True
            print("✓ LLM enabled for personalized recommendations")
        except Exception as e:
            print(f"⚠️ LLM unavailable: {e}")
            self.use_llm = False

    def generate_recommendations(self, user_id: str):
        """Generate recommendations with LLM-enhanced descriptions"""
        
        print("\n🔧 Analyzing with threshold-based logic...")
        result = self.tool_agent.generate_recommendations(user_id)
        
        if result.get('total_recommendations', 0) == 0:
            return result
        
        if self.use_llm and result.get('recommendations'):
            print("✨ Personalizing recommendations with AI...\n")
            
            enhanced_recs = []
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"   Enhancing {i}/{len(result['recommendations'])}...")
                enhanced = self._enhance_recommendation_with_llm(rec)
                enhanced_recs.append(enhanced)
            
            result['recommendations'] = enhanced_recs
            result['ai_overview'] = self._generate_overview_with_llm(result)
            result['llm_enhanced'] = True
        else:
            result['llm_enhanced'] = False
        
        return result
    
    def generate_daily_summary(self, user_id: str, date: str = None):
        """Generate summary with LLM-powered narrative"""
        
        print("\n🔧 Calculating metrics...")
        result = self.tool_agent.generate_daily_summary(user_id, date)
        
        if self.use_llm and result.get('status') == 'success':
            print("✨ Creating AI narrative...\n")
            result['ai_narrative'] = self._generate_narrative_summary(result)
            result['llm_enhanced'] = True
        else:
            result['llm_enhanced'] = False
        
        return result
    
    def _enhance_recommendation_with_llm(self, rec: dict) -> dict:
        """Make recommendation personal and actionable with LLM"""
        
        try:
            prompt = f"""You are a friendly financial advisor. Rewrite this recommendation to be warm and actionable.

CURRENT:
Title: {rec['title']}
Description: {rec['description']}
Savings: ${rec['potential_savings']:.2f}/month

Create a better description (2-3 sentences) that:
1. Acknowledges the situation positively
2. Gives specific, practical advice
3. Motivates action

Be conversational, use "you", keep it friendly."""
            
            response = self.llm_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=150)
            )
            
            enhanced = rec.copy()
            enhanced['description'] = response.text.strip()
            enhanced['llm_generated'] = True
            
            return enhanced
        
        except Exception as e:
            print(f"   LLM enhancement failed: {e}")
            return rec
    
    def _generate_overview_with_llm(self, result: dict) -> str:
        """Generate encouraging overview of all recommendations"""
        
        try:
            recs_info = [
                f"{r['title']}: ${r['potential_savings']:.2f}/month" 
                for r in result['recommendations'][:3]
            ]
            
            prompt = f"""You are a supportive financial advisor.

USER HAS:
- {result['total_recommendations']} recommendations
- Potential savings: ${result.get('potential_monthly_savings', 0):.2f}/month

TOP OPPORTUNITIES:
{chr(10).join(recs_info)}

Write a brief, motivating overview (2 sentences) that highlights the savings potential and encourages action.
Be warm and positive."""
            
            response = self.llm_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=100)
            )
            
            return response.text.strip()
        
        except Exception as e:
            print(f"LLM overview failed: {e}")
            return f"Found {result['total_recommendations']} ways to save ${result.get('potential_monthly_savings', 0):.2f}/month."
    
    def _generate_narrative_summary(self, summary: dict) -> str:
        """Generate engaging daily summary narrative"""
        
        try:
            spending_str = json.dumps(summary.get('spending_by_category', {}), indent=2)
            
            prompt = f"""You are a friendly financial assistant.

TODAY'S ACTIVITY:
- Spent: ${summary.get('total_spent', 0):.2f}
- Transactions: {summary.get('transaction_count', 0)}
- Top category: {summary.get('top_category')}
- Budget alerts: {len(summary.get('budget_alerts', []))}

SPENDING:
{spending_str}

Write a warm, conversational daily summary (3-4 sentences) that:
1. Highlights the day's activity
2. Notes patterns or concerns
3. Ends with encouragement or advice

Be personal and supportive."""
            
            response = self.llm_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.7, max_output_tokens=200)
            )
            
            return response.text.strip()
        
        except Exception as e:
            print(f"LLM narrative failed: {e}")
            return summary.get('summary_text', 'Summary unavailable')


if __name__ == "__main__":
    import sys
    import json
    
    print("\n" + "="*70)
    print("AGENT 2: LLM-ENHANCED FINANCIAL ANALYST")
    print("="*70 + "\n")
    
    user_id = sys.argv[1] if len(sys.argv) > 1 else "dfea6d34-dc5d-407e-b39a-329ad905cc57"
    
    try:
        agent2 = FinancialAnalystLLMAgent()
        
        print("="*70)
        print("TEST 1: RECOMMENDATIONS")
        print("="*70)
        result = agent2.generate_recommendations(user_id)
        
        print(f"\nTotal: {result.get('total_recommendations', 0)}")
        print(f"Savings: ${result.get('potential_monthly_savings', 0):.2f}/month")
        
        if result.get('ai_overview'):
            print("\n✨ AI OVERVIEW:")
            print(result['ai_overview'])
        
        if result.get('recommendations'):
            print("\n💡 SAMPLE RECOMMENDATION:")
            rec = result['recommendations'][0]
            print(f"   {rec['title']}")
            print(f"   {rec['description'][:150]}...")
            if rec.get('llm_generated'):
                print(f"   ✨ (AI-personalized)")
        
        print("\n" + "="*70)
        print("TEST 2: DAILY SUMMARY")
        print("="*70)
        summary = agent2.generate_daily_summary(user_id)
        
        print(f"\nSpending: ${summary.get('total_spent', 0):.2f}")
        print(f"Transactions: {summary.get('transaction_count', 0)}")
        
        if summary.get('ai_narrative'):
            print("\n✨ AI NARRATIVE:")
            print(summary['ai_narrative'])
        
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()