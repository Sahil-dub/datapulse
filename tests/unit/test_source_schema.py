import pytest

from datapulse.source_schema import get_source_columns


def test_get_source_columns_returns_customer_schema() -> None:
    assert get_source_columns("customers") == (
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "country",
        "signup_date",
        "customer_status",
        "acquisition_channel",
    )


def test_get_source_columns_returns_all_supported_sources() -> None:
    expected_sources = {
        "customers",
        "products",
        "orders",
        "payments",
        "subscriptions",
        "support_tickets",
        "web_events",
    }

    from datapulse.source_schema import SOURCE_COLUMNS

    assert set(SOURCE_COLUMNS) == expected_sources


def test_get_source_columns_rejects_unknown_source() -> None:
    with pytest.raises(ValueError, match="Unknown source"):
        get_source_columns("unknown_source")
