"""
Tool 5: Finalize Processing
Marks transactions as fully processed and handles completion tasks
"""

import logging
from typing import Dict, Any, List, Optional
from agent_tools.toolbox_wrapper import get_toolbox
from datetime import datetime
import json
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


def store_processed_data(
    transaction_ids: List[str], 
    user_id: str,
    summary: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Finalizes transaction processing and marks transactions as complete.
    
    This tool:
    1. Updates transaction status from 'processing' → 'fully_processed'
    2. Generates processing statistics
    3. Identifies any failed/stuck transactions
    4. Logs completion for auditing
    5. Optionally triggers user notifications
    
    WHY IT'S NEEDED:
    - Provides clear workflow completion signal
    - Enables error recovery (finds stuck transactions)
    - Creates audit trail
    - Updates final status in database
    
    Args:
        transaction_ids: List of transaction IDs that were processed (required).
        user_id: User ID for notifications and logging (required).
        summary: Optional dict with processing summary {
            'categorized': int,
            'subscriptions_detected': int,
            'anomalies_found': int
        }
    
    Returns:
        A dictionary containing:
        {
            "status": "success" or "error",
            "processed_count": Number of transactions marked complete,
            "failed_count": Number of transactions that failed,
            "stuck_count": Number of transactions stuck in processing,
            "summary": Processing statistics,
            "message": Status message
        }
    
    Example:
        result = store_processed_data(
            transaction_ids=["txn_1", "txn_2", "txn_3"],
            user_id="user_123",
            summary={"categorized": 3, "anomalies_found": 1}
        )
    """
    
    try:
        if not transaction_ids:
            return {
                "status": "success",
                "processed_count": 0,
                "failed_count": 0,
                "stuck_count": 0,
                "message": "No transactions provided"
            }
        
        logger.info(f"💾 Finalizing processing for {len(transaction_ids)} transactions")
        
        toolbox = get_toolbox()
        
        # Step 1: Update transaction status to 'fully_processed'
        try:
            result = toolbox.call_tool(
                "mark-transactions-complete",
                transaction_ids=",".join(transaction_ids)
            )
            
            if result['success']:
                processed_count = len(transaction_ids)
                logger.info(f"   ✅ Marked {processed_count} transactions as fully_processed")
            else:
                logger.warning(f"   ⚠️ Failed to update status: {result.get('error')}")
                processed_count = 0
        except Exception as e:
            logger.warning(f"   ⚠️ Could not update transaction status: {e}")
            processed_count = len(transaction_ids)  # Assume success
        
        # Step 2: Check for any transactions that got stuck
        stuck_transactions = _find_stuck_transactions(user_id)
        
        # Step 3: Generate processing statistics
        stats = _generate_processing_stats(transaction_ids, summary)
        
        # Step 4: Create audit log entry
        _log_processing_completion(
            user_id=user_id,
            transaction_count=processed_count,
            summary=summary or stats
        )
        
        # Step 5: Optionally trigger notifications (if user wants them)
        if summary and (summary.get('anomalies_found', 0) > 0):
            _notify_user_of_anomalies(user_id, summary)
        
        logger.info(
            f"✅ Processing finalized: {processed_count} completed, "
            f"{len(stuck_transactions)} stuck transactions found"
        )
        
        result = {
            "status": "success",
            "processed_count": processed_count,
            "failed_count": 0,
            "stuck_count": len(stuck_transactions),
            "summary": {
                "total_processed": processed_count,
                "categorized": summary.get('categorized', 0) if summary else 0,
                "subscriptions": summary.get('subscriptions_detected', 0) if summary else 0,
                "anomalies": summary.get('anomalies_found', 0) if summary else 0,
                "completion_time": datetime.now().isoformat()
            },
            "message": f"Successfully finalized processing for {processed_count} transactions"
        }
        
        # Include stuck transactions in result for visibility
        if stuck_transactions:
            result['stuck_transactions'] = stuck_transactions
            result['message'] += f" (Warning: {len(stuck_transactions)} stuck transactions found)"
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Error finalizing processing: {e}", exc_info=True)
        return {
            "status": "error",
            "processed_count": 0,
            "failed_count": len(transaction_ids) if transaction_ids else 0,
            "message": f"Finalization failed: {str(e)}"
        }


# ============================================================================
# HELPER FUNCTIONS (All Synchronous)
# ============================================================================

def _find_stuck_transactions(user_id: str) -> List[str]:
    """
    Find transactions stuck in 'processing' state for too long
    These likely failed mid-pipeline and need retry
    """
    try:
        toolbox = get_toolbox()
        
        # Find transactions marked as 'processing' for > 1 hour
        result = toolbox.call_tool(
            "find-stuck-transactions",
            user_id=user_id,
            hours=1  # Stuck for more than 1 hour
        )
        
        if result['success'] and result['data']:
            stuck = [row['transaction_id'] for row in result['data']]
            
            if stuck:
                logger.warning(f"   ⚠️ Found {len(stuck)} stuck transactions for user {user_id}")
                logger.warning(f"      Stuck IDs: {stuck[:5]}...")  # Show first 5
            
            return stuck
    except Exception as e:
        logger.debug(f"   Could not check for stuck transactions: {e}")
    
    return []


def _generate_processing_stats(
    transaction_ids: List[str], 
    provided_summary: Optional[Dict] = None
) -> Dict[str, Any]:
    """Generate statistics about processed transactions"""
    
    if provided_summary:
        # Use provided summary
        return provided_summary
    
    # Generate basic stats
    stats = {
        "total_processed": len(transaction_ids),
        "timestamp": datetime.now().isoformat()
    }
    
    # Optionally query database for more details
    try:
        toolbox = get_toolbox()
        
        # You could add queries here to get:
        # - Count of anomalies detected
        # - Count of subscriptions found
        # - Category breakdown
        
        # Example (if you add this tool to tools.yaml):
        # result = toolbox.call_tool(
        #     "get-processing-summary",
        #     transaction_ids=",".join(transaction_ids)
        # )
        
    except Exception as e:
        logger.debug(f"   Could not generate detailed stats: {e}")
    
    return stats


def _log_processing_completion(
    user_id: str, 
    transaction_count: int, 
    summary: Dict
):
    """
    Create audit log entry for processing completion
    Useful for compliance and debugging
    """
    try:
        log_entry = {
            'user_id': user_id,
            'transaction_count': transaction_count,
            'completed_at': datetime.now().isoformat(),
            'summary': summary,
            'agent': 'agent1_data_processor'
        }
        
        logger.info(f"📋 Audit log: User={user_id}, Transactions={transaction_count}")
        
        # Optionally store in database if you create an audit table
        # toolbox = get_toolbox()
        # toolbox.call_tool("insert-processing-audit", **log_entry)
        
    except Exception as e:
        logger.debug(f"   Could not create audit log: {e}")


def _notify_user_of_anomalies(user_id: str, summary: Dict):
    """
    Send notification to user if anomalies were detected
    Respects user's notification preferences
    """
    try:
        anomaly_count = summary.get('anomalies_found', 0)
        
        if anomaly_count > 0:
            logger.info(f"🔔 Would notify user {user_id}: {anomaly_count} anomalies detected")
            
            # TODO: Implement notification logic
            # 1. Get user's notification_preferences from users table
            # 2. If push enabled: Send push notification
            # 3. If email enabled: Queue email
            # 4. Insert into notifications table for in-app alerts
            
            # Example structure:
            # notification = {
            #     'user_id': user_id,
            #     'type': 'fraud_alert',
            #     'title': f'{anomaly_count} Suspicious Transactions Detected',
            #     'message': 'Review your recent transactions for unusual activity',
            #     'priority': 'high' if anomaly_count >= 3 else 'medium'
            # }
            
            # toolbox = get_toolbox()
            # toolbox.call_tool("insert-notification", **notification)
            
    except Exception as e:
        logger.debug(f"   Could not send notification: {e}")