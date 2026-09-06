from __future__ import annotations

import random
from datetime import datetime, timedelta

import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.utils import generate_id

EVENT_TYPES = [
    "PAGE_VIEW",
    "PRODUCT_VIEW",
    "SEARCH",
    "ADD_TO_CART",
    "REMOVE_FROM_CART",
    "CHECKOUT_STARTED",
    "PURCHASE",
    "SIGNUP",
    "LOGIN",
    "LOGOUT",
]

PAGE_TYPES = [
    "HOME",
    "PRODUCT",
    "SEARCH",
    "CART",
    "CHECKOUT",
    "ACCOUNT",
    "ORDER_CONFIRMATION",
]

DEVICE_TYPES = [
    "DESKTOP",
    "MOBILE",
    "TABLET",
]

TRAFFIC_SOURCES = [
    "ORGANIC",
    "PAID_SEARCH",
    "SOCIAL",
    "EMAIL",
    "DIRECT",
    "REFERRAL",
]

EXPECTED_EVENT_COLUMNS = [
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


def expected_web_event_columns() -> list[str]:
    """Return the expected Web Events source-system columns."""
    return EXPECTED_EVENT_COLUMNS.copy()


def _random_timestamp(
    rng: random.Random,
    start: datetime,
    end: datetime,
) -> datetime:
    """Generate a deterministic random timestamp within the configured range."""
    total_seconds = int((end - start).total_seconds())
    offset_seconds = rng.randint(0, total_seconds)
    return start + timedelta(seconds=offset_seconds)


def _choose_event_type(rng: random.Random) -> str:
    """Choose an event type using a realistic business distribution."""
    weights = [
        0.32,  # PAGE_VIEW
        0.20,  # PRODUCT_VIEW
        0.08,  # SEARCH
        0.08,  # ADD_TO_CART
        0.03,  # REMOVE_FROM_CART
        0.05,  # CHECKOUT_STARTED
        0.03,  # PURCHASE
        0.04,  # SIGNUP
        0.10,  # LOGIN
        0.07,  # LOGOUT
    ]

    return rng.choices(EVENT_TYPES, weights=weights, k=1)[0]


def _page_type_for_event(rng: random.Random, event_type: str) -> str:
    """Generate a page type consistent with the event."""
    mapping = {
        "PAGE_VIEW": PAGE_TYPES,
        "PRODUCT_VIEW": ["PRODUCT"],
        "SEARCH": ["SEARCH"],
        "ADD_TO_CART": ["PRODUCT"],
        "REMOVE_FROM_CART": ["CART", "PRODUCT"],
        "CHECKOUT_STARTED": ["CHECKOUT"],
        "PURCHASE": ["ORDER_CONFIRMATION"],
        "SIGNUP": ["ACCOUNT"],
        "LOGIN": ["ACCOUNT"],
        "LOGOUT": ["ACCOUNT"],
    }

    return rng.choice(mapping[event_type])


def _customer_id_for_event(
    rng: random.Random,
    customer_ids: list[str],
    event_type: str,
) -> str | None:
    """Assign authenticated or anonymous customer context."""
    if event_type in {"SIGNUP", "PAGE_VIEW", "SEARCH"}:
        if rng.random() < 0.50:
            return None

    if rng.random() < 0.15:
        return None

    return rng.choice(customer_ids)


def _product_id_for_event(
    rng: random.Random,
    product_ids: list[str],
    event_type: str,
) -> str | None:
    """Assign a product when the event naturally relates to one."""
    if event_type not in {
        "PRODUCT_VIEW",
        "ADD_TO_CART",
        "REMOVE_FROM_CART",
    }:
        return None

    return rng.choice(product_ids)


def _order_id_for_event(
    rng: random.Random,
    order_ids: list[str],
    event_type: str,
) -> str | None:
    """Assign an order to checkout and purchase events."""
    if event_type not in {"CHECKOUT_STARTED", "PURCHASE"}:
        return None

    return rng.choice(order_ids)


def _revenue_for_event(
    rng: random.Random,
    event_type: str,
) -> float | None:
    """Generate revenue only for purchase events."""
    if event_type != "PURCHASE":
        return None

    return round(rng.uniform(10.0, 500.0), 2)


def _inject_duplicates(
    df: pd.DataFrame,
    rng: random.Random,
    duplicate_rate: float = 0.01,
) -> pd.DataFrame:
    """Replace rows with duplicated complete records while preserving volume."""
    duplicate_count = max(1, int(len(df) * duplicate_rate))

    source_count = len(df) - duplicate_count
    source_indices = rng.sample(range(source_count), duplicate_count)

    duplicated_rows = df.iloc[source_indices].copy()

    result = pd.concat(
        [
            df.iloc[:source_count].copy(),
            duplicated_rows,
        ],
        ignore_index=True,
    )

    return result


def _inject_spike(
    df: pd.DataFrame,
    rng: random.Random,
    start_date: datetime,
) -> pd.DataFrame:
    """Create a deterministic abnormal event-volume spike on one day."""
    spike_count = max(1, int(len(df) * 0.005))

    spike_date = start_date + timedelta(days=400)

    indices = rng.sample(range(len(df)), spike_count)

    for index in indices:
        original_timestamp = df.at[index, "event_timestamp"]

        seconds_since_midnight = (
            original_timestamp.hour * 3600
            + original_timestamp.minute * 60
            + original_timestamp.second
        )

        df.at[index, "event_timestamp"] = spike_date + timedelta(
            seconds=seconds_since_midnight,
        )

    return df


def generate_web_events(
    config: DataGenerationConfig,
    customers: pd.DataFrame,
    products: pd.DataFrame,
    orders: pd.DataFrame,
) -> pd.DataFrame:
    """Generate deterministic synthetic Web Events source-system data."""
    rng = random.Random(config.seed + 600)

    customer_ids = customers["customer_id"].dropna().astype(str).tolist()
    product_ids = products["product_id"].dropna().astype(str).tolist()
    order_ids = orders["order_id"].dropna().astype(str).tolist()

    start_datetime = datetime.combine(config.start_date, datetime.min.time())
    end_datetime = datetime.combine(config.end_date, datetime.max.time())

    rows: list[dict[str, object]] = []

    session_count = max(1, int(config.web_events_count * 0.20))
    session_ids = [generate_id(rng) for _ in range(session_count)]

    for _ in range(config.web_events_count):
        event_type = _choose_event_type(rng)
        event_timestamp = _random_timestamp(
            rng,
            start_datetime,
            end_datetime,
        )

        customer_id = _customer_id_for_event(
            rng,
            customer_ids,
            event_type,
        )

        product_id = _product_id_for_event(
            rng,
            product_ids,
            event_type,
        )

        order_id = _order_id_for_event(
            rng,
            order_ids,
            event_type,
        )

        revenue_amount = _revenue_for_event(
            rng,
            event_type,
        )

        source_delay_hours = rng.randint(0, 48)
        source_received_at = event_timestamp + timedelta(
            hours=source_delay_hours,
        )

        rows.append(
            {
                "event_id": generate_id(rng),
                "event_timestamp": event_timestamp,
                "source_received_at": source_received_at,
                "session_id": rng.choice(session_ids),
                "customer_id": customer_id,
                "event_type": event_type,
                "page_type": _page_type_for_event(rng, event_type),
                "device_type": rng.choice(DEVICE_TYPES),
                "traffic_source": rng.choice(TRAFFIC_SOURCES),
                "product_id": product_id,
                "order_id": order_id,
                "revenue_amount": revenue_amount,
            }
        )

    df = pd.DataFrame(rows, columns=EXPECTED_EVENT_COLUMNS)

    # Intentional source-system defects.

    row_count = len(df)

    # Missing customer references.
    missing_customer_count = max(1, int(row_count * 0.005))
    missing_customer_indices = rng.sample(
        range(row_count),
        missing_customer_count,
    )

    for index in missing_customer_indices:
        if pd.notna(df.at[index, "customer_id"]):
            df.at[index, "customer_id"] = None

    # Invalid customer references.
    invalid_customer_count = max(1, int(row_count * 0.005))
    invalid_customer_indices = rng.sample(
        range(row_count),
        invalid_customer_count,
    )

    for index in invalid_customer_indices:
        df.at[index, "customer_id"] = "INVALID_CUSTOMER"

    # Invalid product references.
    invalid_product_count = max(1, int(row_count * 0.003))
    invalid_product_indices = rng.sample(
        range(row_count),
        invalid_product_count,
    )

    for index in invalid_product_indices:
        df.at[index, "product_id"] = "INVALID_PRODUCT"

    # Invalid order references.
    invalid_order_count = max(1, int(row_count * 0.003))
    invalid_order_indices = rng.sample(
        range(row_count),
        invalid_order_count,
    )

    for index in invalid_order_indices:
        df.at[index, "order_id"] = "INVALID_ORDER"

    # Invalid categorical values.
    invalid_event_count = max(1, int(row_count * 0.003))
    invalid_event_indices = rng.sample(
        range(row_count),
        invalid_event_count,
    )

    for index in invalid_event_indices:
        df.at[index, "event_type"] = "UNKNOWN_EVENT"

    invalid_device_indices = rng.sample(
        range(row_count),
        invalid_event_count,
    )

    for index in invalid_device_indices:
        df.at[index, "device_type"] = "UNKNOWN_DEVICE"

    invalid_source_indices = rng.sample(
        range(row_count),
        invalid_event_count,
    )

    for index in invalid_source_indices:
        df.at[index, "traffic_source"] = "UNKNOWN_SOURCE"

    invalid_page_indices = rng.sample(
        range(row_count),
        invalid_event_count,
    )

    for index in invalid_page_indices:
        df.at[index, "page_type"] = "UNKNOWN_PAGE"

    # Malformed session IDs.
    malformed_session_count = max(1, int(row_count * 0.002))
    malformed_session_indices = rng.sample(
        range(row_count),
        malformed_session_count,
    )

    for index in malformed_session_indices:
        df.at[index, "session_id"] = ""

    # Negative revenue.
    negative_revenue_count = max(1, int(row_count * 0.002))
    negative_revenue_indices = rng.sample(
        range(row_count),
        negative_revenue_count,
    )

    for index in negative_revenue_indices:
        df.at[index, "revenue_amount"] = -abs(
            round(rng.uniform(5.0, 200.0), 2),
        )

    # PURCHASE events with missing/zero revenue.
    purchase_indices = df.index[df["event_type"] == "PURCHASE"].tolist()

    if purchase_indices:
        affected_purchase_count = max(
            1,
            min(
                len(purchase_indices),
                int(row_count * 0.001),
            ),
        )

        affected_purchase_indices = rng.sample(
            purchase_indices,
            affected_purchase_count,
        )

        for index in affected_purchase_indices:
            df.at[index, "revenue_amount"] = 0.0

    # Non-purchase events with revenue.
    non_purchase_indices = df.index[df["event_type"] != "PURCHASE"].tolist()

    positive_revenue_count = max(1, int(row_count * 0.001))
    affected_non_purchase_indices = rng.sample(
        non_purchase_indices,
        min(positive_revenue_count, len(non_purchase_indices)),
    )

    for index in affected_non_purchase_indices:
        df.at[index, "revenue_amount"] = round(
            rng.uniform(5.0, 100.0),
            2,
        )

    # Invalid timestamps: source receipt before event occurrence.
    invalid_timestamp_count = max(1, int(row_count * 0.002))
    invalid_timestamp_indices = rng.sample(
        range(row_count),
        invalid_timestamp_count,
    )

    for index in invalid_timestamp_indices:
        event_timestamp = df.at[index, "event_timestamp"]
        df.at[index, "source_received_at"] = event_timestamp - timedelta(hours=rng.randint(1, 24))

    # Additional delayed source records.
    delayed_count = max(1, int(row_count * 0.003))
    delayed_indices = rng.sample(
        range(row_count),
        delayed_count,
    )

    for index in delayed_indices:
        event_timestamp = df.at[index, "event_timestamp"]
        df.at[index, "source_received_at"] = event_timestamp + timedelta(days=rng.randint(3, 7))

    # Abnormal event-volume spike.
    df = _inject_spike(
        df,
        rng,
        start_datetime,
    )

    # Duplicate complete event records.
    df = _inject_duplicates(
        df,
        rng,
    )

    return df
