from __future__ import annotations

from dataclasses import dataclass

CUSTOMER_EMAIL_RENAME = "customer_email_rename"
PRODUCT_ADD_BRAND = "product_add_brand"
ORDER_REMOVE_SHIPPING_AMOUNT = "order_remove_shipping_amount"

SUPPORTED_SCHEMA_DRIFT_SCENARIOS = frozenset(
    {
        CUSTOMER_EMAIL_RENAME,
        PRODUCT_ADD_BRAND,
        ORDER_REMOVE_SHIPPING_AMOUNT,
    }
)


@dataclass(frozen=True)
class SchemaDriftConfig:
    """Configuration for deterministic, opt-in source schema drift."""

    enabled: bool = False
    scenarios: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        scenarios = tuple(self.scenarios)

        unknown_scenarios = set(scenarios) - SUPPORTED_SCHEMA_DRIFT_SCENARIOS
        if unknown_scenarios:
            unknown = ", ".join(sorted(unknown_scenarios))
            raise ValueError(f"Unsupported schema drift scenario(s): {unknown}")

        if len(scenarios) != len(set(scenarios)):
            raise ValueError("Schema drift scenarios must not contain duplicates.")

        if not self.enabled and scenarios:
            raise ValueError("Schema drift scenarios cannot be configured when drift is disabled.")
