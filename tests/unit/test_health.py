from datapulse.health import get_health


def test_get_health_returns_ok_status() -> None:
    result = get_health()

    assert result["status"] == "ok"
    assert result["application"] == "DataPulse"
    assert result["environment"] == "development"
