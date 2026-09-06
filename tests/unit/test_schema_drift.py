import pandas as pd
import pytest

from datapulse.data_generation.schema_drift import (
    apply_customer_email_rename,
    apply_order_remove_shipping_amount,
    apply_product_add_brand,
)


def test_customer_email_rename_preserves_values():
    dataframe = pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "email": ["a@example.com", "b@example.com"],
        }
    )

    drifted = apply_customer_email_rename(dataframe)

    assert "email" not in drifted.columns
    assert "email_address" in drifted.columns
    assert drifted["email_address"].tolist() == [
        "a@example.com",
        "b@example.com",
    ]
    assert list(dataframe.columns) == ["customer_id", "email"]


def test_product_add_brand_preserves_existing_columns():
    dataframe = pd.DataFrame(
        {
            "product_id": ["p1", "p2"],
            "product_name": ["Product 1", "Product 2"],
            "unit_price": [10.0, 20.0],
        }
    )

    drifted = apply_product_add_brand(dataframe)

    assert list(drifted.columns) == [
        "product_id",
        "product_name",
        "unit_price",
        "brand",
    ]
    assert drifted["brand"].tolist() == [
        "SYNTHETIC_BRAND",
        "SYNTHETIC_BRAND",
    ]
    assert list(dataframe.columns) == [
        "product_id",
        "product_name",
        "unit_price",
    ]


def test_order_remove_shipping_amount_preserves_other_columns():
    dataframe = pd.DataFrame(
        {
            "order_id": ["o1"],
            "order_total": [100.0],
            "shipping_amount": [5.0],
        }
    )

    drifted = apply_order_remove_shipping_amount(dataframe)

    assert "shipping_amount" not in drifted.columns
    assert drifted["order_id"].tolist() == ["o1"]
    assert drifted["order_total"].tolist() == [100.0]
    assert list(dataframe.columns) == [
        "order_id",
        "order_total",
        "shipping_amount",
    ]


@pytest.mark.parametrize(
    ("function", "dataframe", "expected_message"),
    [
        (
            apply_customer_email_rename,
            pd.DataFrame({"customer_id": ["c1"]}),
            "requires an 'email' column",
        ),
        (
            apply_product_add_brand,
            pd.DataFrame({"product_name": ["Product"]}),
            "requires a 'product_id' column",
        ),
        (
            apply_order_remove_shipping_amount,
            pd.DataFrame({"order_id": ["o1"]}),
            "requires a 'shipping_amount' column",
        ),
    ],
)
def test_schema_drift_requires_expected_source_column(
    function,
    dataframe,
    expected_message,
):
    with pytest.raises(ValueError, match=expected_message):
        function(dataframe)
