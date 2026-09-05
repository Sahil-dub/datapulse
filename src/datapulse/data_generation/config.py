from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class DataGenerationConfig:
    """Configuration for reproducible synthetic data generation."""

    seed: int = 42

    start_date: date = date(2025, 1, 1)
    end_date: date = date(2026, 6, 30)

    output_dir: Path = Path("data/generated")

    customers_count: int = 5_000
    products_count: int = 250
    orders_count: int = 50_000
    payments_count: int = 55_000
    subscriptions_count: int = 7_500
    support_tickets_count: int = 15_000
    web_events_count: int = 300_000

    def __post_init__(self) -> None:
        """Validate configuration values."""

        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date.")

        if self.seed < 0:
            raise ValueError("seed must be non-negative.")

        counts = {
            "customers_count": self.customers_count,
            "products_count": self.products_count,
            "orders_count": self.orders_count,
            "payments_count": self.payments_count,
            "subscriptions_count": self.subscriptions_count,
            "support_tickets_count": self.support_tickets_count,
            "web_events_count": self.web_events_count,
        }

        for name, count in counts.items():
            if count < 0:
                raise ValueError(f"{name} must be non-negative.")
