from datapulse.database import create_database_engine
from datapulse.settings import Settings


def test_settings_build_postgres_database_url() -> None:
    settings = Settings(
        postgres_host="db.example",
        postgres_port=5433,
        postgres_db="analytics",
        postgres_user="reader",
        postgres_password="secret",
    )

    assert settings.database_url == (
        "postgresql+psycopg://reader:secret@db.example:5433/analytics"
    )


def test_create_database_engine_uses_configured_url() -> None:
    settings = Settings(
        postgres_host="db.example",
        postgres_port=5432,
        postgres_db="datapulse",
        postgres_user="datapulse",
        postgres_password="secret",
    )

    engine = create_database_engine(settings)

    assert engine.url.render_as_string(hide_password=False) == (
        "postgresql+psycopg://datapulse:secret@db.example:5432/datapulse"
    )
    assert engine.pool._pre_ping is True
