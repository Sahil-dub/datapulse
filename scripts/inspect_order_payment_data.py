from pathlib import Path

import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.sources.customers import generate_customers
from datapulse.data_generation.sources.orders import generate_orders
from datapulse.data_generation.sources.payments import generate_payments
from datapulse.data_generation.sources.products import generate_products


def main() -> None:
    config = DataGenerationConfig(
        output_dir=Path("data/generated"),
    )

    print("Generating full-scale synthetic source data...")

    customers = generate_customers(config)
    products = generate_products(config)
    orders = generate_orders(
        config,
        customers=customers,
        products=products,
    )
    payments = generate_payments(
        config,
        orders=orders,
    )

    print("\n=== ROW COUNTS ===")
    print(f"Customers: {len(customers):,}")
    print(f"Products: {len(products):,}")
    print(f"Orders: {len(orders):,}")
    print(f"Payments: {len(payments):,}")

    valid_customer_ids = set(customers["customer_id"].dropna())
    valid_product_ids = set(products["product_id"].dropna())
    valid_order_ids = set(orders["order_id"].dropna())

    invalid_customer_refs = (
        orders["customer_id"].notna() & ~orders["customer_id"].isin(valid_customer_ids)
    ).sum()

    missing_customer_refs = orders["customer_id"].isna().sum()

    invalid_product_refs = (
        orders["product_id"].notna() & ~orders["product_id"].isin(valid_product_ids)
    ).sum()

    missing_product_refs = orders["product_id"].isna().sum()

    invalid_order_refs_in_payments = (~payments["order_id"].isin(valid_order_ids)).sum()

    duplicate_order_ids = orders["order_id"].duplicated(keep=False).sum()
    duplicate_payment_ids = payments["payment_id"].duplicated(keep=False).sum()

    invalid_quantities = (orders["quantity"] <= 0).sum()

    invalid_unit_prices = (orders["unit_price"] < 0).sum()

    calculated_order_total = (
        orders["quantity"] * orders["unit_price"]
        - orders["discount_amount"]
        + orders["shipping_amount"]
    )

    incorrect_order_totals = ((orders["order_total"] - calculated_order_total).abs() > 0.01).sum()

    valid_order_statuses = {
        "PENDING",
        "CONFIRMED",
        "SHIPPED",
        "DELIVERED",
        "CANCELLED",
        "RETURNED",
    }

    invalid_order_statuses = (~orders["order_status"].isin(valid_order_statuses)).sum()

    invalid_payment_amounts = (payments["payment_amount"] < 0).sum()

    valid_payment_statuses = {
        "PENDING",
        "AUTHORIZED",
        "CAPTURED",
        "FAILED",
        "REFUNDED",
        "CANCELLED",
    }

    invalid_payment_statuses = (~payments["payment_status"].isin(valid_payment_statuses)).sum()

    captured_zero_amount = (
        (payments["payment_status"] == "CAPTURED") & (payments["payment_amount"] == 0)
    ).sum()

    payment_latency = payments["source_updated_at"] - payments["payment_date"]

    delayed_payment_records = (payment_latency >= pd.Timedelta(2, unit="D")).sum()

    print("\n=== ORDER DATA QUALITY SIGNALS ===")
    print(f"Duplicate order IDs: {duplicate_order_ids:,}")
    print(f"Missing customer references: {missing_customer_refs:,}")
    print(f"Invalid customer references: {invalid_customer_refs:,}")
    print(f"Missing product references: {missing_product_refs:,}")
    print(f"Invalid product references: {invalid_product_refs:,}")
    print(f"Invalid quantities: {invalid_quantities:,}")
    print(f"Invalid unit prices: {invalid_unit_prices:,}")
    print(f"Incorrect order totals: {incorrect_order_totals:,}")
    print(f"Invalid order statuses: {invalid_order_statuses:,}")

    print("\n=== PAYMENT DATA QUALITY SIGNALS ===")
    print(f"Duplicate payment IDs: {duplicate_payment_ids:,}")
    print(f"Payments with unmatched order references: {invalid_order_refs_in_payments:,}")
    print(f"Invalid payment amounts: {invalid_payment_amounts:,}")
    print(f"Invalid payment statuses: {invalid_payment_statuses:,}")
    print(f"Captured payments with zero amount: {captured_zero_amount:,}")
    print(f"Delayed payment records (>= 2 days): {delayed_payment_records:,}")

    print("\n=== ORDER STATUS DISTRIBUTION ===")
    print(orders["order_status"].value_counts(dropna=False).to_string())

    print("\n=== PAYMENT STATUS DISTRIBUTION ===")
    print(payments["payment_status"].value_counts(dropna=False).to_string())

    print("\n=== PAYMENT METHOD DISTRIBUTION ===")
    print(payments["payment_method"].value_counts(dropna=False).to_string())

    print("\nInspection complete.")


if __name__ == "__main__":
    main()
