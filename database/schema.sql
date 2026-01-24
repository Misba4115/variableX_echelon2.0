-- ===========================================
-- AUTONOMOUS SILVER PREDICTION AGENT
-- Supabase Database Schema
-- ===========================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================
-- TABLE: targets
-- Purpose: Store monitoring URLs/APIs for data collection
-- ===========================================
CREATE TABLE IF NOT EXISTS targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('api', 'scrape', 'rss')),
    url TEXT NOT NULL,
    category VARCHAR(100) DEFAULT 'general',
    scrape_selector TEXT,  -- CSS selector for scraping
    api_endpoint TEXT,     -- Specific API endpoint
    headers JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    poll_interval_seconds INTEGER DEFAULT 300,
    last_scraped_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for active targets lookup
CREATE INDEX idx_targets_active ON targets(is_active) WHERE is_active = true;
CREATE INDEX idx_targets_category ON targets(category);

-- ===========================================
-- TABLE: market_data
-- Purpose: Store price data, news, and market information
-- ===========================================
CREATE TABLE IF NOT EXISTS market_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_id UUID REFERENCES targets(id) ON DELETE SET NULL,
    data_type VARCHAR(50) NOT NULL CHECK (data_type IN ('price', 'news', 'indicator', 'sentiment')),
    symbol VARCHAR(20),
    
    -- Price data fields
    price DECIMAL(18, 6),
    currency VARCHAR(10) DEFAULT 'USD',
    price_change DECIMAL(18, 6),
    price_change_percent DECIMAL(10, 4),
    high_24h DECIMAL(18, 6),
    low_24h DECIMAL(18, 6),
    volume DECIMAL(24, 4),
    
    -- News/Content fields
    title TEXT,
    content TEXT,
    source_url TEXT,
    author VARCHAR(255),
    
    -- Sentiment fields
    sentiment_score DECIMAL(5, 4),  -- -1.0 to 1.0
    sentiment_label VARCHAR(20),    -- positive, negative, neutral
    
    -- Metadata
    raw_data JSONB,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    data_timestamp TIMESTAMPTZ,  -- Original timestamp from source
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX idx_market_data_type ON market_data(data_type);
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_collected ON market_data(collected_at DESC);
CREATE INDEX idx_market_data_target ON market_data(target_id);

-- ===========================================
-- TABLE: agent_logs
-- Purpose: Store autonomous reasoning and decision logs
-- ===========================================
CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL,
    log_type VARCHAR(50) NOT NULL CHECK (log_type IN ('reasoning', 'decision', 'action', 'error', 'prediction')),
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    
    -- Agent reasoning fields
    agent_state VARCHAR(100),
    input_summary TEXT,
    reasoning_chain TEXT,  -- The agent's thought process
    decision TEXT,
    action_taken TEXT,
    
    -- Prediction fields
    prediction_type VARCHAR(50),  -- price_direction, price_target, etc.
    prediction_value JSONB,
    confidence_score DECIMAL(5, 4),  -- 0.0 to 1.0
    prediction_horizon VARCHAR(50),  -- 1h, 24h, 7d, etc.
    
    -- Validation fields
    was_correct BOOLEAN,
    actual_outcome JSONB,
    validated_at TIMESTAMPTZ,
    
    -- Metadata
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    model_used VARCHAR(100),
    raw_response JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for agent log analysis
CREATE INDEX idx_agent_logs_session ON agent_logs(session_id);
CREATE INDEX idx_agent_logs_type ON agent_logs(log_type);
CREATE INDEX idx_agent_logs_created ON agent_logs(created_at DESC);
CREATE INDEX idx_agent_logs_severity ON agent_logs(severity);

-- ===========================================
-- FUNCTION: Update updated_at timestamp
-- ===========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to targets table
CREATE TRIGGER update_targets_updated_at
    BEFORE UPDATE ON targets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- ROW LEVEL SECURITY (RLS) Policies
-- Uncomment and modify based on your auth needs
-- ===========================================

-- ALTER TABLE targets ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE market_data ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_logs ENABLE ROW LEVEL SECURITY;

-- Example policy for authenticated users
-- CREATE POLICY "Allow authenticated read access"
--     ON market_data FOR SELECT
--     TO authenticated
--     USING (true);
