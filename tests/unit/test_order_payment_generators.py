import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.sources.customers import generate_customers
from datapulse.data_generation.sources.orders import (
    expected_order_columns,
    generate_orders,
)
from datapulse.data_generation.sources.payments import (
    expected_payment_columns,
    generate_payments,
)
from datapulse.data_generation.sources.products import generate_products


def build_dependencies() -> tuple[
    DataGenerationConfig,
    pd.DataFrame,
    pd.DataFrame,
]:
    config = DataGenerationConfig(
        customers_count=100,
        products_count=20,
        orders_count=500,
        payments_count=550,
    )

    customers = generate_customers(config)
    products = generate_products(config)

    return config, customers, products


def test_orders_have_expected_columns() -> None:
    config, customers, products = build_dependencies()

    orders = generate_orders(config, customers, products)

    assert list(orders.columns) == expected_order_columns()


def test_orders_have_expected_volume() -> None:
    config, customers, products = build_dependencies()

    orders = generate_orders(config, customers, products)

    assert len(orders) == config.orders_count


def test_orders_are_reproducible() -> None:
    config, customers, products = build_dependencies()

    first = generate_orders(config, customers, products)
    second = generate_orders(config, customers, products)

    pd.testing.assert_frame_equal(first, second)


def test_orders_contain_duplicate_ids() -> None:
    config, customers, products = build_dependencies()

    orders = generate_orders(config, customers, products)

    assert orders["order_id"].duplicated().any()


def test_orders_contain_missing_customer_ids() -> None:
    config, customers, products = build_dependencies()

    orders = generate_orders(config, customers, products)

    assert orders["customer_id"].isna().any()


def test_orders_contain_invalid_customer_ids() -> None:
    config, customers, products = build_dependencies()

    orders = generate_orders(config, customers, products)

    valid_customer_ids = set(customers["customer_id"])

    invalid_ids = set(orders["customer_id"].dropna()) - valid_customer_ids

    assert invalid_ids


def test_orders_contain_missing_product_ids() -> None:
    config, customers, products = build_dependencies()

    orders = generate_orders(config, customers, products)

    assert orders["product_id"].isna().any()


def test_orders_contain_invalid_quantities() -> None:
    config, customers, products = build_dependencies()

    orders = generate_orders(config, customers, products)

    assert (orders["quantity"] <= 0).any()


def test_orders_contain_invalid_prices() -> None:
    config, customers, products = build_dependencies()

    orders = generate_orders(config, customers, products)

    assert (orders["unit_price"] <= 0).any()


def test_orders_contain_invalid_statuses() -> None:
    config, customers, products = build_dependencies()

    orders = generate_orders(config, customers, products)

    assert (orders["order_status"] == "UNKNOWN_STATUS").any()


def test_payments_have_expected_columns() -> None:
    config, customers, products = build_dependencies()
    orders = generate_orders(config, customers, products)

    payments = generate_payments(config, orders)

    assert list(payments.columns) == expected_payment_columns()


def test_payments_have_expected_volume() -> None:
    config, customers, products = build_dependencies()
    orders = generate_orders(config, customers, products)

    payments = generate_payments(config, orders)

    assert len(payments) == config.payments_count


def test_payments_are_reproducible() -> None:
    config, customers, products = build_dependencies()
    orders = generate_orders(config, customers, products)

    first = generate_payments(config, orders)
    second = generate_payments(config, orders)

    pd.testing.assert_frame_equal(first, second)


def test_payments_contain_duplicate_ids() -> None:
    config, customers, products = build_dependencies()
    orders = generate_orders(config, customers, products)

    payments = generate_payments(config, orders)

    assert payments["payment_id"].duplicated().any()


def test_payments_contain_unmatched_orders() -> None:
    config, customers, products = build_dependencies()
    orders = generate_orders(config, customers, products)

    payments = generate_payments(config, orders)

    valid_order_ids = set(orders["order_id"])

    unmatched_ids = set(payments["order_id"]) - valid_order_ids

    assert unmatched_ids


def test_payments_contain_invalid_amounts() -> None:
    config, customers, products = build_dependencies()
    orders = generate_orders(config, customers, products)

    payments = generate_payments(config, orders)

    assert (payments["payment_amount"] <= 0).any()


def test_payments_contain_invalid_statuses() -> None:
    config, customers, products = build_dependencies()
    orders = generate_orders(config, customers, products)

    payments = generate_payments(config, orders)

    assert (payments["payment_status"] == "UNKNOWN_STATUS").any()


def test_payments_contain_delayed_records() -> None:
    config, customers, products = build_dependencies()
    orders = generate_orders(config, customers, products)

    payments = generate_payments(config, orders)

    latency = pd.to_datetime(payments["source_updated_at"]) - pd.to_datetime(
        payments["payment_date"]
    )

    assert (latency >= pd.Timedelta(2, unit="D")).any()
