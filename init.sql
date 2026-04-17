-- Create Market Ticks Table (Raw Data)
CREATE TABLE IF NOT EXISTS default.market_ticks (
    symbol String,
    price Float64 CODEC(ZSTD(1)),
    timestamp DateTime64(3, 'UTC') CODEC(DoubleDelta, ZSTD(1)),
    source String
) ENGINE = MergeTree()
ORDER BY (symbol, timestamp)
PARTITION BY toYYYYMMDD(timestamp);

-- Create Drift Metrics Table (Analytical Brain)
CREATE TABLE IF NOT EXISTS default.drift_metrics (
    symbol String,
    ks_p_value Float64,
    psi_value Float64,
    z_score Float64,
    timestamp DateTime64(3, 'UTC')
) ENGINE = MergeTree()
ORDER BY (symbol, timestamp);