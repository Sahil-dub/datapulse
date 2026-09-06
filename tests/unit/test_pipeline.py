from pathlib import Path

import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.pipeline import materialize_all_sources
from datapulse.data_generation.schema_drift_config import (
    CUSTOMER_EMAIL_RENAME,
    ORDER_REMOVE_SHIPPING_AMOUNT,
    PRODUCT_ADD_BRAND,
    SchemaDriftConfig,
)


def test_materialize_all_sources_creates_expected_files(tmp_path: Path) -> None:
    config = DataGenerationConfig(
        output_dir=tmp_path,
        customers_count=20,
        products_count=5,
        orders_count=30,
        payments_count=35,
        subscriptions_count=10,
        support_tickets_count=15,
        web_events_count=50,
    )

    output_paths = materialize_all_sources(config)

    expected_sources = {
        "customers",
        "products",
        "orders",
        "payments",
        "subscriptions",
        "support_tickets",
        "web_events",
    }

    assert set(output_paths) == expected_sources

    for source_name, output_path in output_paths.items():
        assert output_path == (tmp_path / source_name / f"{source_name}.csv")
        assert output_path.exists()
        assert output_path.stat().st_size > 0


def test_materialize_all_sources_preserves_expected_columns(
    tmp_path: Path,
) -> None:
    config = DataGenerationConfig(
        output_dir=tmp_path,
        customers_count=20,
        products_count=5,
        orders_count=30,
        payments_count=35,
        subscriptions_count=10,
        support_tickets_count=15,
        web_events_count=50,
    )

    output_paths = materialize_all_sources(config)

    expected_columns = {
        "customers": {
            "customer_id",
            "first_name",
            "last_name",
            "email",
            "country",
            "signup_date",
            "customer_status",
            "acquisition_channel",
        },
        "products": {
            "product_id",
            "product_name",
            "category",
            "unit_price",
            "product_status",
            "created_date",
        },
        "orders": {
            "order_id",
            "customer_id",
            "product_id",
            "order_date",
            "quantity",
            "unit_price",
            "discount_amount",
            "shipping_amount",
            "order_total",
            "order_status",
            "sales_channel",
        },
        "payments": {
            "payment_id",
            "order_id",
            "payment_date",
            "payment_method",
            "payment_amount",
            "payment_status",
            "transaction_reference",
            "currency",
            "source_updated_at",
        },
        "subscriptions": {
            "subscription_id",
            "customer_id",
            "plan_type",
            "subscription_status",
            "billing_frequency",
            "start_date",
            "end_date",
            "monthly_fee",
            "auto_renew",
            "source_updated_at",
        },
        "support_tickets": {
            "ticket_id",
            "customer_id",
            "ticket_created_at",
            "ticket_updated_at",
            "ticket_category",
            "priority",
            "ticket_status",
            "resolution_channel",
            "assigned_team",
            "resolution_time_hours",
            "customer_satisfaction_score",
        },
        "web_events": {
            "event_id",
            "event_timestamp",
            "source_received_at",
            "session_id",
            "customer_id",
            "event_type",
            "page_type",
            "device_type",
            "traffic_source",
            "product_id",
            "order_id",
            "revenue_amount",
        },
    }

    for source_name, columns in expected_columns.items():
        dataframe = pd.read_csv(output_paths[source_name])
        assert columns.issubset(dataframe.columns)
        assert not dataframe.empty


def test_materialize_all_sources_applies_customer_email_rename(
    tmp_path: Path,
) -> None:
    config = DataGenerationConfig(
        output_dir=tmp_path,
        customers_count=20,
        products_count=5,
        orders_count=30,
        payments_count=35,
        subscriptions_count=10,
        support_tickets_count=15,
        web_events_count=50,
    )
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(CUSTOMER_EMAIL_RENAME,),
    )

    output_paths = materialize_all_sources(config, drift_config)

    dataframe = pd.read_csv(output_paths["customers"])

    assert "email_address" in dataframe.columns
    assert "email" not in dataframe.columns


def test_materialize_all_sources_applies_product_brand_addition(
    tmp_path: Path,
) -> None:
    config = DataGenerationConfig(
        output_dir=tmp_path,
        customers_count=20,
        products_count=5,
        orders_count=30,
        payments_count=35,
        subscriptions_count=10,
        support_tickets_count=15,
        web_events_count=50,
    )
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(PRODUCT_ADD_BRAND,),
    )

    output_paths = materialize_all_sources(config, drift_config)

    dataframe = pd.read_csv(output_paths["products"])

    assert "brand" in dataframe.columns
    assert dataframe["brand"].eq("SYNTHETIC_BRAND").all()


def test_materialize_all_sources_applies_order_column_removal(
    tmp_path: Path,
) -> None:
    config = DataGenerationConfig(
        output_dir=tmp_path,
        customers_count=20,
        products_count=5,
        orders_count=30,
        payments_count=35,
        subscriptions_count=10,
        support_tickets_count=15,
        web_events_count=50,
    )
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(ORDER_REMOVE_SHIPPING_AMOUNT,),
    )

    output_paths = materialize_all_sources(config, drift_config)

    dataframe = pd.read_csv(output_paths["orders"])

    assert "shipping_amount" not in dataframe.columns
    assert "order_total" in dataframe.columns


def test_materialize_all_sources_can_apply_multiple_drift_scenarios(
    tmp_path: Path,
) -> None:
    config = DataGenerationConfig(
        output_dir=tmp_path,
        customers_count=20,
        products_count=5,
        orders_count=30,
        payments_count=35,
        subscriptions_count=10,
        support_tickets_count=15,
        web_events_count=50,
    )
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(
            CUSTOMER_EMAIL_RENAME,
            PRODUCT_ADD_BRAND,
            ORDER_REMOVE_SHIPPING_AMOUNT,
        ),
    )

    output_paths = materialize_all_sources(config, drift_config)

    customers = pd.read_csv(output_paths["customers"])
    products = pd.read_csv(output_paths["products"])
    orders = pd.read_csv(output_paths["orders"])

    assert "email_address" in customers.columns
    assert "email" not in customers.columns
    assert "brand" in products.columns
    assert "shipping_amount" not in orders.columns


def test_materialize_all_sources_leaves_unrelated_sources_unchanged(
    tmp_path: Path,
) -> None:
    config = DataGenerationConfig(
        output_dir=tmp_path,
        customers_count=20,
        products_count=5,
        orders_count=30,
        payments_count=35,
        subscriptions_count=10,
        support_tickets_count=15,
        web_events_count=50,
    )
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(CUSTOMER_EMAIL_RENAME,),
    )

    output_paths = materialize_all_sources(config, drift_config)

    products = pd.read_csv(output_paths["products"])
    orders = pd.read_csv(output_paths["orders"])

    assert "brand" not in products.columns
    assert "shipping_amount" in orders.columns


def test_materialize_all_sources_keeps_canonical_schema_by_default(
    tmp_path: Path,
) -> None:
    config = DataGenerationConfig(
        output_dir=tmp_path,
        customers_count=20,
        products_count=5,
        orders_count=30,
        payments_count=35,
        subscriptions_count=10,
        support_tickets_count=15,
        web_events_count=50,
    )

    output_paths = materialize_all_sources(config)

    customers = pd.read_csv(output_paths["customers"])
    products = pd.read_csv(output_paths["products"])
    orders = pd.read_csv(output_paths["orders"])

    assert "email" in customers.columns
    assert "email_address" not in customers.columns
    assert "brand" not in products.columns
    assert "shipping_amount" in orders.columns
