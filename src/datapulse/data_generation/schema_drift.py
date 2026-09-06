from __future__ import annotations

import pandas as pd


def apply_customer_email_rename(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Simulate an upstream rename of the customer email column."""
    if "email" not in dataframe.columns:
        raise ValueError("Customer schema drift requires an 'email' column.")

    drifted = dataframe.copy()
    drifted = drifted.rename(columns={"email": "email_address"})

    return drifted


def apply_product_add_brand(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Simulate an upstream additive schema change by adding a brand column."""
    if "product_id" not in dataframe.columns:
        raise ValueError("Product schema drift requires a 'product_id' column.")

    drifted = dataframe.copy()
    drifted["brand"] = "SYNTHETIC_BRAND"

    return drifted


def apply_order_remove_shipping_amount(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Simulate an upstream breaking change that removes shipping_amount."""
    if "shipping_amount" not in dataframe.columns:
        raise ValueError("Order schema drift requires a 'shipping_amount' column.")

    drifted = dataframe.copy()
    drifted = drifted.drop(columns=["shipping_amount"])

    return drifted
