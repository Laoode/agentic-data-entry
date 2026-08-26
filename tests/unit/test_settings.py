"""Settings validation tests."""

import pytest

from config.settings import Settings


def test_deepseek_vision_is_default_kie_model():
    """Use DeepSeek vision when no KIE model is configured."""
    settings = Settings(_env_file=None)

    assert settings.kie_model == "deepseek-v4-flash-vision-exp"


def test_production_rejects_development_database_url():
    settings = Settings(
        _env_file=None,
        STAGE="production",
        JWT_SECRET="production-test-secret-at-least-32-bytes",
    )

    with pytest.raises(ValueError, match="DATABASE_URL"):
        settings.validate_production_config()
