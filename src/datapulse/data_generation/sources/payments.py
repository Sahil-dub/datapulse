from __future__ import annotations

import random

import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig

PAYMENT_METHODS = [
    "CREDIT_CARD",
    "DEBIT_CARD",
    "PAYPAL",
    "BANK_TRANSFER",
]

PAYMENT_STATUSES = [
    "PENDING",
    "AUTHORIZED",
    "CAPTURED",
    "FAILED",
    "REFUNDED",
    "CANCELLED",
]

CURRENCIES = [
    "EUR",
    "USD",
    "GBP",
]


def expected_payment_columns() -> list[str]:
    """Return the expected Payments source-system columns."""
    return [
        "payment_id",
        "order_id",
        "payment_date",
        "payment_method",
        "payment_amount",
        "payment_status",
        "transaction_reference",
        "currency",
        "source_updated_at",
    ]


def generate_payments(
    config: DataGenerationConfig,
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Generate synthetic Payments source-system data.

    The generated dataset contains multiple payment attempts for some
    orders, plus controlled duplicates, unmatched orders, invalid amounts,
    invalid statuses, and delayed source updates.
    """
    rng = random.Random(config.seed + 300)

    valid_orders = orders[orders["order_id"].notna()].copy()

    order_ids = valid_orders["order_id"].astype(str).tolist()

    order_dates = dict(
        zip(
            valid_orders["order_id"].astype(str),
            pd.to_datetime(valid_orders["order_date"]),
            strict=True,
        )
    )

    order_totals = dict(
        zip(
            valid_orders["order_id"].astype(str),
            valid_orders["order_total"],
            strict=True,
        )
    )

    rows: list[dict] = []

    for index in range(config.payments_count):
        payment_id = f"PAY-{index + 1:06d}"

        order_id = rng.choice(order_ids)
        order_date = order_dates[order_id]

        payment_date = order_date + (
            pd.Timedelta(int(rng.randint(0, 3)), unit="D")
            + pd.Timedelta(int(rng.randint(0, 23)), unit="h")
            + pd.Timedelta(int(rng.randint(0, 59)), unit="m")
        )

        order_total = max(float(order_totals[order_id]), 0.0)

        # Most payments correspond to the order value, but payment attempts
        # may be smaller or larger because failed/retried payments exist.
        payment_amount = round(
            order_total
            * rng.choice(
                [
                    1.0,
                    1.0,
                    1.0,
                    0.5,
                    0.75,
                    1.05,
                ]
            ),
            2,
        )

        payment_status = rng.choice(PAYMENT_STATUSES)

        source_updated_at = payment_date + pd.Timedelta(
            int(rng.randint(1, 60)),
            unit="m",
        )

        rows.append(
            {
                "payment_id": payment_id,
                "order_id": order_id,
                "payment_date": payment_date,
                "payment_method": rng.choice(PAYMENT_METHODS),
                "payment_amount": payment_amount,
                "payment_status": payment_status,
                "transaction_reference": f"TXN-{index + 1:08d}",
                "currency": rng.choice(CURRENCIES),
                "source_updated_at": source_updated_at,
            }
        )

    payments = pd.DataFrame(rows)

    # ---------------------------------------------------------
    # Controlled data-quality issues
    # ---------------------------------------------------------

    # Payments referencing orders that do not exist.
    unmatched_count = max(1, config.payments_count // 100)
    unmatched_indices = rng.sample(
        range(len(payments)),
        unmatched_count,
    )
    payments.loc[unmatched_indices, "order_id"] = "ORD-999999"

    # Invalid payment amounts.
    invalid_amount_count = max(1, config.payments_count // 200)
    invalid_amount_indices = rng.sample(
        range(len(payments)),
        invalid_amount_count,
    )
    for index in invalid_amount_indices:
        payments.loc[index, "payment_amount"] = rng.choice([-25.0, -10.0, 0.0])

    # Invalid payment statuses.
    invalid_status_count = max(1, config.payments_count // 250)
    invalid_status_indices = rng.sample(
        range(len(payments)),
        invalid_status_count,
    )
    payments.loc[invalid_status_indices, "payment_status"] = "UNKNOWN_STATUS"

    # Inconsistent captured payments: captured but zero amount.
    captured_zero_count = max(1, config.payments_count // 250)
    captured_zero_indices = rng.sample(
        range(len(payments)),
        captured_zero_count,
    )
    payments.loc[captured_zero_indices, "payment_status"] = "CAPTURED"
    payments.loc[captured_zero_indices, "payment_amount"] = 0.0

    # Delayed source updates.
    delayed_count = max(1, config.payments_count // 100)
    delayed_indices = rng.sample(
        range(len(payments)),
        delayed_count,
    )
    payments.loc[delayed_indices, "source_updated_at"] = payments.loc[
        delayed_indices, "payment_date"
    ] + pd.Timedelta(
        int(rng.randint(2, 5)),
        unit="D",
    )

    # Duplicate complete payment records while preserving the configured
    # target volume.
    duplicate_count = max(1, config.payments_count // 100)
    duplicate_indices = rng.sample(
        range(config.payments_count - duplicate_count),
        duplicate_count,
    )
    duplicates = payments.iloc[duplicate_indices].copy()

    payments = pd.concat(
        [
            payments.iloc[:-duplicate_count],
            duplicates,
        ],
        ignore_index=True,
    )

    # Keep the configured target volume.
    payments = payments.iloc[: config.payments_count].reset_index(drop=True)

    return payments[expected_payment_columns()]
