-- Table données brutes (raw)
CREATE TABLE IF NOT EXISTS raw_stock_data (
    id          SERIAL PRIMARY KEY,
    ticker      VARCHAR(10)    NOT NULL,
    date        DATE           NOT NULL,
    open        NUMERIC(12, 4),
    high        NUMERIC(12, 4),
    low         NUMERIC(12, 4),
    close       NUMERIC(12, 4),
    volume      BIGINT,
    loaded_at   TIMESTAMP      DEFAULT NOW(),
    UNIQUE(ticker, date)
);

-- Table données transformées (KPIs)
CREATE TABLE IF NOT EXISTS transformed_stock_data (
    id              SERIAL PRIMARY KEY,
    ticker          VARCHAR(10)   NOT NULL,
    date            DATE          NOT NULL,
    close           NUMERIC(12, 4),
    daily_return    NUMERIC(8, 4),   -- rendement journalier (%)
    ma_7            NUMERIC(12, 4),  -- moyenne mobile 7 jours
    ma_30           NUMERIC(12, 4),  -- moyenne mobile 30 jours
    volatility_30   NUMERIC(8, 4),   -- volatilité 30 jours
    processed_at    TIMESTAMP     DEFAULT NOW(),
    UNIQUE(ticker, date)
);