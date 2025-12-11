# """
# Agent 1: Data Processor - Simplified Version
# Direct processing without ADK agent wrapper
# """

# from mcp_toolbox.tools.data_processor import DataProcessorAgent


# class DataProcessorLLMAgent:
#     """Simplified wrapper for Data Processor - direct processing only"""

#     def __init__(self):
#         self.tool_agent = DataProcessorAgent()

#     def process_transactions(self, user_id: str):
#         """Process all unprocessed transactions for a user"""
#         return self.tool_agent.process_user_transactions(user_id)


# if __name__ == "__main__":
#     import sys
#     import json
    
#     print("\n" + "="*70)
#     print("AGENT 1: DATA PROCESSOR - DIRECT PROCESSING MODE")
#     print("="*70 + "\n")
    
#     if len(sys.argv) > 1:
#         user_id = sys.argv[1]
#     else:
#         user_id = "dfea6d34-dc5d-407e-b39a-329ad905cc57"
#         print(f"No user_id provided, using default: {user_id}\n")
    
#     try:
#         print("Initializing Data Processor Agent...")
#         agent = DataProcessorLLMAgent()
#         print("✓ Agent initialized successfully\n")
        
#         print("="*70)
#         print("PROCESSING TRANSACTIONS")
#         print("="*70)
#         result = agent.process_transactions(user_id)
        
#         print("\n" + "="*70)
#         print("RESULTS")
#         print("="*70)
#         print(json.dumps(result, indent=2))
#         print("="*70 + "\n")
        
#     except Exception as e:
#         print(f"\n❌ ERROR: {e}\n")
#         import traceback
#         traceback.print_exc()

"""
Agent 1: Data Processor - LLM-Enhanced Version
File: mcp_toolbox/agents/agent_data_processor.py

Hybrid Approach:
- Processing logic: Hardcoded (fast, deterministic)
- Result descriptions: LLM-generated (natural, insightful)
"""

from mcp_toolbox.tools.data_processor import DataProcessorAgent
from google import genai
from google.genai import types


class DataProcessorLLMAgent:
    """LLM-enhanced wrapper for Data Processor"""

    def __init__(self):
        self.tool_agent = DataProcessorAgent()
        
        # Initialize Gemini client for text generation
        try:
            self.llm_client = genai.Client()
            self.use_llm = True
            print("✓ LLM enabled for natural language summaries")
        except Exception as e:
            print(f"⚠️ LLM unavailable, using templates: {e}")
            self.use_llm = False

    def process_transactions(self, user_id: str):
        """
        Process transactions with hardcoded logic,
        then generate LLM-powered summary
        """
        
        # STEP 1: Use hardcoded logic for actual processing (fast!)
        print("\n🔧 Processing transactions with rule-based logic...")
        result = self.tool_agent.process_user_transactions(user_id)
        
        if result.get('processed_count', 0) == 0:
            return result
        
        # STEP 2: Use LLM to generate natural summary (intelligent!)
        if self.use_llm:
            print("✨ Generating AI-powered summary...\n")
            
            result['ai_summary'] = self._generate_llm_summary(result)
            result['llm_enhanced'] = True
        else:
            result['ai_summary'] = self._generate_template_summary(result)
            result['llm_enhanced'] = False
        
        return result
    
    def _generate_llm_summary(self, processing_result: dict) -> str:
        """Use LLM to generate natural language summary"""
        
        try:
            prompt = f"""
You are a financial assistant summarizing transaction processing results.

PROCESSING RESULTS:
- Transactions processed: {processing_result.get('processed_count', 0)}
- Bills detected: {processing_result.get('bills_detected', 0)}
- Subscriptions detected: {processing_result.get('subscriptions_detected', 0)}
- Spending categories: {processing_result.get('patterns_calculated', 0)}
- Anomalies flagged: {processing_result.get('anomalies_flagged', 0)}

Generate a brief, friendly summary (2-3 sentences) highlighting:
1. What was processed
2. Key findings (bills, subscriptions, anomalies)
3. A helpful next step

Be conversational and encouraging. Use emojis appropriately.
"""
            
            response = self.llm_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,  # Creative but not too random
                    max_output_tokens=200
                )
            )
            
            return response.text.strip()
        
        except Exception as e:
            print(f"LLM summary failed: {e}")
            return self._generate_template_summary(processing_result)
    
    def _generate_template_summary(self, result: dict) -> str:
        """Fallback template-based summary"""
        
        summary = f"✅ Processed {result.get('processed_count', 0)} transactions. "
        
        if result.get('bills_detected', 0) > 0:
            summary += f"Found {result['bills_detected']} recurring bills. "
        
        if result.get('subscriptions_detected', 0) > 0:
            summary += f"Detected {result['subscriptions_detected']} subscriptions. "
        
        if result.get('anomalies_flagged', 0) > 0:
            summary += f"⚠️ Flagged {result['anomalies_flagged']} unusual transactions for review."
        
        return summary


if __name__ == "__main__":
    import sys
    import json
    
    print("\n" + "="*70)
    print("AGENT 1: LLM-ENHANCED DATA PROCESSOR")
    print("="*70 + "\n")
    
    user_id = sys.argv[1] if len(sys.argv) > 1 else "dfea6d34-dc5d-407e-b39a-329ad905cc57"
    
    try:
        agent = DataProcessorLLMAgent()
        result = agent.process_transactions(user_id)
        
        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)
        
        # Show statistics
        print(f"Processed: {result.get('processed_count', 0)}")
        print(f"Bills: {result.get('bills_detected', 0)}")
        print(f"Subscriptions: {result.get('subscriptions_detected', 0)}")
        print(f"Anomalies: {result.get('anomalies_flagged', 0)}")
        
        # Show AI summary
        if result.get('ai_summary'):
            print("\n" + "="*70)
            print("AI SUMMARY")
            print("="*70)
            print(result['ai_summary'])
            
            if result.get('llm_enhanced'):
                print("\n✨ This summary was generated by Gemini AI")
            else:
                print("\n📝 Template-based summary (LLM unavailable)")
        
        print("\n" + "="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()