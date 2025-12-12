-- Smart Expense Analyzer - Database Schema
-- This script runs when the PostgreSQL container starts for the first time

-- ==========================================================================
-- USERS TABLE
-- ==========================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    monthly_income NUMERIC(12, 2) DEFAULT 0,
    life_stage VARCHAR(50) DEFAULT 'adult',
    dependents INTEGER DEFAULT 0,
    location VARCHAR(100),
    budget_alert_threshold NUMERIC(5, 2) DEFAULT 80.00,
    notification_preferences JSONB DEFAULT '{"email": true, "push": false}'::JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================================
-- ACCOUNTS TABLE (Bank/Card accounts from Plaid)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS accounts (
    account_id VARCHAR(100) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plaid_item_id VARCHAR(100),
    name VARCHAR(255),
    official_name VARCHAR(255),
    type VARCHAR(50),
    subtype VARCHAR(50),
    mask VARCHAR(10),
    current_balance NUMERIC(12, 2),
    available_balance NUMERIC(12, 2),
    iso_currency_code VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================================================
-- TRANSACTIONS TABLE (Raw transactions from Plaid/PDF)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(100) PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    account_id VARCHAR(100) REFERENCES accounts(account_id),
    amount NUMERIC(12, 2) NOT NULL,
    date DATE NOT NULL,
    name VARCHAR(255),
    merchant_name VARCHAR(255),
    category VARCHAR(100),
    personal_finance_category VARCHAR(100),
    payment_channel VARCHAR(50),
    transaction_type VARCHAR(50),
    pending BOOLEAN DEFAULT FALSE,
    source VARCHAR(50) DEFAULT 'plaid',
    processing_status VARCHAR(50) DEFAULT 'unprocessed',
    last_processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_user_date ON transactions(user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(processing_status);

-- ==========================================================================
-- PROCESSED TRANSACTIONS (AI-enhanced data)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS processed_transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100) UNIQUE REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category_ai VARCHAR(100),
    merchant_standardized VARCHAR(255),
    is_subscription BOOLEAN DEFAULT FALSE,
    subscription_confidence NUMERIC(4, 2),
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score NUMERIC(4, 2),
    anomaly_reason TEXT,
    is_bill BOOLEAN DEFAULT FALSE,
    bill_cycle_day INTEGER,
    tags TEXT[],
    notes TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_processed_user ON processed_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_processed_subscription ON processed_transactions(is_subscription) WHERE is_subscription = TRUE;
CREATE INDEX IF NOT EXISTS idx_processed_anomaly ON processed_transactions(is_anomaly) WHERE is_anomaly = TRUE;

-- ==========================================================================
-- SUBSCRIPTIONS (Detected recurring payments)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    merchant_name VARCHAR(255),
    merchant_standardized VARCHAR(255),
    amount NUMERIC(12, 2),
    frequency VARCHAR(50) DEFAULT 'monthly',
    start_date DATE,
    last_charge_date DATE,
    next_expected_date DATE,
    category VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    usage_score NUMERIC(3, 2),
    occurrence_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, merchant_standardized, frequency)
);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);

-- ==========================================================================
-- SPENDING PATTERNS (Monthly aggregates by category)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS spending_patterns (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100),
    period_type VARCHAR(20) DEFAULT 'monthly',
    year INTEGER,
    month INTEGER,
    period_start DATE,
    period_end DATE,
    total_amount NUMERIC(12, 2),
    transaction_count INTEGER,
    avg_transaction_amount NUMERIC(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, category, period_type, year, month)
);

CREATE INDEX IF NOT EXISTS idx_spending_user_cat ON spending_patterns(user_id, category);

-- ==========================================================================
-- BUDGET ANALYSIS (Agent 2 analysis results)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS budget_analysis (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100),
    year INTEGER,
    month INTEGER,
    current_spend NUMERIC(12, 2),
    baseline NUMERIC(12, 2),
    status VARCHAR(50),
    utilization_percent NUMERIC(6, 2),
    alert_message TEXT,
    alert_priority VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, category, year, month)
);

-- ==========================================================================
-- RECOMMENDATIONS (Agent 2 generated recommendations)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tool_name VARCHAR(100),
    recommendation_type VARCHAR(100),
    title VARCHAR(255),
    description TEXT,
    potential_savings NUMERIC(12, 2),
    annual_savings NUMERIC(12, 2),
    priority INTEGER DEFAULT 3,
    urgency VARCHAR(20) DEFAULT 'medium',
    related_category VARCHAR(100),
    related_merchant VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    user_action VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendations_user ON recommendations(user_id);

-- ==========================================================================
-- TREND PREDICTIONS (Agent 2 spending forecasts)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS trend_predictions (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category VARCHAR(100),
    target_year INTEGER,
    target_month INTEGER,
    predicted_amount NUMERIC(12, 2),
    confidence_score NUMERIC(4, 2),
    based_on_months INTEGER,
    historical_median NUMERIC(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, category, target_year, target_month)
);

-- ==========================================================================
-- CONVERSATION HISTORY (Agent 3 chat logs)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID,
    role VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    intent VARCHAR(100),
    tools_called TEXT[],
    tool_results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversation_user_session ON conversation_history(user_id, session_id);

-- ==========================================================================
-- UPLOAD HISTORY (PDF statement uploads)
-- ==========================================================================
CREATE TABLE IF NOT EXISTS upload_history (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    file_hash VARCHAR(64),
    bank_type VARCHAR(100),
    account_type VARCHAR(50),
    transactions_imported INTEGER DEFAULT 0,
    upload_status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, file_hash)
);

-- ==========================================================================
-- INSERT DEFAULT TEST USER
-- ==========================================================================
INSERT INTO users (id, username, email, monthly_income, life_stage)
VALUES (
    'dfea6d34-dc5d-407e-b39a-329ad905cc57',
    'testuser',
    'test@example.com',
    5000.00,
    'professional'
) ON CONFLICT (id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO postgres;

