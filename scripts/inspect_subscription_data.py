from pathlib import Path

import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.sources.customers import generate_customers
from datapulse.data_generation.sources.subscriptions import (
    generate_subscriptions,
)


def main() -> None:
    config = DataGenerationConfig()

    print("Generating full-scale synthetic customer and subscription data...")

    customers = generate_customers(config)
    subscriptions = generate_subscriptions(config, customers)

    valid_customer_ids = set(customers["customer_id"].dropna())

    print("\n=== ROW COUNTS ===")
    print(f"Customers: {len(customers):,}")
    print(f"Subscriptions: {len(subscriptions):,}")

    print("\n=== SUBSCRIPTION DATA QUALITY SIGNALS ===")
    print(
        "Duplicate subscription IDs:",
        subscriptions["subscription_id"].duplicated().sum(),
    )
    print(
        "Missing customer references:",
        subscriptions["customer_id"].isna().sum(),
    )
    print(
        "Invalid customer references:",
        (
            subscriptions["customer_id"].notna()
            & ~subscriptions["customer_id"].isin(valid_customer_ids)
        ).sum(),
    )
    print(
        "Invalid plans:",
        (subscriptions["plan_type"] == "UNKNOWN_PLAN").sum(),
    )
    print(
        "Invalid subscription statuses:",
        (subscriptions["subscription_status"] == "UNKNOWN_STATUS").sum(),
    )
    print(
        "Invalid billing frequencies:",
        (subscriptions["billing_frequency"] == "UNKNOWN_FREQUENCY").sum(),
    )
    print(
        "Invalid monthly fees:",
        (subscriptions["monthly_fee"] <= 0).sum(),
    )

    invalid_dates = (
        subscriptions["end_date"].notna()
        & (subscriptions["end_date"] < subscriptions["start_date"])
    )
    print("Invalid date relationships:", invalid_dates.sum())

    cancelled_without_end = (
        (subscriptions["subscription_status"] == "CANCELLED")
        & subscriptions["end_date"].isna()
    )
    print(
        "Cancelled subscriptions without end date:",
        cancelled_without_end.sum(),
    )

    latency = subscriptions["source_updated_at"] - subscriptions["start_date"]
    print(
        "Delayed source updates (>= 3 days):",
        (latency >= pd.Timedelta(3, unit="D")).sum(),
    )

    print("\n=== PLAN DISTRIBUTION ===")
    print(subscriptions["plan_type"].value_counts())

    print("\n=== STATUS DISTRIBUTION ===")
    print(subscriptions["subscription_status"].value_counts())

    print("\n=== BILLING FREQUENCY DISTRIBUTION ===")
    print(subscriptions["billing_frequency"].value_counts())

    print("\n=== AUTO-RENEW DISTRIBUTION ===")
    print(subscriptions["auto_renew"].value_counts())

    print("\nInspection complete.")


if __name__ == "__main__":
    main()