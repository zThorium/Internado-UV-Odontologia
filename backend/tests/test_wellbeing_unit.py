import pytest

from app.services.wellbeing import _evaluate_alert


pytestmark = pytest.mark.unit


def test_evaluate_alert_requires_at_least_two_weeks():
    assert _evaluate_alert(["good"]) is None


def test_evaluate_alert_returns_red_for_two_consecutive_difficult():
    assert _evaluate_alert(["difficult", "difficult", "good"]) == "red"


def test_evaluate_alert_returns_red_for_three_difficult_in_last_five():
    recent = ["regular", "difficult", "good", "difficult", "difficult"]
    assert _evaluate_alert(recent) == "red"


def test_evaluate_alert_returns_yellow_for_two_consecutive_regular_or_difficult():
    assert _evaluate_alert(["regular", "difficult", "good"]) == "yellow"


def test_evaluate_alert_returns_none_when_trend_is_healthy():
    assert _evaluate_alert(["good", "regular", "good"]) is None
