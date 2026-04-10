-- ATO Shield v2 - Database Schema Initialization
-- This script runs on first PostgreSQL startup

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Banks table
CREATE TABLE IF NOT EXISTS banks (
    bank_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    webhook_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysts table
CREATE TABLE IF NOT EXISTS analysts (
    analyst_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bank_id UUID REFERENCES banks(bank_id),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(255) PRIMARY KEY,
    bank_id UUID REFERENCES banks(bank_id),
    payload JSONB NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cases table
CREATE TABLE IF NOT EXISTS cases (
    case_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id VARCHAR(255) REFERENCES transactions(transaction_id),
    bank_id UUID REFERENCES banks(bank_id),
    risk_score FLOAT NOT NULL,
    risk_level VARCHAR(10) NOT NULL,  -- HIGH / MEDIUM / LOW
    fraud_type VARCHAR(10),  -- ATO / VEL / AMT / NGT / ANO
    status VARCHAR(20) DEFAULT 'OPEN',  -- OPEN / RESOLVED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SHAP reasons table
CREATE TABLE IF NOT EXISTS shap_reasons (
    reason_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES cases(case_id),
    reason_text VARCHAR(500) NOT NULL,
    display_order INTEGER NOT NULL
);

-- Decisions table
CREATE TABLE IF NOT EXISTS decisions (
    decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES cases(case_id),
    analyst_id UUID REFERENCES analysts(analyst_id),
    action VARCHAR(50) NOT NULL,  -- BLOCK / FREEZE / ESCALATE / CLEAR
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_cases_bank_id ON cases(bank_id);
CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_risk_level ON cases(risk_level);
CREATE INDEX idx_transactions_bank_id ON transactions(bank_id);
CREATE INDEX idx_analysts_bank_id ON analysts(bank_id);

-- Insert demo bank for development
INSERT INTO banks (bank_id, name, api_key, webhook_url) 
VALUES ('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 
        'HDFC Bank Demo', 
        'ask_live_demo_key_12345', 
        'https://webhook.site/your-unique-id')
ON CONFLICT (bank_id) DO NOTHING;

-- Insert demo analyst for development
INSERT INTO analysts (bank_id, name, email, password_hash)
VALUES ('a1b2c3d4-e5f6-7890-abcd-ef1234567890',
        'Demo Analyst',
        'analyst@atoshield.demo',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYILp92S.0i')
ON CONFLICT (email) DO NOTHING;
