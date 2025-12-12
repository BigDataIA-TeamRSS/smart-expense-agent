import logging
from agents.agent1_data_processor import process_user_transactions_agent1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    user_id = "fd47f678-0c8a-42b5-8af2-936ec0e370c5"
    logger.info(f"Processing transactions for user: {user_id}")

    # This call remains the same, as the changes were internal to the agent file.
    response_text = process_user_transactions_agent1(user_id)
    
    print("\n=== AGENT 1 FINAL RESPONSE ===\n")
    print(response_text)

if __name__ == "__main__":
    main()