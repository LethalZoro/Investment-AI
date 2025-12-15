-- Database Schema for PSX Investment Co-Pilot
-- Generated for PostgreSQL (Supabase)

CREATE TABLE IF NOT EXISTS user_settings (
    id SERIAL PRIMARY KEY,
    cash_balance FLOAT DEFAULT 0.0,
    monthly_investment FLOAT DEFAULT 0.0,
    daily_trade_budget FLOAT DEFAULT 5000.0,
    ai_cash_balance FLOAT DEFAULT 10000.0,
    initial_ai_capital FLOAT DEFAULT 10000.0,
    autonomous_mode BOOLEAN DEFAULT FALSE,
    rollover_percent FLOAT DEFAULT 0.30,
    risk_profile VARCHAR DEFAULT 'MEDIUM',
    last_run_date TIMESTAMP,
    unused_budget_carryover FLOAT DEFAULT 0.0,
    polling_interval INTEGER DEFAULT 5,
    trading_start_time VARCHAR DEFAULT '09:30',
    trading_end_time VARCHAR DEFAULT '15:30'
);

CREATE TABLE IF NOT EXISTS portfolio_items (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR,
    quantity INTEGER,
    avg_cost FLOAT,
    strategy_tag VARCHAR DEFAULT 'UNASSIGNED',
    target_allocation FLOAT,
    entry_notes VARCHAR,
    risk_tolerance VARCHAR DEFAULT 'MEDIUM'
);

CREATE INDEX IF NOT EXISTS ix_portfolio_items_symbol ON portfolio_items (symbol);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR,
    action VARCHAR,
    quantity INTEGER,
    price FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes VARCHAR
);

CREATE INDEX IF NOT EXISTS ix_transactions_symbol ON transactions (symbol);

CREATE TABLE IF NOT EXISTS daily_plans (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    plan_json VARCHAR,
    executed BOOLEAN DEFAULT FALSE,
    budget_allocated FLOAT DEFAULT 0.0,
    budget_used FLOAT DEFAULT 0.0,
    rationale VARCHAR
);

CREATE TABLE IF NOT EXISTS ai_alerts (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR,
    signal VARCHAR,
    reason VARCHAR,
    url VARCHAR,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_ai_alerts_symbol ON ai_alerts (symbol);

CREATE TABLE IF NOT EXISTS portfolio_history (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_value FLOAT,
    cash_balance FLOAT,
    holdings_value FLOAT
);

-- AI Autonomous Models

CREATE TABLE IF NOT EXISTS ai_portfolio_items (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR,
    quantity INTEGER,
    avg_cost FLOAT,
    current_price FLOAT DEFAULT 0.0,
    total_cost FLOAT,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_reasoning VARCHAR,
    last_decision VARCHAR DEFAULT 'HOLD',
    last_reason VARCHAR,
    last_confidence VARCHAR,
    last_analyzed TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_ai_portfolio_items_symbol ON ai_portfolio_items (symbol);

CREATE TABLE IF NOT EXISTS ai_recommendations (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR,
    action VARCHAR,
    quantity INTEGER,
    price FLOAT,
    reason VARCHAR,
    status VARCHAR DEFAULT 'PENDING',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_ai_recommendations_symbol ON ai_recommendations (symbol);

CREATE TABLE IF NOT EXISTS ai_trade_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR,
    action VARCHAR,
    quantity INTEGER,
    price FLOAT,
    pnl FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR
);

CREATE INDEX IF NOT EXISTS ix_ai_trade_history_symbol ON ai_trade_history (symbol);

CREATE TABLE IF NOT EXISTS ai_notifications (
    id SERIAL PRIMARY KEY,
    title VARCHAR,
    message VARCHAR,
    type VARCHAR,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
);
