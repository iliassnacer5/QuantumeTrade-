-- ============================================================
--  Quantum Trade AI — initialisation TimescaleDB
--  Exécuté au premier démarrage du conteneur Postgres.
--
--  Répartition des responsabilités :
--   - Ce fichier ne gère QUE les objets spécifiques TimescaleDB :
--     extensions + hypertables de séries temporelles (ohlcv, news).
--   - Les tables relationnelles de l'application (tenants, users, signals,
--     trades) sont créées et maintenues par l'ORM SQLAlchemy (create_all /
--     migrations Alembic), pour garantir une cohérence stricte des types
--     entre le code et la base.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------- Données de marché OHLCV (série temporelle) ----------
CREATE TABLE IF NOT EXISTS ohlcv (
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
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_tf ON ohlcv(symbol, timeframe, time DESC);

-- ---------- News / sentiment (série temporelle) ----------
CREATE TABLE IF NOT EXISTS news (
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
CREATE INDEX IF NOT EXISTS idx_news_symbol ON news(symbol, time DESC);

-- Note : les tables tenants / users / signals / trades sont créées par le backend
-- (SQLAlchemy) au démarrage. Voir backend/app/models/db.py.
