from pathlib import Path

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.manifest import (
    build_source_manifest,
    build_source_manifest_entry,
    write_source_manifest,
)
from datapulse.data_generation.materialization import write_source_csv
from datapulse.data_generation.schema_drift import (
    apply_customer_email_rename,
    apply_order_remove_shipping_amount,
    apply_product_add_brand,
)
from datapulse.data_generation.schema_drift_config import (
    CUSTOMER_EMAIL_RENAME,
    ORDER_REMOVE_SHIPPING_AMOUNT,
    PRODUCT_ADD_BRAND,
    SchemaDriftConfig,
)
from datapulse.data_generation.sources import (
    generate_customers,
    generate_orders,
    generate_payments,
    generate_products,
    generate_subscriptions,
    generate_support_tickets,
    generate_web_events,
)


def materialize_all_sources(
    config: DataGenerationConfig,
    schema_drift_config: SchemaDriftConfig | None = None,
) -> dict[str, Path]:
    """Generate and materialize all synthetic source datasets.

    Sources are generated in dependency order so that downstream datasets
    can reference valid customer, product, and order identifiers.
    """
    customers = generate_customers(config)
    products = generate_products(config)
    orders = generate_orders(config, customers, products)
    payments = generate_payments(config, orders)
    subscriptions = generate_subscriptions(config, customers)
    support_tickets = generate_support_tickets(config, customers)
    web_events = generate_web_events(config, customers, products, orders)

    drift_config = schema_drift_config or SchemaDriftConfig()

    if drift_config.enabled:
        if CUSTOMER_EMAIL_RENAME in drift_config.scenarios:
            customers = apply_customer_email_rename(customers)

        if PRODUCT_ADD_BRAND in drift_config.scenarios:
            products = apply_product_add_brand(products)

        if ORDER_REMOVE_SHIPPING_AMOUNT in drift_config.scenarios:
            orders = apply_order_remove_shipping_amount(orders)

    datasets = {
        "customers": customers,
        "products": products,
        "orders": orders,
        "payments": payments,
        "subscriptions": subscriptions,
        "support_tickets": support_tickets,
        "web_events": web_events,
    }

    output_paths: dict[str, Path] = {}
    manifest_entries: list[dict[str, object]] = []

    for source_name, dataframe in datasets.items():
        output_path = Path(config.output_dir) / source_name / f"{source_name}.csv"

        output_paths[source_name] = write_source_csv(
            dataframe,
            output_path,
        )

        manifest_entries.append(
            build_source_manifest_entry(
                source_name=source_name,
                dataframe=dataframe,
                file_path=output_path,
            )
        )

    manifest = build_source_manifest(
        entries=manifest_entries,
        schema_drift_scenarios=drift_config.scenarios,
    )

    manifest_path = write_source_manifest(
        manifest,
        Path(config.output_dir) / "manifest.json",
    )

    output_paths["manifest"] = manifest_path

    return output_paths
