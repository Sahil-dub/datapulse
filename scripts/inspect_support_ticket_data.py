from __future__ import annotations

import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.sources.customers import generate_customers
from datapulse.data_generation.sources.support_tickets import (
    generate_support_tickets,
)


def main() -> None:
    config = DataGenerationConfig()

    print("Generating full-scale synthetic customer and support-ticket data...")

    customers = generate_customers(config)
    tickets = generate_support_tickets(config, customers)

    valid_customer_ids = set(customers["customer_id"].dropna())

    print("\n=== ROW COUNTS ===")
    print(f"Customers: {len(customers):,}")
    print(f"Support tickets: {len(tickets):,}")

    print("\n=== SUPPORT TICKET DATA QUALITY SIGNALS ===")
    print(
        "Duplicate ticket IDs:",
        tickets["ticket_id"].duplicated().sum(),
    )
    print(
        "Missing customer references:",
        tickets["customer_id"].isna().sum(),
    )
    print(
        "Invalid customer references:",
        (tickets["customer_id"].notna() & ~tickets["customer_id"].isin(valid_customer_ids)).sum(),
    )
    print(
        "Invalid categories:",
        (tickets["ticket_category"] == "UNKNOWN_CATEGORY").sum(),
    )
    print(
        "Invalid priorities:",
        (tickets["priority"] == "UNKNOWN_PRIORITY").sum(),
    )
    print(
        "Invalid statuses:",
        (tickets["ticket_status"] == "UNKNOWN_STATUS").sum(),
    )
    print(
        "Invalid resolution channels:",
        (tickets["resolution_channel"] == "UNKNOWN_CHANNEL").sum(),
    )
    print(
        "Invalid assigned teams:",
        (tickets["assigned_team"] == "UNKNOWN_TEAM").sum(),
    )
    print(
        "Negative resolution times:",
        (tickets["resolution_time_hours"] < 0).sum(),
    )
    print(
        "Extremely large resolution times (>1,000 hours):",
        (tickets["resolution_time_hours"] > 1000).sum(),
    )

    resolved_without_time = (
        tickets["ticket_status"].isin(["RESOLVED", "CLOSED"])
        & tickets["resolution_time_hours"].isna()
    )
    print(
        "Resolved/closed tickets without resolution time:",
        resolved_without_time.sum(),
    )

    open_with_time = (
        tickets["ticket_status"].isin(["OPEN", "IN_PROGRESS"])
        & tickets["resolution_time_hours"].notna()
    )
    print(
        "Open/in-progress tickets with resolution time:",
        open_with_time.sum(),
    )

    invalid_satisfaction = tickets["customer_satisfaction_score"].notna() & ~tickets[
        "customer_satisfaction_score"
    ].between(1, 5)
    print(
        "Invalid satisfaction scores:",
        invalid_satisfaction.sum(),
    )

    timestamp_inconsistencies = tickets["ticket_updated_at"] < tickets["ticket_created_at"]
    print(
        "Updated-before-created timestamps:",
        timestamp_inconsistencies.sum(),
    )

    update_latency = tickets["ticket_updated_at"] - tickets["ticket_created_at"]
    print(
        "Delayed source updates (>= 3 days):",
        (update_latency >= pd.Timedelta(3, unit="D")).sum(),
    )

    print("\n=== CATEGORY DISTRIBUTION ===")
    print(tickets["ticket_category"].value_counts())

    print("\n=== PRIORITY DISTRIBUTION ===")
    print(tickets["priority"].value_counts())

    print("\n=== STATUS DISTRIBUTION ===")
    print(tickets["ticket_status"].value_counts())

    print("\n=== RESOLUTION CHANNEL DISTRIBUTION ===")
    print(tickets["resolution_channel"].value_counts())

    print("\n=== ASSIGNED TEAM DISTRIBUTION ===")
    print(tickets["assigned_team"].value_counts())

    print("\nInspection complete.")


if __name__ == "__main__":
    main()
