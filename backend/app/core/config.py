"""Configuration centralisée, chargée depuis les variables d'environnement."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de l'application (12-factor : tout vient de l'environnement)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Environnement
    environment: str = "dev"
    log_level: str = "INFO"
    # Observabilité (Phase 5) — Sentry optionnel (no-op si vide).
    sentry_dsn: str = ""
    # Cache des complétions LLM (s) — réduction des coûts (Phase 5).
    llm_cache_ttl: int = 300
    # Automatisation : sélection quotidienne de trades (heure UTC du pré-calcul + digest).
    daily_digest_hour: int = 7
    daily_digest_enabled: bool = True

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:3000"

    # Persistance
    database_url: str = "postgresql+asyncpg://quantum:quantum_dev_pwd@postgres:5432/quantum"
    redis_url: str = "redis://redis:6379/0"
    kafka_bootstrap_servers: str = "redpanda:9092"

    # Persistance MVP : in-memory par défaut -> l'app tourne sans Postgres.
    # Passer à false pour utiliser la base SQL (DATABASE_URL).
    use_in_memory_db: bool = True

    # JWT
    jwt_algorithm: str = "HS256"

    # Sécurité
    rate_limit_enabled: bool = True

    # LLM
    anthropic_api_key: str = ""
    google_api_key: str = ""
    litellm_default_model: str = "gemini/gemini-2.5-pro"
    llm_enabled: bool = True
    # Modèles par rôle (overridables par env) — stratégie hybride Claude/Gemini.
    # NB : la série gemini-1.5 a été retirée de l'API v1beta ; on utilise la série 2.5 (GA).
    # Stratégie hybride : Gemini 2.5-flash (rapide/pas cher) pour les commentaires d'agents répétés
    # (fast/grounding) ; Claude pour la vision chartiste et le raisonnement (Sonnet 4.6) et l'arbitrage
    # maître (Opus 4.8). Le failover bascule automatiquement vers Gemini si la clé Anthropic est absente
    # (le fallback d'un modèle anthropic est llm_model_fast), donc tout reste fonctionnel sans clé Claude.
    llm_model_master: str = "anthropic/claude-opus-4-8"
    llm_model_reasoning: str = "anthropic/claude-sonnet-4-6"
    llm_model_fast: str = "gemini/gemini-2.5-flash"
    llm_model_vision: str = "anthropic/claude-sonnet-4-6"
    llm_model_grounding: str = "gemini/gemini-2.5-flash"
    
    # LLM Budget Guards
    llm_max_requests_per_minute: int = 15
    llm_max_tokens_per_minute: int = 30000
    llm_daily_budget_usd: float = 1.0

    # Données marché / news
    binance_api_key: str = ""
    binance_api_secret: str = ""
    finnhub_api_key: str = ""
    newsapi_key: str = ""
    newsdata_key: str = ""
    massive_news_key: str = ""
    # Multi-marchés (Phase 2)
    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""
    oanda_api_key: str = ""
    oanda_account_id: str = ""
    fred_api_key: str = ""

    # Facturation
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_starter: str = ""

    # Alertes
    telegram_bot_token: str = ""
    resend_api_key: str = ""
    email_from: str = "alerts@quantumtrade.ai"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def database_url_sync(self) -> str:
        """URL SQLAlchemy synchrone (les repositories du MVP sont synchrones).

        Convertit l'éventuel driver async (asyncpg) en driver sync (psycopg2).
        """
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg2://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Singleton mis en cache des settings."""
    return Settings()
