import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.sources.customers import generate_customers
from datapulse.data_generation.sources.orders import generate_orders
from datapulse.data_generation.sources.products import generate_products
from datapulse.data_generation.sources.web_events import (
    EVENT_TYPES,
    expected_web_event_columns,
    generate_web_events,
)


def _build_dependencies() -> tuple[
    DataGenerationConfig,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    config = DataGenerationConfig(
        customers_count=100,
        products_count=20,
        orders_count=200,
        payments_count=200,
        subscriptions_count=100,
        support_tickets_count=100,
        web_events_count=500,
    )

    customers = generate_customers(config)
    products = generate_products(config)
    orders = generate_orders(config, customers, products)

    return config, customers, products, orders


def test_expected_web_event_columns() -> None:
    expected = [
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
    ]

    assert expected_web_event_columns() == expected


def test_web_event_generator_has_expected_volume() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    assert len(events) == config.web_events_count


def test_web_event_generator_has_expected_columns() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    assert list(events.columns) == expected_web_event_columns()


def test_web_event_generator_is_reproducible() -> None:
    config, customers, products, orders = _build_dependencies()

    first = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    second = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    pd.testing.assert_frame_equal(first, second)


def test_web_event_generator_changes_with_seed() -> None:
    config, customers, products, orders = _build_dependencies()

    first = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    different_config = DataGenerationConfig(
        seed=999,
        customers_count=100,
        products_count=20,
        orders_count=200,
        payments_count=200,
        subscriptions_count=100,
        support_tickets_count=100,
        web_events_count=500,
    )

    different = generate_web_events(
        different_config,
        customers,
        products,
        orders,
    )

    assert not first.equals(different)


def test_web_events_contain_duplicate_ids() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    duplicate_count = events["event_id"].duplicated().sum()

    assert duplicate_count > 0


def test_web_events_contain_invalid_customer_references() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    assert (events["customer_id"] == "INVALID_CUSTOMER").any()


def test_web_events_contain_invalid_product_references() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    assert (events["product_id"] == "INVALID_PRODUCT").any()


def test_web_events_contain_invalid_order_references() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    assert (events["order_id"] == "INVALID_ORDER").any()


def test_web_events_contain_invalid_event_types() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    assert (events["event_type"] == "UNKNOWN_EVENT").any()


def test_web_events_contain_malformed_sessions() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    assert (events["session_id"] == "").any()


def test_web_events_contain_negative_revenue() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    assert (events["revenue_amount"] < 0).any()


def test_web_events_contain_timestamp_violations() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    invalid_timestamps = events["source_received_at"] < events["event_timestamp"]

    assert invalid_timestamps.any()


def test_web_events_contain_delayed_source_records() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    delay = events["source_received_at"] - events["event_timestamp"]

    assert (delay >= pd.Timedelta(3, unit="D")).any()


def test_web_events_contain_expected_event_types() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    observed_types = set(events["event_type"])

    assert observed_types.intersection(EVENT_TYPES)


def test_purchase_events_have_order_context() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    purchase_events = events[events["event_type"] == "PURCHASE"]

    assert len(purchase_events) > 0
    assert purchase_events["order_id"].notna().any()


def test_product_events_have_product_context() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    product_events = events[events["event_type"] == "PRODUCT_VIEW"]

    assert len(product_events) > 0
    assert product_events["product_id"].notna().all()


def test_web_events_contain_multiple_sessions() -> None:
    config, customers, products, orders = _build_dependencies()

    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    assert events["session_id"].nunique() > 1
