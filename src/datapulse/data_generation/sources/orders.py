from __future__ import annotations

import random
from decimal import Decimal

import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig

ORDER_STATUSES = [
    "PENDING",
    "CONFIRMED",
    "SHIPPED",
    "DELIVERED",
    "CANCELLED",
    "RETURNED",
]

SALES_CHANNELS = [
    "WEB",
    "MOBILE_APP",
    "MARKETPLACE",
    "STORE",
]


def expected_order_columns() -> list[str]:
    """Return the expected Orders source-system columns."""
    return [
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
    ]


def generate_orders(
    config: DataGenerationConfig,
    customers: pd.DataFrame,
    products: pd.DataFrame,
) -> pd.DataFrame:
    """Generate synthetic Orders source-system data.

    The generated dataset contains mostly valid orders plus controlled
    duplicates, missing references, invalid references, invalid quantities,
    invalid monetary values, and invalid categorical values.
    """
    rng = random.Random(config.seed + 200)

    customer_ids = customers["customer_id"].dropna().astype(str).tolist()
    product_ids = products["product_id"].dropna().astype(str).tolist()

    product_prices = dict(
        zip(
            products["product_id"].astype(str),
            products["unit_price"],
            strict=True,
        )
    )

    rows: list[dict] = []

    for index in range(config.orders_count):
        order_id = f"ORD-{index + 1:06d}"

        customer_id = rng.choice(customer_ids)
        product_id = rng.choice(product_ids)

        order_date = pd.Timestamp(
            config.start_date + (config.end_date - config.start_date) * rng.random()
        ).floor("s")

        quantity = rng.randint(1, 5)
        unit_price = Decimal(str(product_prices[product_id])).quantize(Decimal("0.01"))

        subtotal = unit_price * quantity
        discount_amount = (subtotal * Decimal(str(rng.choice([0, 0.05, 0.10, 0.15])))).quantize(
            Decimal("0.01")
        )

        shipping_amount = Decimal(str(rng.choice([0, 4.99, 7.99, 9.99]))).quantize(Decimal("0.01"))

        order_total = (subtotal - discount_amount + shipping_amount).quantize(Decimal("0.01"))

        rows.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "product_id": product_id,
                "order_date": order_date,
                "quantity": quantity,
                "unit_price": float(unit_price),
                "discount_amount": float(discount_amount),
                "shipping_amount": float(shipping_amount),
                "order_total": float(order_total),
                "order_status": rng.choice(ORDER_STATUSES),
                "sales_channel": rng.choice(SALES_CHANNELS),
            }
        )

    orders = pd.DataFrame(rows)

    # ---------------------------------------------------------
    # Controlled data-quality issues
    # ---------------------------------------------------------

    # Missing customer references.
    missing_customer_count = max(1, config.orders_count // 100)
    missing_customer_indices = rng.sample(
        range(len(orders)),
        missing_customer_count,
    )
    orders.loc[missing_customer_indices, "customer_id"] = None

    # Invalid customer references.
    invalid_customer_count = max(1, config.orders_count // 100)
    invalid_customer_indices = rng.sample(
        [index for index in range(len(orders)) if index not in missing_customer_indices],
        invalid_customer_count,
    )
    orders.loc[invalid_customer_indices, "customer_id"] = "CUST-999999"

    # Missing product references.
    missing_product_count = max(1, config.orders_count // 200)
    missing_product_indices = rng.sample(
        range(len(orders)),
        missing_product_count,
    )
    orders.loc[missing_product_indices, "product_id"] = None

    # Invalid product references.
    invalid_product_count = max(1, config.orders_count // 200)
    invalid_product_indices = rng.sample(
        [index for index in range(len(orders)) if index not in missing_product_indices],
        invalid_product_count,
    )
    orders.loc[invalid_product_indices, "product_id"] = "PROD-999999"

    # Invalid quantities.
    invalid_quantity_count = max(1, config.orders_count // 200)
    invalid_quantity_indices = rng.sample(
        range(len(orders)),
        invalid_quantity_count,
    )
    for index in invalid_quantity_indices:
        orders.loc[index, "quantity"] = rng.choice([0, -1, -2])

    # Invalid unit prices.
    invalid_price_count = max(1, config.orders_count // 250)
    invalid_price_indices = rng.sample(
        range(len(orders)),
        invalid_price_count,
    )
    for index in invalid_price_indices:
        orders.loc[index, "unit_price"] = rng.choice([-10.0, -25.0, 0.0])

    # Incorrect order totals.
    invalid_total_count = max(1, config.orders_count // 200)
    invalid_total_indices = rng.sample(
        range(len(orders)),
        invalid_total_count,
    )
    for index in invalid_total_indices:
        orders.loc[index, "order_total"] = round(
            float(orders.loc[index, "order_total"]) + rng.choice([-50, 25, 100]),
            2,
        )

    # Invalid categorical values.
    invalid_status_count = max(1, config.orders_count // 250)
    invalid_status_indices = rng.sample(
        range(len(orders)),
        invalid_status_count,
    )
    orders.loc[invalid_status_indices, "order_status"] = "UNKNOWN_STATUS"

    # Duplicate complete records while preserving the configured target volume.
    duplicate_count = max(1, config.orders_count // 100)
    duplicate_indices = rng.sample(
        range(config.orders_count - duplicate_count),
        duplicate_count,
    )
    duplicates = orders.iloc[duplicate_indices].copy()

    orders = pd.concat(
        [
            orders.iloc[:-duplicate_count],
            duplicates,
        ],
        ignore_index=True,
    )

    # Keep the configured target volume.
    orders = orders.iloc[: config.orders_count].reset_index(drop=True)

    return orders[expected_order_columns()]
