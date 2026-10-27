import pytest

from backend.app.models.report import FlagStatus
from backend.app.services.reference_ranges import (
    evaluate_reference_range,
    parse_reference_interval,
)


def test_parse_reference_interval_two_sided():
    interval = parse_reference_interval("13.5 - 17.5 g/dL")
    assert interval is not None
    assert interval.is_numeric is True
    assert interval.low == 13.5
    assert interval.high == 17.5
    assert interval.comparator == "range"


def test_parse_reference_interval_single_sided():
    # Upper bound
    lt = parse_reference_interval("< 200 mg/dL")
    assert lt is not None
    assert lt.low is None
    assert lt.high == 200.0
    assert lt.comparator == "<"

    lte = parse_reference_interval("<= 100")
    assert lte is not None
    assert lte.high == 100.0
    assert lte.comparator == "<="

    # Lower bound
    gt = parse_reference_interval("> 40 mg/dL")
    assert gt is not None
    assert gt.low == 40.0
    assert gt.high is None
    assert gt.comparator == ">"

    gte = parse_reference_interval(">= 60")
    assert gte is not None
    assert gte.low == 60.0
    assert gte.comparator == ">="


def test_parse_reference_interval_qualitative():
    interval = parse_reference_interval("Negative")
    assert interval is not None
    assert interval.is_numeric is False
    assert interval.raw_text == "Negative"


def test_parse_reference_interval_empty():
    assert parse_reference_interval(None) is None
    assert parse_reference_interval("") is None
    assert parse_reference_interval("   ") is None


def test_evaluate_two_sided_range_boundaries():
    interval = parse_reference_interval("13.5 - 17.5")

    # Boundary: exact lower bound -> NORMAL
    flag, _ = evaluate_reference_range(13.5, "13.5", interval)
    assert flag == FlagStatus.NORMAL

    # Boundary: exact upper bound -> NORMAL
    flag, _ = evaluate_reference_range(17.5, "17.5", interval)
    assert flag == FlagStatus.NORMAL

    # Within bounds -> NORMAL
    flag, _ = evaluate_reference_range(15.0, "15.0", interval)
    assert flag == FlagStatus.NORMAL

    # Below lower bound -> LOW
    flag, _ = evaluate_reference_range(12.0, "12.0", interval)
    assert flag == FlagStatus.LOW

    # Above upper bound -> HIGH
    flag, _ = evaluate_reference_range(19.0, "19.0", interval)
    assert flag == FlagStatus.HIGH

    # Verify CRITICAL is never assigned
    assert flag != FlagStatus.CRITICAL_HIGH
    assert flag != FlagStatus.CRITICAL_LOW


def test_evaluate_single_sided_ranges():
    # < 200
    lt_interval = parse_reference_interval("< 200")
    flag_normal, _ = evaluate_reference_range(195.0, "195", lt_interval)
    assert flag_normal == FlagStatus.NORMAL

    flag_boundary, _ = evaluate_reference_range(200.0, "200", lt_interval)
    assert flag_boundary == FlagStatus.HIGH

    flag_high, _ = evaluate_reference_range(220.0, "220", lt_interval)
    assert flag_high == FlagStatus.HIGH

    # > 40
    gt_interval = parse_reference_interval("> 40")
    flag_gt_normal, _ = evaluate_reference_range(48.0, "48", gt_interval)
    assert flag_gt_normal == FlagStatus.NORMAL

    flag_gt_boundary, _ = evaluate_reference_range(40.0, "40", gt_interval)
    assert flag_gt_boundary == FlagStatus.LOW

    flag_gt_low, _ = evaluate_reference_range(35.0, "35", gt_interval)
    assert flag_gt_low == FlagStatus.LOW


def test_evaluate_missing_or_non_numeric():
    # Missing interval
    flag_missing, reason = evaluate_reference_range(100.0, "100", None)
    assert flag_missing == FlagStatus.INCONCLUSIVE
    assert "No reference interval" in reason

    # Qualitative match
    qual_interval = parse_reference_interval("Negative")
    flag_qual, _ = evaluate_reference_range(None, "Negative", qual_interval)
    assert flag_qual == FlagStatus.NORMAL

    # Non-numeric value against numeric interval
    num_interval = parse_reference_interval("70 - 99")
    flag_nan, _ = evaluate_reference_range(None, "Pending", num_interval)
    assert flag_nan == FlagStatus.INCONCLUSIVE
