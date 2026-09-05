import pandas as pd
import pytest

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.sources.customers import (
    expected_customer_columns,
    generate_customers,
)
from datapulse.data_generation.sources.products import (
    expected_product_columns,
    generate_products,
)


@pytest.fixture
def small_config() -> DataGenerationConfig:
    """Provide a small deterministic configuration for unit tests."""

    return DataGenerationConfig(
        seed=42,
        customers_count=100,
        products_count=25,
    )


def test_generate_customers_returns_expected_columns(
    small_config: DataGenerationConfig,
) -> None:
    customers = generate_customers(small_config)

    assert list(customers.columns) == expected_customer_columns()


def test_generate_customers_contains_expected_volume(
    small_config: DataGenerationConfig,
) -> None:
    customers = generate_customers(small_config)

    assert len(customers) > small_config.customers_count


def test_generate_customers_has_duplicate_ids(
    small_config: DataGenerationConfig,
) -> None:
    customers = generate_customers(small_config)

    duplicate_count = customers["customer_id"].duplicated().sum()

    assert duplicate_count > 0


def test_generate_customers_contains_missing_emails(
    small_config: DataGenerationConfig,
) -> None:
    customers = generate_customers(small_config)

    assert customers["email"].isna().sum() > 0


def test_generate_customers_contains_invalid_country(
    small_config: DataGenerationConfig,
) -> None:
    customers = generate_customers(small_config)

    assert (customers["country"] == "UNKNOWN_COUNTRY").any()


def test_generate_customers_is_reproducible(
    small_config: DataGenerationConfig,
) -> None:
    first = generate_customers(small_config)
    second = generate_customers(small_config)

    pd.testing.assert_frame_equal(first, second)


def test_generate_customers_different_seed_changes_output() -> None:
    first_config = DataGenerationConfig(
        seed=42,
        customers_count=100,
    )
    second_config = DataGenerationConfig(
        seed=99,
        customers_count=100,
    )

    first = generate_customers(first_config)
    second = generate_customers(second_config)

    assert not first.equals(second)


def test_generate_products_returns_expected_columns(
    small_config: DataGenerationConfig,
) -> None:
    products = generate_products(small_config)

    assert list(products.columns) == expected_product_columns()


def test_generate_products_contains_expected_volume(
    small_config: DataGenerationConfig,
) -> None:
    products = generate_products(small_config)

    assert len(products) == small_config.products_count


def test_generate_products_contains_missing_categories(
    small_config: DataGenerationConfig,
) -> None:
    products = generate_products(small_config)

    assert products["category"].isna().sum() > 0


def test_generate_products_contains_invalid_prices(
    small_config: DataGenerationConfig,
) -> None:
    products = generate_products(small_config)

    assert (products["unit_price"] < 0).any()


def test_generate_products_is_reproducible(
    small_config: DataGenerationConfig,
) -> None:
    first = generate_products(small_config)
    second = generate_products(small_config)

    pd.testing.assert_frame_equal(first, second)


def test_generate_products_different_seed_changes_output() -> None:
    first_config = DataGenerationConfig(
        seed=42,
        products_count=25,
    )
    second_config = DataGenerationConfig(
        seed=99,
        products_count=25,
    )

    first = generate_products(first_config)
    second = generate_products(second_config)

    assert not first.equals(second)
