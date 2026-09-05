import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.utils import (
    create_rng,
    generate_id,
    random_choice,
    random_date,
)

FIRST_NAMES = [
    "Anna",
    "Daniel",
    "Emma",
    "Felix",
    "Hannah",
    "Jonas",
    "Laura",
    "Lukas",
    "Marie",
    "Max",
    "Mia",
    "Noah",
    "Paul",
    "Sophie",
    "Thomas",
]

LAST_NAMES = [
    "Becker",
    "Fischer",
    "Hoffmann",
    "Keller",
    "Klein",
    "Koch",
    "Krüger",
    "Lange",
    "Lehmann",
    "Meyer",
    "Richter",
    "Schmidt",
    "Schneider",
    "Schulz",
    "Wagner",
]

COUNTRIES = [
    "Germany",
    "Austria",
    "Switzerland",
    "France",
    "Netherlands",
    "Belgium",
    "Poland",
    "Spain",
    "Italy",
    "Denmark",
]

CUSTOMER_STATUSES = [
    "active",
    "inactive",
    "suspended",
]

ACQUISITION_CHANNELS = [
    "organic_search",
    "paid_search",
    "social",
    "email",
    "referral",
    "direct",
]


def generate_customers(
    config: DataGenerationConfig,
) -> pd.DataFrame:
    """Generate a deterministic synthetic customer source dataset."""

    rng = create_rng(config.seed)

    records: list[dict[str, object]] = []

    for _ in range(config.customers_count):
        first_name = random_choice(rng, FIRST_NAMES)
        last_name = random_choice(rng, LAST_NAMES)

        customer_id = generate_id(rng)

        records.append(
            {
                "customer_id": customer_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": (
                    f"{first_name.lower()}.{last_name.lower()}.{customer_id[:8]}@example.com"
                ),
                "country": random_choice(rng, COUNTRIES),
                "signup_date": random_date(
                    rng,
                    config.start_date,
                    config.end_date,
                ),
                "customer_status": random_choice(
                    rng,
                    CUSTOMER_STATUSES,
                ),
                "acquisition_channel": random_choice(
                    rng,
                    ACQUISITION_CHANNELS,
                ),
            }
        )

    customers = pd.DataFrame(records)

    return _introduce_customer_quality_issues(
        customers,
        config,
    )


def _introduce_customer_quality_issues(
    customers: pd.DataFrame,
    config: DataGenerationConfig,
) -> pd.DataFrame:
    """Introduce controlled source-system quality issues."""

    if customers.empty:
        return customers

    rng = create_rng(config.seed + 1)
    result = customers.copy()

    # Duplicate a small number of existing source records.
    duplicate_count = min(
        max(1, len(result) // 100),
        len(result),
    )

    duplicate_indices = rng.sample(
        range(len(result)),
        duplicate_count,
    )

    duplicates = result.iloc[duplicate_indices].copy()

    # Introduce missing and invalid values into selected records.
    issue_count = min(
        max(1, len(result) // 200),
        len(result),
    )

    issue_indices = rng.sample(
        range(len(result)),
        issue_count,
    )

    result.loc[issue_indices, "email"] = None

    invalid_country_count = min(
        max(1, len(result) // 500),
        len(result),
    )

    invalid_country_indices = rng.sample(
        range(len(result)),
        invalid_country_count,
    )

    result.loc[
        invalid_country_indices,
        "country",
    ] = "UNKNOWN_COUNTRY"

    result = pd.concat(
        [result, duplicates],
        ignore_index=True,
    )

    return result


def expected_customer_columns() -> list[str]:
    """Return the expected customer source columns."""

    return [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "country",
        "signup_date",
        "customer_status",
        "acquisition_channel",
    ]
