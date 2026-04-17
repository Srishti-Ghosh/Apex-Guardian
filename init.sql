-- init.sql
CREATE TABLE IF NOT EXISTS default.market_ticks (
    symbol String,
    price Float64 CODEC(ZSTD(1)),
    timestamp DateTime64(3, 'UTC') CODEC(DoubleDelta, ZSTD(1)),
    source String
) ENGINE = MergeTree()
ORDER BY (symbol, timestamp)
PARTITION BY toYYYYMMDD(timestamp);