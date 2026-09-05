import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.utils import (
    create_rng,
    generate_id,
    random_choice,
    random_date,
)

PRODUCT_CATEGORIES = [
    "electronics",
    "home",
    "sports",
    "books",
    "beauty",
    "clothing",
    "office",
]

PRODUCT_STATUSES = [
    "active",
    "inactive",
    "discontinued",
]

PRODUCT_PREFIXES = [
    "Pro",
    "Essential",
    "Premium",
    "Classic",
    "Smart",
    "Advanced",
    "Compact",
]

PRODUCT_NAMES = [
    "Laptop",
    "Headphones",
    "Backpack",
    "Desk Lamp",
    "Coffee Maker",
    "Running Shoes",
    "Office Chair",
    "Smart Watch",
    "Bluetooth Speaker",
    "Water Bottle",
    "Keyboard",
    "Mouse",
    "Monitor",
    "Notebook",
    "Jacket",
]


def generate_products(
    config: DataGenerationConfig,
) -> pd.DataFrame:
    """Generate a deterministic synthetic product source dataset."""

    rng = create_rng(config.seed + 10)

    records: list[dict[str, object]] = []

    for _ in range(config.products_count):
        product_id = generate_id(rng)

        prefix = random_choice(rng, PRODUCT_PREFIXES)
        product_name = random_choice(rng, PRODUCT_NAMES)

        records.append(
            {
                "product_id": product_id,
                "product_name": f"{prefix} {product_name}",
                "category": random_choice(
                    rng,
                    PRODUCT_CATEGORIES,
                ),
                "unit_price": round(
                    rng.uniform(5.0, 1500.0),
                    2,
                ),
                "product_status": random_choice(
                    rng,
                    PRODUCT_STATUSES,
                ),
                "created_date": random_date(
                    rng,
                    config.start_date,
                    config.end_date,
                ),
            }
        )

    products = pd.DataFrame(records)

    return _introduce_product_quality_issues(
        products,
        config,
    )


def _introduce_product_quality_issues(
    products: pd.DataFrame,
    config: DataGenerationConfig,
) -> pd.DataFrame:
    """Introduce controlled source-system quality issues."""

    if products.empty:
        return products

    rng = create_rng(config.seed + 11)
    result = products.copy()

    issue_count = min(
        max(1, len(result) // 100),
        len(result),
    )

    issue_indices = rng.sample(
        range(len(result)),
        issue_count,
    )

    # Missing category values simulate incomplete source records.
    result.loc[issue_indices, "category"] = None

    invalid_price_count = min(
        max(1, len(result) // 250),
        len(result),
    )

    invalid_price_indices = rng.sample(
        range(len(result)),
        invalid_price_count,
    )

    # Negative prices are intentionally invalid.
    result.loc[
        invalid_price_indices,
        "unit_price",
    ] = -10.0

    return result


def expected_product_columns() -> list[str]:
    """Return the expected product source columns."""

    return [
        "product_id",
        "product_name",
        "category",
        "unit_price",
        "product_status",
        "created_date",
    ]
