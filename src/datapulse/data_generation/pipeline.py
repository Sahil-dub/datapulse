from pathlib import Path

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.materialization import write_source_csv
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

    for source_name, dataframe in datasets.items():
        output_path = Path(config.output_dir) / source_name / f"{source_name}.csv"
        output_paths[source_name] = write_source_csv(
            dataframe,
            output_path,
        )

    return output_paths
