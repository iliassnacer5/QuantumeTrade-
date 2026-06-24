"""Configuration centralisée, chargée depuis les variables d'environnement."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de l'application (12-factor : tout vient de l'environnement)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Environnement
    environment: str = "dev"
    log_level: str = "INFO"

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
    litellm_default_model: str = "claude-sonnet-4-6"

    # Données marché / news
    binance_api_key: str = ""
    binance_api_secret: str = ""
    finnhub_api_key: str = ""
    newsapi_key: str = ""

    # Facturation
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_starter: str = ""

    # Alertes
    telegram_bot_token: str = ""
    resend_api_key: str = ""
    email_from: str = "alerts@quantumtrade.ai"

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
