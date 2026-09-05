import random
import uuid
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


def create_rng(seed: int) -> random.Random:
    """Create a deterministic random number generator."""

    if seed < 0:
        raise ValueError("seed must be non-negative.")

    return random.Random(seed)


def random_date(
    rng: random.Random,
    start_date: date,
    end_date: date,
) -> date:
    """Generate a deterministic random date within an inclusive range."""

    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date.")

    day_range = (end_date - start_date).days

    return start_date + timedelta(
        days=rng.randint(0, day_range),
    )


def random_choice[T](
    rng: random.Random,
    values: Sequence[T],
) -> T:
    """Select one value deterministically from a sequence."""

    if not values:
        raise ValueError("values must not be empty.")

    return rng.choice(values)


def generate_id(rng: random.Random) -> str:
    """Generate a deterministic UUID string using the supplied RNG."""

    random_bytes = bytes(rng.getrandbits(8) for _ in range(16))

    generated_uuid = uuid.UUID(bytes=random_bytes)

    return str(generated_uuid)


def ensure_directory(path: Path) -> Path:
    """Create a directory if it does not already exist."""

    path.mkdir(parents=True, exist_ok=True)

    return path
