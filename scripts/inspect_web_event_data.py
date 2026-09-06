from __future__ import annotations

import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.sources.customers import generate_customers
from datapulse.data_generation.sources.orders import generate_orders
from datapulse.data_generation.sources.products import generate_products
from datapulse.data_generation.sources.web_events import generate_web_events


def main() -> None:
    config = DataGenerationConfig()

    print("Generating full-scale synthetic customer, product, order, and web-event data...")

    customers = generate_customers(config)
    products = generate_products(config)
    orders = generate_orders(config, customers, products)
    events = generate_web_events(
        config,
        customers,
        products,
        orders,
    )

    print("\n=== ROW COUNTS ===")
    print(f"Customers: {len(customers):,}")
    print(f"Products: {len(products):,}")
    print(f"Orders: {len(orders):,}")
    print(f"Web events: {len(events):,}")

    print("\n=== WEB EVENT DATA QUALITY SIGNALS ===")

    print(
        "Duplicate event IDs:",
        events["event_id"].duplicated().sum(),
    )

    print(
        "Missing customer references:",
        events["customer_id"].isna().sum(),
    )

    print(
        "Invalid customer references:",
        (events["customer_id"] == "INVALID_CUSTOMER").sum(),
    )

    print(
        "Invalid product references:",
        (events["product_id"] == "INVALID_PRODUCT").sum(),
    )

    print(
        "Invalid order references:",
        (events["order_id"] == "INVALID_ORDER").sum(),
    )

    print(
        "Invalid event types:",
        (
            ~events["event_type"].isin(
                {
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
                }
            )
        ).sum(),
    )

    print(
        "Invalid page types:",
        (
            ~events["page_type"].isin(
                {
                    "HOME",
                    "PRODUCT",
                    "SEARCH",
                    "CART",
                    "CHECKOUT",
                    "ACCOUNT",
                    "ORDER_CONFIRMATION",
                }
            )
        ).sum(),
    )

    print(
        "Invalid device types:",
        (
            ~events["device_type"].isin(
                {
                    "DESKTOP",
                    "MOBILE",
                    "TABLET",
                }
            )
        ).sum(),
    )

    print(
        "Invalid traffic sources:",
        (
            ~events["traffic_source"].isin(
                {
                    "ORGANIC",
                    "PAID_SEARCH",
                    "SOCIAL",
                    "EMAIL",
                    "DIRECT",
                    "REFERRAL",
                }
            )
        ).sum(),
    )

    print(
        "Malformed session IDs:",
        (events["session_id"].fillna("") == "").sum(),
    )

    print(
        "Negative revenue:",
        (events["revenue_amount"] < 0).sum(),
    )

    purchase_events = events["event_type"] == "PURCHASE"

    print(
        "Purchase events with zero/missing revenue:",
        (
            purchase_events & (events["revenue_amount"].isna() | (events["revenue_amount"] <= 0))
        ).sum(),
    )

    non_purchase_events = ~purchase_events

    print(
        "Non-purchase events with revenue:",
        (
            non_purchase_events & events["revenue_amount"].notna() & (events["revenue_amount"] > 0)
        ).sum(),
    )

    print(
        "Source received before event:",
        (events["source_received_at"] < events["event_timestamp"]).sum(),
    )

    delay = events["source_received_at"] - events["event_timestamp"]

    print(
        "Delayed source records (>= 3 days):",
        (delay >= pd.Timedelta(3, unit="D")).sum(),
    )

    print("\n=== EVENT TYPE DISTRIBUTION ===")
    print(events["event_type"].value_counts().to_string())

    print("\n=== PAGE TYPE DISTRIBUTION ===")
    print(events["page_type"].value_counts().to_string())

    print("\n=== DEVICE DISTRIBUTION ===")
    print(events["device_type"].value_counts().to_string())

    print("\n=== TRAFFIC SOURCE DISTRIBUTION ===")
    print(events["traffic_source"].value_counts().to_string())

    print("\n=== SESSION STATISTICS ===")
    events_per_session = events.groupby("session_id").size()

    print(f"Unique sessions: {events['session_id'].nunique():,}")
    print(f"Average events/session: {events_per_session.mean():.2f}")
    print(f"Median events/session: {events_per_session.median():.2f}")
    print(f"Maximum events/session: {events_per_session.max():,}")

    print("\n=== DAILY EVENT VOLUME ===")
    daily_volume = (
        events.assign(event_date=pd.to_datetime(events["event_timestamp"]).dt.date)
        .groupby("event_date")
        .size()
    )

    print(f"Days represented: {daily_volume.size:,}")
    print(f"Median daily events: {daily_volume.median():,.0f}")
    print(f"Maximum daily events: {daily_volume.max():,.0f}")
    print(f"Maximum/median daily volume ratio: {daily_volume.max() / daily_volume.median():.2f}x")

    print("\nInspection complete.")


if __name__ == "__main__":
    main()
