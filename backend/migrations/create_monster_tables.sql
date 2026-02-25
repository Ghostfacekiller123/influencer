-- Influencer watchlist table
CREATE TABLE IF NOT EXISTS influencer_watchlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    handle TEXT NOT NULL,
    platform TEXT NOT NULL DEFAULT 'instagram',
    status TEXT DEFAULT 'active',
    last_checked_at TIMESTAMP,
    total_products_found INT DEFAULT 0,
    added_by TEXT DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(handle, platform)
);

-- Monster configuration table
CREATE TABLE IF NOT EXISTS monster_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    is_active BOOLEAN DEFAULT false,
    monitoring_interval INT DEFAULT 21600,
    auto_discovery_enabled BOOLEAN DEFAULT false,
    max_influencers_to_monitor INT DEFAULT 100,
    platforms_enabled TEXT[] DEFAULT ARRAY['instagram'],
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default config
INSERT INTO monster_config (is_active, monitoring_interval)
SELECT false, 21600
WHERE NOT EXISTS (SELECT 1 FROM monster_config LIMIT 1);

-- Processing logs table
CREATE TABLE IF NOT EXISTS processing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    influencer_handle TEXT,
    platform TEXT,
    action TEXT,
    status TEXT,
    products_found INT DEFAULT 0,
    products_saved INT DEFAULT 0,
    error_message TEXT,
    execution_time_seconds FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_watchlist_status ON influencer_watchlist(status);
CREATE INDEX IF NOT EXISTS idx_watchlist_platform ON influencer_watchlist(platform);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON processing_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_influencer ON processing_logs(influencer_handle);
