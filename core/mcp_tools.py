"""
MCP Toolbox wrapper for PostgreSQL operations
Handles all database interactions via MCP
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class MCPDatabaseTools:
    """
    Wrapper around MCP toolbox for database operations
    Provides typed methods for common operations
    """
    
    def __init__(self, mcp_client):
        """
        Args:
            mcp_client: Your MCP toolbox client instance
        """
        self.mcp = mcp_client
    
    # ========================================
    # TRANSACTION OPERATIONS
    # ========================================
    
    async def get_unprocessed_transactions(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Get transactions that haven't been processed yet"""
        query = """
            SELECT 
                t.transaction_id,
                t.user_id,
                t.account_id,
                t.date,
                t.amount,
                t.description,
                t.merchant_name,
                t.transaction_type
            FROM transactions t
            WHERE t.user_id = $1
              AND t.processing_status = 'unprocessed'
            ORDER BY t.date DESC
            LIMIT $2
        """
        
        result = await self.mcp.execute_query(query, [user_id, limit])
        return result.get('rows', [])
    
    async def mark_transaction_processing_started(self, transaction_id: str):
        """Mark transaction as being processed"""
        query = """
            UPDATE transactions
            SET processing_status = 'processing',
                last_processed_at = CURRENT_TIMESTAMP
            WHERE transaction_id = $1
        """
        await self.mcp.execute_query(query, [transaction_id])
    
    async def mark_transaction_processed(self, transaction_id: str):
        """Mark transaction as fully processed"""
        query = """
            UPDATE transactions
            SET processing_status = 'fully_processed',
                last_processed_at = CURRENT_TIMESTAMP
            WHERE transaction_id = $1
        """
        await self.mcp.execute_query(query, [transaction_id])
    
    # ========================================
    # PROCESSING LOG OPERATIONS
    # ========================================
    
    async def start_processing_log(
        self,
        transaction_id: str,
        agent_name: str,
        stage: str
    ) -> str:
        """Create a new processing log entry"""
        query = """
            INSERT INTO processing_log 
                (transaction_id, agent_name, stage, status, started_at, attempt_number)
            VALUES ($1, $2, $3, 'running', CURRENT_TIMESTAMP, 1)
            RETURNING id
        """
        
        result = await self.mcp.execute_query(
            query,
            [transaction_id, agent_name, stage]
        )
        
        log_id = result['rows'][0]['id']
        logger.info(f"Created processing log {log_id} for {agent_name}:{stage}")
        return log_id
    
    async def update_processing_log(
        self,
        log_id: str,
        status: str,
        output_summary: Optional[Dict] = None,
        error_message: Optional[str] = None,
        attempt_number: Optional[int] = None
    ):
        """Update processing log entry"""
        updates = []
        params = []
        param_idx = 1
        
        updates.append(f"status = ${param_idx}")
        params.append(status)
        param_idx += 1
        
        if status == 'completed':
            updates.append(f"completed_at = CURRENT_TIMESTAMP")
            updates.append(f"duration_ms = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)) * 1000")
        
        if output_summary:
            updates.append(f"output_summary = ${param_idx}")
            params.append(json.dumps(output_summary))
            param_idx += 1
        
        if error_message:
            updates.append(f"error_message = ${param_idx}")
            params.append(error_message)
            param_idx += 1
        
        if attempt_number:
            updates.append(f"attempt_number = ${param_idx}")
            params.append(attempt_number)
            param_idx += 1
        
        params.append(log_id)
        
        query = f"""
            UPDATE processing_log
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
        """
        
        await self.mcp.execute_query(query, params)
    
    # ========================================
    # PROCESSED TRANSACTIONS
    # ========================================
    
    async def insert_processed_transaction(self, data: Dict) -> str:
        """Insert AI-enhanced transaction data"""
        query = """
            INSERT INTO processed_transactions (
                transaction_id, user_id, category_ai, merchant_standardized,
                is_subscription, subscription_id, subscription_confidence,
                is_anomaly, anomaly_score, anomaly_reason,
                is_bill, tags, notes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (transaction_id) 
            DO UPDATE SET
                category_ai = EXCLUDED.category_ai,
                merchant_standardized = EXCLUDED.merchant_standardized,
                is_subscription = EXCLUDED.is_subscription,
                is_anomaly = EXCLUDED.is_anomaly,
                anomaly_score = EXCLUDED.anomaly_score,
                processed_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        
        result = await self.mcp.execute_query(query, [
            data['transaction_id'],
            data['user_id'],
            data['category_ai'],
            data.get('merchant_standardized'),
            data.get('is_subscription', False),
            data.get('subscription_id'),
            data.get('subscription_confidence'),
            data.get('is_anomaly', False),
            data.get('anomaly_score'),
            data.get('anomaly_reason'),
            data.get('is_bill', False),
            data.get('tags', []),
            data.get('notes')
        ])
        
        return result['rows'][0]['id']
    
    # ========================================
    # SUBSCRIPTIONS
    # ========================================
    
    async def get_user_subscriptions(
        self,
        user_id: str,
        merchant_standardized: Optional[str] = None
    ) -> List[Dict]:
        """Get user's existing subscriptions"""
        query = """
            SELECT * FROM subscriptions
            WHERE user_id = $1
              AND status = 'active'
        """
        
        params = [user_id]
        
        if merchant_standardized:
            query += " AND merchant_standardized = $2"
            params.append(merchant_standardized)
        
        result = await self.mcp.execute_query(query, params)
        return result.get('rows', [])
    
    async def insert_subscription(self, data: Dict) -> str:
        """Create new subscription record"""
        query = """
            INSERT INTO subscriptions (
                user_id, merchant_name, merchant_standardized, amount,
                frequency, frequency_days, start_date, last_charge_date,
                next_expected_date, status, category, confidence,
                detection_method, occurrence_count
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING id
        """
        
        result = await self.mcp.execute_query(query, [
            data['user_id'],
            data['merchant_name'],
            data['merchant_standardized'],
            data['amount'],
            data['frequency'],
            data.get('frequency_days'),
            data['start_date'],
            data['last_charge_date'],
            data['next_expected_date'],
            data.get('status', 'active'),
            data.get('category'),
            data.get('confidence'),
            data.get('detection_method'),
            data.get('occurrence_count', 1)
        ])
        
        return result['rows'][0]['id']
    
    async def update_subscription(self, subscription_id: str, updates: Dict):
        """Update existing subscription"""
        update_fields = []
        params = []
        param_idx = 1
        
        for field, value in updates.items():
            update_fields.append(f"{field} = ${param_idx}")
            params.append(value)
            param_idx += 1
        
        params.append(subscription_id)
        
        query = f"""
            UPDATE subscriptions
            SET {', '.join(update_fields)},
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ${param_idx}
        """
        
        await self.mcp.execute_query(query, params)
    
    # ========================================
    # SPENDING PATTERNS
    # ========================================
    
    async def get_spending_patterns(
        self,
        user_id: str,
        category: Optional[str] = None,
        months: int = 3
    ) -> List[Dict]:
        """Get historical spending patterns"""
        query = """
            SELECT * FROM spending_patterns
            WHERE user_id = $1
              AND period_start >= CURRENT_DATE - INTERVAL '%s months'
        """ % months
        
        params = [user_id]
        
        if category:
            query += " AND category = $2"
            params.append(category)
        
        query += " ORDER BY period_start DESC"
        
        result = await self.mcp.execute_query(query, params)
        return result.get('rows', [])
    
    # ========================================
    # BUDGET ANALYSIS
    # ========================================
    
    async def insert_budget_analysis(self, data: Dict) -> str:
        """Insert budget analysis results"""
        query = """
            INSERT INTO budget_analysis (
                user_id, category, year, month, current_spend,
                baseline, warning_threshold, critical_threshold,
                overspending_threshold, status, utilization_percent,
                alert_message, alert_priority, recommended_action
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            ON CONFLICT (user_id, category, year, month)
            DO UPDATE SET
                current_spend = EXCLUDED.current_spend,
                status = EXCLUDED.status,
                utilization_percent = EXCLUDED.utilization_percent,
                alert_message = EXCLUDED.alert_message,
                created_at = CURRENT_TIMESTAMP
            RETURNING id
        """
        
        result = await self.mcp.execute_query(query, [
            data['user_id'],
            data['category'],
            data['year'],
            data['month'],
            data['current_spend'],
            data['baseline'],
            data.get('warning_threshold'),
            data.get('critical_threshold'),
            data.get('overspending_threshold'),
            data['status'],
            data.get('utilization_percent'),
            data.get('alert_message'),
            data.get('alert_priority'),
            data.get('recommended_action')
        ])
        
        return result['rows'][0]['id']