from __future__ import annotations

import random
from typing import Final

import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.utils import generate_id

TICKET_CATEGORIES: Final = [
    "BILLING",
    "PAYMENT",
    "DELIVERY",
    "PRODUCT",
    "ACCOUNT",
    "TECHNICAL",
    "REFUND",
    "OTHER",
]

PRIORITIES: Final = ["LOW", "MEDIUM", "HIGH", "URGENT"]

TICKET_STATUSES: Final = [
    "OPEN",
    "IN_PROGRESS",
    "RESOLVED",
    "CLOSED",
    "ESCALATED",
]

RESOLUTION_CHANNELS: Final = [
    "EMAIL",
    "CHAT",
    "PHONE",
    "SELF_SERVICE",
]

ASSIGNED_TEAMS: Final = [
    "BILLING_SUPPORT",
    "PAYMENTS_SUPPORT",
    "LOGISTICS_SUPPORT",
    "PRODUCT_SUPPORT",
    "ACCOUNT_SUPPORT",
    "TECH_SUPPORT",
    "GENERAL_SUPPORT",
]


def expected_support_ticket_columns() -> list[str]:
    return [
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
    ]


def generate_support_tickets(
    config: DataGenerationConfig,
    customers: pd.DataFrame,
) -> pd.DataFrame:
    """Generate deterministic, intentionally dirty support-ticket data."""
    rng = random.Random(config.seed + 500)

    customer_ids = customers["customer_id"].dropna().astype(str).tolist()

    rows: list[dict] = []

    start_timestamp = pd.Timestamp(config.start_date)
    end_timestamp = pd.Timestamp(config.end_date)
    total_seconds = int((end_timestamp - start_timestamp).total_seconds())

    for _ in range(config.support_tickets_count):
        ticket_id = generate_id(rng)
        customer_id = rng.choice(customer_ids)

        created_at = start_timestamp + pd.Timedelta(
            rng.randint(0, total_seconds),
            unit="s",
        )

        status = rng.choice(TICKET_STATUSES)
        category = rng.choice(TICKET_CATEGORIES)
        priority = rng.choice(PRIORITIES)
        resolution_channel = rng.choice(RESOLUTION_CHANNELS)
        assigned_team = rng.choice(ASSIGNED_TEAMS)

        if status in {"RESOLVED", "CLOSED"}:
            resolution_time_hours = round(rng.uniform(0.5, 240.0), 2)
            satisfaction_score = rng.randint(1, 5)
            updated_at = created_at + pd.Timedelta(
                int(resolution_time_hours * 3600),
                unit="s",
            )
        else:
            resolution_time_hours = None
            satisfaction_score = None
            updated_at = created_at + pd.Timedelta(
                rng.randint(0, 72),
                unit="h",
            )

        rows.append(
            {
                "ticket_id": ticket_id,
                "customer_id": customer_id,
                "ticket_created_at": created_at,
                "ticket_updated_at": updated_at,
                "ticket_category": category,
                "priority": priority,
                "ticket_status": status,
                "resolution_channel": resolution_channel,
                "assigned_team": assigned_team,
                "resolution_time_hours": resolution_time_hours,
                "customer_satisfaction_score": satisfaction_score,
            }
        )

    tickets = pd.DataFrame(
        rows,
        columns=expected_support_ticket_columns(),
    )

    row_count = config.support_tickets_count

    # Missing customer references.
    missing_customer_count = max(1, int(row_count * 0.01))
    missing_indices = rng.sample(range(row_count), missing_customer_count)
    tickets.loc[missing_indices, "customer_id"] = None

    # Invalid customer references.
    invalid_customer_count = max(1, int(row_count * 0.01))
    available_indices = [index for index in range(row_count) if index not in missing_indices]
    invalid_indices = rng.sample(available_indices, invalid_customer_count)
    tickets.loc[invalid_indices, "customer_id"] = "UNKNOWN_CUSTOMER"

    # Invalid categorical values.
    invalid_category_indices = rng.sample(
        range(row_count),
        max(1, int(row_count * 0.01)),
    )
    tickets.loc[invalid_category_indices, "ticket_category"] = "UNKNOWN_CATEGORY"

    invalid_priority_indices = rng.sample(
        range(row_count),
        max(1, int(row_count * 0.01)),
    )
    tickets.loc[invalid_priority_indices, "priority"] = "UNKNOWN_PRIORITY"

    invalid_status_indices = rng.sample(
        range(row_count),
        max(1, int(row_count * 0.01)),
    )
    tickets.loc[invalid_status_indices, "ticket_status"] = "UNKNOWN_STATUS"

    invalid_channel_indices = rng.sample(
        range(row_count),
        max(1, int(row_count * 0.01)),
    )
    tickets.loc[invalid_channel_indices, "resolution_channel"] = "UNKNOWN_CHANNEL"

    invalid_team_indices = rng.sample(
        range(row_count),
        max(1, int(row_count * 0.01)),
    )
    tickets.loc[invalid_team_indices, "assigned_team"] = "UNKNOWN_TEAM"

    # Invalid negative resolution times.
    invalid_resolution_indices = rng.sample(
        range(row_count),
        max(1, int(row_count * 0.01)),
    )
    tickets.loc[
        invalid_resolution_indices,
        "resolution_time_hours",
    ] = -5.0

    # Implausibly large resolution times.
    large_resolution_indices = rng.sample(
        range(row_count),
        max(1, int(row_count * 0.005)),
    )
    tickets.loc[
        large_resolution_indices,
        "resolution_time_hours",
    ] = 10000.0

    # Resolved/closed tickets missing resolution time.
    resolved_indices = tickets.index[tickets["ticket_status"].isin(["RESOLVED", "CLOSED"])].tolist()

    if resolved_indices:
        missing_resolution_count = max(1, int(row_count * 0.005))
        missing_resolution_count = min(
            missing_resolution_count,
            len(resolved_indices),
        )
        selected = rng.sample(resolved_indices, missing_resolution_count)
        tickets.loc[selected, "resolution_time_hours"] = None

    # Open/in-progress tickets with a populated resolution time.
    open_indices = tickets.index[tickets["ticket_status"].isin(["OPEN", "IN_PROGRESS"])].tolist()

    if open_indices:
        inconsistent_count = max(1, int(row_count * 0.005))
        inconsistent_count = min(inconsistent_count, len(open_indices))
        selected = rng.sample(open_indices, inconsistent_count)
        tickets.loc[selected, "resolution_time_hours"] = [
            round(rng.uniform(1.0, 48.0), 2) for _ in selected
        ]

    # Invalid satisfaction scores.
    satisfaction_indices = rng.sample(
        range(row_count),
        max(1, int(row_count * 0.01)),
    )
    tickets.loc[
        satisfaction_indices,
        "customer_satisfaction_score",
    ] = 0

    # Timestamp inconsistencies.
    timestamp_indices = rng.sample(
        range(row_count),
        max(1, int(row_count * 0.005)),
    )
    tickets.loc[timestamp_indices, "ticket_updated_at"] = tickets.loc[
        timestamp_indices, "ticket_created_at"
    ] - pd.to_timedelta(
        rng.randint(1, 24),
        unit="h",
    )

    # Delayed source updates.
    delayed_indices = rng.sample(
        range(row_count),
        max(1, int(row_count * 0.01)),
    )
    tickets.loc[delayed_indices, "ticket_updated_at"] = tickets.loc[
        delayed_indices, "ticket_updated_at"
    ] + pd.Timedelta(
        rng.randint(3, 10),
        unit="D",
    )

    # Duplicate complete records while preserving target volume.
    duplicate_count = max(1, int(row_count * 0.01))
    base_count = row_count - duplicate_count

    duplicate_indices = rng.sample(
        range(base_count),
        duplicate_count,
    )

    duplicate_rows = tickets.iloc[duplicate_indices].copy()

    tickets = pd.concat(
        [
            tickets.iloc[:base_count],
            duplicate_rows,
        ],
        ignore_index=True,
    )

    return tickets
