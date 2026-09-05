from datetime import date
from pathlib import Path

import pytest

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.utils import (
    create_rng,
    ensure_directory,
    generate_id,
    random_choice,
    random_date,
)


def test_config_has_expected_defaults() -> None:
    """The default configuration should match the Phase 2 design."""

    config = DataGenerationConfig()

    assert config.seed == 42
    assert config.start_date == date(2025, 1, 1)
    assert config.end_date == date(2026, 6, 30)
    assert config.output_dir == Path("data/generated")

    assert config.customers_count == 5_000
    assert config.products_count == 250
    assert config.orders_count == 50_000
    assert config.payments_count == 55_000
    assert config.subscriptions_count == 7_500
    assert config.support_tickets_count == 15_000
    assert config.web_events_count == 300_000


def test_config_rejects_invalid_date_range() -> None:
    """The configuration should reject an invalid date range."""

    with pytest.raises(ValueError, match="start_date"):
        DataGenerationConfig(
            start_date=date(2026, 1, 1),
            end_date=date(2025, 1, 1),
        )


def test_config_rejects_negative_seed() -> None:
    """The configuration should reject negative seeds."""

    with pytest.raises(ValueError, match="seed"):
        DataGenerationConfig(seed=-1)


def test_config_rejects_negative_record_count() -> None:
    """The configuration should reject negative record counts."""

    with pytest.raises(ValueError, match="customers_count"):
        DataGenerationConfig(customers_count=-1)


def test_rng_is_reproducible() -> None:
    """The same seed should produce the same random sequence."""

    rng_one = create_rng(42)
    rng_two = create_rng(42)

    values_one = [rng_one.random() for _ in range(10)]
    values_two = [rng_two.random() for _ in range(10)]

    assert values_one == values_two


def test_different_seeds_produce_different_sequences() -> None:
    """Different seeds should normally produce different sequences."""

    rng_one = create_rng(42)
    rng_two = create_rng(99)

    values_one = [rng_one.random() for _ in range(10)]
    values_two = [rng_two.random() for _ in range(10)]

    assert values_one != values_two


def test_random_date_stays_within_range() -> None:
    """Generated dates should remain inside the configured range."""

    rng = create_rng(42)

    start_date = date(2025, 1, 1)
    end_date = date(2025, 1, 31)

    generated_dates = [random_date(rng, start_date, end_date) for _ in range(100)]

    assert all(start_date <= value <= end_date for value in generated_dates)


def test_random_date_is_reproducible() -> None:
    """The same seed should generate the same dates."""

    start_date = date(2025, 1, 1)
    end_date = date(2025, 1, 31)

    rng_one = create_rng(42)
    rng_two = create_rng(42)

    dates_one = [random_date(rng_one, start_date, end_date) for _ in range(20)]

    dates_two = [random_date(rng_two, start_date, end_date) for _ in range(20)]

    assert dates_one == dates_two


def test_random_choice_returns_value_from_sequence() -> None:
    """Random choice should return one of the supplied values."""

    rng = create_rng(42)
    values = ["gold", "silver", "bronze"]

    result = random_choice(rng, values)

    assert result in values


def test_random_choice_rejects_empty_sequence() -> None:
    """Random choice should reject an empty sequence."""

    rng = create_rng(42)

    with pytest.raises(ValueError, match="must not be empty"):
        random_choice(rng, [])


def test_generate_id_is_reproducible() -> None:
    """IDs should be reproducible when using the same seed."""

    rng_one = create_rng(42)
    rng_two = create_rng(42)

    ids_one = [generate_id(rng_one) for _ in range(10)]
    ids_two = [generate_id(rng_two) for _ in range(10)]

    assert ids_one == ids_two


def test_generate_ids_are_unique_for_normal_generation() -> None:
    """Generated IDs should normally be unique."""

    rng = create_rng(42)

    generated_ids = {generate_id(rng) for _ in range(1_000)}

    assert len(generated_ids) == 1_000


def test_ensure_directory_creates_directory(tmp_path: Path) -> None:
    """The utility should create missing directories."""

    target_directory = tmp_path / "generated" / "customers"

    result = ensure_directory(target_directory)

    assert result == target_directory
    assert target_directory.exists()
    assert target_directory.is_dir()
