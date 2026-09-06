import pytest

from datapulse.data_generation.schema_drift_config import (
    CUSTOMER_EMAIL_RENAME,
    ORDER_REMOVE_SHIPPING_AMOUNT,
    PRODUCT_ADD_BRAND,
    SUPPORTED_SCHEMA_DRIFT_SCENARIOS,
    SchemaDriftConfig,
)


def test_disabled_configuration_has_no_scenarios() -> None:
    config = SchemaDriftConfig()

    assert config.enabled is False
    assert config.scenarios == ()


def test_supported_scenarios_are_centralized() -> None:
    assert SUPPORTED_SCHEMA_DRIFT_SCENARIOS == {
        CUSTOMER_EMAIL_RENAME,
        PRODUCT_ADD_BRAND,
        ORDER_REMOVE_SHIPPING_AMOUNT,
    }


def test_enabled_configuration_accepts_supported_scenarios() -> None:
    config = SchemaDriftConfig(
        enabled=True,
        scenarios=(
            CUSTOMER_EMAIL_RENAME,
            PRODUCT_ADD_BRAND,
        ),
    )

    assert config.enabled is True
    assert config.scenarios == (
        CUSTOMER_EMAIL_RENAME,
        PRODUCT_ADD_BRAND,
    )


def test_unknown_scenario_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported schema drift scenario",
    ):
        SchemaDriftConfig(
            enabled=True,
            scenarios=("unknown_scenario",),
        )


def test_duplicate_scenarios_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="must not contain duplicates",
    ):
        SchemaDriftConfig(
            enabled=True,
            scenarios=(
                CUSTOMER_EMAIL_RENAME,
                CUSTOMER_EMAIL_RENAME,
            ),
        )


def test_scenarios_cannot_be_configured_when_disabled() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be configured when drift is disabled",
    ):
        SchemaDriftConfig(
            enabled=False,
            scenarios=(ORDER_REMOVE_SHIPPING_AMOUNT,),
        )


def test_configuration_is_immutable() -> None:
    config = SchemaDriftConfig(
        enabled=True,
        scenarios=(PRODUCT_ADD_BRAND,),
    )

    with pytest.raises(AttributeError):
        config.enabled = False
