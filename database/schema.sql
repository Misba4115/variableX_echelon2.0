-- ===========================================
-- SILVER PREDICTION AGENT - FINAL SCHEMA
-- Generated from current Supabase tables
-- ===========================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================
-- TABLE: targets
-- Purpose: URLs/APIs to monitor
-- ===========================================
CREATE TABLE IF NOT EXISTS targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    category VARCHAR(100),
    scrape_selector TEXT,
    api_endpoint TEXT,
    headers JSONB,
    is_active BOOLEAN DEFAULT true,
    poll_interval_seconds INTEGER DEFAULT 300,
    last_scraped_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_targets_active ON targets(is_active);
CREATE INDEX idx_targets_category ON targets(category);


-- ===========================================
-- TABLE: price_data
-- Purpose: Silver price records
-- ===========================================
CREATE TABLE IF NOT EXISTS price_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_id UUID REFERENCES targets(id) ON DELETE SET NULL,
    price NUMERIC NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    price_change NUMERIC,
    price_change_percent NUMERIC,
    high_24h NUMERIC,
    low_24h NUMERIC,
    volume NUMERIC,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    source_timestamp TIMESTAMPTZ,
    raw_data JSONB
);

CREATE INDEX idx_price_data_fetched ON price_data(fetched_at DESC);


-- ===========================================
-- TABLE: news_data
-- Purpose: News articles about silver
-- ===========================================
CREATE TABLE IF NOT EXISTS news_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_id UUID REFERENCES targets(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    content TEXT,
    source_url TEXT,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    raw_data JSONB
);

CREATE INDEX idx_news_data_fetched ON news_data(fetched_at DESC);


-- ===========================================
-- TABLE: agent_logs
-- Purpose: Agent reasoning and predictions
-- ===========================================
CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    reasoning_chain TEXT,
    decision TEXT,
    prediction_value JSONB,
    confidence_score NUMERIC,
    raw_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_logs_session ON agent_logs(session_id);
CREATE INDEX idx_agent_logs_created ON agent_logs(created_at DESC);


-- ===========================================
-- Disable RLS for development
-- ===========================================
ALTER TABLE targets DISABLE ROW LEVEL SECURITY;
ALTER TABLE price_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE news_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE agent_logs DISABLE ROW LEVEL SECURITY;
