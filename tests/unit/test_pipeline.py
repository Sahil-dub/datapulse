import json
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


def _config(tmp_path: Path) -> DataGenerationConfig:
    return DataGenerationConfig(
        output_dir=tmp_path,
        customers_count=20,
        products_count=5,
        orders_count=30,
        payments_count=35,
        subscriptions_count=10,
        support_tickets_count=15,
        web_events_count=50,
    )


def test_materialize_all_sources_creates_expected_files(tmp_path: Path) -> None:
    output_paths = materialize_all_sources(_config(tmp_path))

    expected_sources = {
        "customers",
        "products",
        "orders",
        "payments",
        "subscriptions",
        "support_tickets",
        "web_events",
    }

    assert set(output_paths) == expected_sources | {"manifest"}
    assert output_paths["manifest"] == tmp_path / "manifest.json"
    assert output_paths["manifest"].is_file()

    for source_name in expected_sources:
        output_path = output_paths[source_name]

        assert output_path == (tmp_path / source_name / f"{source_name}.csv")
        assert output_path.is_file()


def test_materialize_all_sources_preserves_expected_columns(
    tmp_path: Path,
) -> None:
    output_paths = materialize_all_sources(_config(tmp_path))

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
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(CUSTOMER_EMAIL_RENAME,),
    )

    output_paths = materialize_all_sources(_config(tmp_path), drift_config)

    dataframe = pd.read_csv(output_paths["customers"])

    assert "email_address" in dataframe.columns
    assert "email" not in dataframe.columns


def test_materialize_all_sources_applies_product_brand_addition(
    tmp_path: Path,
) -> None:
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(PRODUCT_ADD_BRAND,),
    )

    output_paths = materialize_all_sources(_config(tmp_path), drift_config)

    dataframe = pd.read_csv(output_paths["products"])

    assert "brand" in dataframe.columns
    assert dataframe["brand"].eq("SYNTHETIC_BRAND").all()


def test_materialize_all_sources_applies_order_column_removal(
    tmp_path: Path,
) -> None:
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(ORDER_REMOVE_SHIPPING_AMOUNT,),
    )

    output_paths = materialize_all_sources(_config(tmp_path), drift_config)

    dataframe = pd.read_csv(output_paths["orders"])

    assert "shipping_amount" not in dataframe.columns
    assert "order_total" in dataframe.columns


def test_materialize_all_sources_can_apply_multiple_drift_scenarios(
    tmp_path: Path,
) -> None:
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(
            CUSTOMER_EMAIL_RENAME,
            PRODUCT_ADD_BRAND,
            ORDER_REMOVE_SHIPPING_AMOUNT,
        ),
    )

    output_paths = materialize_all_sources(_config(tmp_path), drift_config)

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
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(CUSTOMER_EMAIL_RENAME,),
    )

    output_paths = materialize_all_sources(_config(tmp_path), drift_config)

    products = pd.read_csv(output_paths["products"])
    orders = pd.read_csv(output_paths["orders"])

    assert "brand" not in products.columns
    assert "shipping_amount" in orders.columns


def test_materialize_all_sources_keeps_canonical_schema_by_default(
    tmp_path: Path,
) -> None:
    output_paths = materialize_all_sources(_config(tmp_path))

    customers = pd.read_csv(output_paths["customers"])
    products = pd.read_csv(output_paths["products"])
    orders = pd.read_csv(output_paths["orders"])

    assert "email" in customers.columns
    assert "email_address" not in customers.columns
    assert "brand" not in products.columns
    assert "shipping_amount" in orders.columns


def test_materialize_all_sources_creates_manifest(
    tmp_path: Path,
) -> None:
    output_paths = materialize_all_sources(_config(tmp_path))

    manifest_path = output_paths["manifest"]

    assert manifest_path == tmp_path / "manifest.json"
    assert manifest_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert "generated_at" in manifest
    assert manifest["schema_drift_scenarios"] == []
    assert len(manifest["sources"]) == 7

    source_names = {entry["source_name"] for entry in manifest["sources"]}

    assert source_names == {
        "customers",
        "products",
        "orders",
        "payments",
        "subscriptions",
        "support_tickets",
        "web_events",
    }


def test_materialize_all_sources_records_schema_drift(
    tmp_path: Path,
) -> None:
    drift_config = SchemaDriftConfig(
        enabled=True,
        scenarios=(
            CUSTOMER_EMAIL_RENAME,
            PRODUCT_ADD_BRAND,
        ),
    )

    output_paths = materialize_all_sources(
        _config(tmp_path),
        schema_drift_config=drift_config,
    )

    manifest = json.loads(output_paths["manifest"].read_text(encoding="utf-8"))

    assert manifest["schema_drift_scenarios"] == [
        CUSTOMER_EMAIL_RENAME,
        PRODUCT_ADD_BRAND,
    ]

    source_entries = {entry["source_name"]: entry for entry in manifest["sources"]}

    assert "email_address" in source_entries["customers"]["columns"]
    assert "brand" in source_entries["products"]["columns"]


def test_materialize_all_sources_validates_manifest_after_writing(
    tmp_path: Path, monkeypatch
) -> None:
    import datapulse.data_generation.pipeline as pipeline

    calls: list[Path] = []

    def record_validation(manifest_path: Path) -> None:
        calls.append(manifest_path)

    monkeypatch.setattr(pipeline, "validate_source_manifest", record_validation)

    output_paths = materialize_all_sources(_config(tmp_path))

    assert calls == [tmp_path / "manifest.json"]
    assert output_paths["manifest"] == tmp_path / "manifest.json"


def test_materialize_all_sources_fails_if_manifest_validation_fails(
    tmp_path: Path, monkeypatch
) -> None:
    import datapulse.data_generation.pipeline as pipeline

    def fail_validation(_manifest_path: Path) -> None:
        raise ValueError("Manifest validation failed: simulated failure.")

    monkeypatch.setattr(pipeline, "validate_source_manifest", fail_validation)

    try:
        materialize_all_sources(_config(tmp_path))
    except ValueError as exc:
        assert str(exc) == "Manifest validation failed: simulated failure."
    else:
        raise AssertionError("Expected manifest validation failure.")
