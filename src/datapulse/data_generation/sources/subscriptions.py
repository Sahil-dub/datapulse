from __future__ import annotations

import random
from typing import Final

import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.utils import generate_id

PLAN_TYPES: Final = ["BASIC", "STANDARD", "PREMIUM", "ENTERPRISE"]
SUBSCRIPTION_STATUSES: Final = ["ACTIVE", "PAUSED", "CANCELLED", "EXPIRED"]
BILLING_FREQUENCIES: Final = ["MONTHLY", "QUARTERLY", "YEARLY"]

PLAN_FEES: Final = {
    "BASIC": 9.99,
    "STANDARD": 19.99,
    "PREMIUM": 39.99,
    "ENTERPRISE": 99.99,
}


def expected_subscription_columns() -> list[str]:
    return [
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
    ]


def generate_subscriptions(
    config: DataGenerationConfig,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """Generate deterministic, intentionally dirty subscription source data."""
    rng = random.Random(config.seed + 400)

    customer_ids = customers["customer_id"].dropna().astype(str).tolist()

    rows: list[dict] = []

    for _ in range(config.subscriptions_count):
        subscription_id = generate_id(rng)

        customer_id = rng.choice(customer_ids)

        plan_type = rng.choice(PLAN_TYPES)
        billing_frequency = rng.choice(BILLING_FREQUENCIES)
        status = rng.choice(SUBSCRIPTION_STATUSES)

        start_date = pd.Timestamp(config.start_date) + pd.Timedelta(
            rng.randint(
                0,
                (config.end_date - config.start_date).days,
            ),
            unit="D",
        )

        # Most subscriptions have an end date only when they are not active.
        if status == "ACTIVE":
            end_date = pd.NaT
        else:
            duration_days = rng.randint(30, 730)
            end_date = start_date + pd.Timedelta(duration_days, unit="D")

        monthly_fee = PLAN_FEES[plan_type]
        auto_renew = status == "ACTIVE" and rng.random() < 0.8

        source_updated_at = start_date + pd.Timedelta(
            rng.randint(0, 72),
            unit="h",
        )

        rows.append(
            {
                "subscription_id": subscription_id,
                "customer_id": customer_id,
                "plan_type": plan_type,
                "subscription_status": status,
                "billing_frequency": billing_frequency,
                "start_date": start_date,
                "end_date": end_date,
                "monthly_fee": monthly_fee,
                "auto_renew": auto_renew,
                "source_updated_at": source_updated_at,
            }
        )

    subscriptions = pd.DataFrame(rows, columns=expected_subscription_columns())

    # Missing customer references.
    missing_customer_count = max(1, int(config.subscriptions_count * 0.01))
    missing_indices = rng.sample(
        range(config.subscriptions_count),
        missing_customer_count,
    )
    subscriptions.loc[missing_indices, "customer_id"] = None

    # Invalid customer references.
    invalid_customer_count = max(1, int(config.subscriptions_count * 0.01))
    available_indices = [
        index for index in range(config.subscriptions_count) if index not in missing_indices
    ]
    invalid_indices = rng.sample(available_indices, invalid_customer_count)
    subscriptions.loc[invalid_indices, "customer_id"] = "UNKNOWN_CUSTOMER"

    # Invalid plans.
    invalid_plan_count = max(1, int(config.subscriptions_count * 0.01))
    plan_indices = rng.sample(
        range(config.subscriptions_count),
        invalid_plan_count,
    )
    subscriptions.loc[plan_indices, "plan_type"] = "UNKNOWN_PLAN"

    # Invalid subscription statuses.
    invalid_status_count = max(1, int(config.subscriptions_count * 0.01))
    status_indices = rng.sample(
        range(config.subscriptions_count),
        invalid_status_count,
    )
    subscriptions.loc[status_indices, "subscription_status"] = "UNKNOWN_STATUS"

    # Invalid billing frequencies.
    invalid_frequency_count = max(1, int(config.subscriptions_count * 0.01))
    frequency_indices = rng.sample(
        range(config.subscriptions_count),
        invalid_frequency_count,
    )
    subscriptions.loc[frequency_indices, "billing_frequency"] = "UNKNOWN_FREQUENCY"

    # Invalid monetary values.
    invalid_fee_count = max(1, int(config.subscriptions_count * 0.01))
    fee_indices = rng.sample(
        range(config.subscriptions_count),
        invalid_fee_count,
    )
    subscriptions.loc[fee_indices, "monthly_fee"] = -9.99

    # Invalid date relationships.
    invalid_date_count = max(1, int(config.subscriptions_count * 0.01))
    date_indices = rng.sample(
        range(config.subscriptions_count),
        invalid_date_count,
    )
    for index in date_indices:
        start_date = subscriptions.loc[index, "start_date"]
        subscriptions.loc[index, "end_date"] = start_date - pd.Timedelta(
            rng.randint(1, 30),
            unit="D",
        )

    # Lifecycle inconsistency: cancelled subscriptions without an end date.
    cancelled_indices = subscriptions.index[
        subscriptions["subscription_status"] == "CANCELLED"
    ].tolist()
    if cancelled_indices:
        inconsistency_count = max(
            1,
            int(config.subscriptions_count * 0.005),
        )
        inconsistency_count = min(inconsistency_count, len(cancelled_indices))
        selected = rng.sample(cancelled_indices, inconsistency_count)
        subscriptions.loc[selected, "end_date"] = pd.NaT

    # Delayed source updates.
    delayed_count = max(1, int(config.subscriptions_count * 0.01))
    delayed_indices = rng.sample(
        range(config.subscriptions_count),
        delayed_count,
    )
    subscriptions.loc[delayed_indices, "source_updated_at"] = subscriptions.loc[
        delayed_indices, "source_updated_at"
    ] + pd.Timedelta(rng.randint(3, 10), unit="D")

    # Duplicate complete records while preserving the target row count.
    duplicate_count = max(1, int(config.subscriptions_count * 0.01))
    base_count = config.subscriptions_count - duplicate_count
    duplicate_indices = rng.sample(range(base_count), duplicate_count)

    duplicate_rows = subscriptions.iloc[duplicate_indices].copy()
    subscriptions = pd.concat(
        [subscriptions.iloc[:base_count], duplicate_rows],
        ignore_index=True,
    )

    return subscriptions
