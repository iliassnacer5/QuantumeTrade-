"""Configuration partagée des tests : désactive le rate limiting et isole l'état."""

import pytest

from app.core.config import get_settings
from app.repositories.store import reset_store


@pytest.fixture(autouse=True)
def _test_env():
    settings = get_settings()
    settings.rate_limit_enabled = False
    settings.use_in_memory_db = True
    reset_store()
    yield
