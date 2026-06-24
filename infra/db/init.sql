-- ============================================================
--  Quantum Trade AI — schéma initial de base de données
--  PostgreSQL + TimescaleDB. Exécuté au premier démarrage.
--  Multi-tenant : isolation stricte par tenant_id.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------- Tenants (organisations / comptes) ----------
CREATE TABLE tenants (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT NOT NULL,
    plan        TEXT NOT NULL DEFAULT 'free',   -- free | starter | pro | elite | enterprise
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Utilisateurs ----------
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email           TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    full_name       TEXT,
    mfa_enabled     BOOLEAN NOT NULL DEFAULT false,
    risk_profile    TEXT DEFAULT 'moderate',     -- conservative | moderate | aggressive
    capital         DOUBLE PRECISION NOT NULL DEFAULT 10000,
    watchlist       TEXT NOT NULL DEFAULT '[]',  -- JSON array de symboles
    onboarded       BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_tenant ON users(tenant_id);

-- ---------- Données de marché OHLCV (série temporelle) ----------
CREATE TABLE ohlcv (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT NOT NULL,                   -- ex. BTC/USDT
    timeframe   TEXT NOT NULL,                   -- 1m,5m,15m,1h,4h,1d
    open        DOUBLE PRECISION NOT NULL,
    high        DOUBLE PRECISION NOT NULL,
    low         DOUBLE PRECISION NOT NULL,
    close       DOUBLE PRECISION NOT NULL,
    volume      DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (symbol, timeframe, time)
);
SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);
CREATE INDEX idx_ohlcv_symbol_tf ON ohlcv(symbol, timeframe, time DESC);

-- ---------- News / sentiment (série temporelle) ----------
CREATE TABLE news (
    id          UUID DEFAULT uuid_generate_v4(),
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT,
    source      TEXT,
    headline    TEXT NOT NULL,
    url         TEXT,
    sentiment   DOUBLE PRECISION,                -- -1 (baissier) .. +1 (haussier)
    PRIMARY KEY (id, time)
);
SELECT create_hypertable('news', 'time', if_not_exists => TRUE);
CREATE INDEX idx_news_symbol ON news(symbol, time DESC);

-- ---------- Signaux générés (Signal Card) ----------
CREATE TABLE signals (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    symbol          TEXT NOT NULL,
    direction       TEXT NOT NULL,               -- BUY | SELL | HOLD
    entry           DOUBLE PRECISION NOT NULL,
    stop_loss       DOUBLE PRECISION NOT NULL,
    take_profit_1   DOUBLE PRECISION,
    take_profit_2   DOUBLE PRECISION,
    take_profit_3   DOUBLE PRECISION,
    risk_reward     DOUBLE PRECISION,
    confidence      INTEGER CHECK (confidence BETWEEN 0 AND 100),
    timeframe       TEXT,
    rationale       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_signals_symbol ON signals(symbol, created_at DESC);
CREATE INDEX idx_signals_tenant ON signals(tenant_id, created_at DESC);

-- ---------- Journal de trades (Phase 3) ----------
CREATE TABLE trades (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    signal_id       UUID REFERENCES signals(id),
    symbol          TEXT NOT NULL,
    direction       TEXT NOT NULL,
    entry_price     DOUBLE PRECISION,
    exit_price      DOUBLE PRECISION,
    quantity        DOUBLE PRECISION,
    pnl             DOUBLE PRECISION,
    status          TEXT DEFAULT 'open',         -- open | closed | cancelled
    ai_review       TEXT,
    opened_at       TIMESTAMPTZ DEFAULT now(),
    closed_at       TIMESTAMPTZ
);
CREATE INDEX idx_trades_user ON trades(user_id, opened_at DESC);
