import re
from typing import Optional, Tuple

from backend.app.models.report import FlagStatus, ReferenceInterval


# Regex patterns for range parsing
TWO_SIDED_PATTERN = re.compile(
    r"^\s*([<>]?=?\s*-?\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*([<>]?=?\s*-?\d+(?:\.\d+)?)\s*([a-zA-Z/%^0-9\s]*)$",
    re.IGNORECASE
)
LESS_THAN_PATTERN = re.compile(
    r"^\s*(<=?)\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z/%^0-9\s]*)$"
)
GREATER_THAN_PATTERN = re.compile(
    r"^\s*(>=?)\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z/%^0-9\s]*)$"
)


def parse_reference_interval(raw_text: Optional[str]) -> Optional[ReferenceInterval]:
    """
    Parse a laboratory reference interval string into structured numeric or qualitative bounds.
    Returns None if raw_text is empty or absent. Never invents missing bounds.
    """
    if not raw_text or not raw_text.strip():
        return None

    cleaned = raw_text.strip()

    # Case 1: Check for single-sided upper bound (< X or <= X)
    match_lt = LESS_THAN_PATTERN.match(cleaned)
    if match_lt:
        comparator = match_lt.group(1)
        high_val = float(match_lt.group(2))
        unit = match_lt.group(3).strip() or None
        return ReferenceInterval(
            raw_text=cleaned,
            low=None,
            high=high_val,
            unit=unit,
            is_numeric=True,
            comparator=comparator,
        )

    # Case 2: Check for single-sided lower bound (> X or >= X)
    match_gt = GREATER_THAN_PATTERN.match(cleaned)
    if match_gt:
        comparator = match_gt.group(1)
        low_val = float(match_gt.group(2))
        unit = match_gt.group(3).strip() or None
        return ReferenceInterval(
            raw_text=cleaned,
            low=low_val,
            high=None,
            unit=unit,
            is_numeric=True,
            comparator=comparator,
        )

    # Case 3: Two-sided interval (e.g. 13.5 - 17.5, 70 to 99)
    match_two = TWO_SIDED_PATTERN.match(cleaned)
    if match_two:
        try:
            # Clean possible stray characters in numbers
            low_str = match_two.group(1).replace("<", "").replace(">", "").replace("=", "").strip()
            high_str = match_two.group(2).replace("<", "").replace(">", "").replace("=", "").strip()
            low_val = float(low_str)
            high_val = float(high_str)
            unit = match_two.group(3).strip() or None
            return ReferenceInterval(
                raw_text=cleaned,
                low=low_val,
                high=high_val,
                unit=unit,
                is_numeric=True,
                comparator="range",
            )
        except ValueError:
            pass

    # Case 4: Non-numeric qualitative range (e.g., "Negative", "Non-reactive", "Normal")
    return ReferenceInterval(
        raw_text=cleaned,
        low=None,
        high=None,
        unit=None,
        is_numeric=False,
        comparator=None,
    )


def evaluate_reference_range(
    value_numeric: Optional[float],
    value_text: str,
    interval: Optional[ReferenceInterval],
) -> Tuple[FlagStatus, str]:
    """
    Deterministically compare an analyte value against the stated reference interval.
    
    Guarantees:
    - Never assigns CRITICAL without a validated source-supported panic threshold.
    - Classifies boundary values consistently.
    - Accurately reports missing or non-numeric reference intervals.
    """
    if interval is None:
        return (
            FlagStatus.INCONCLUSIVE,
            "No reference interval stated by laboratory in report."
        )

    if not interval.is_numeric:
        # Qualitative / non-numeric comparison
        norm_val = value_text.strip().lower()
        norm_ref = interval.raw_text.strip().lower()
        if norm_val == norm_ref or (norm_ref == "negative" and norm_val in ["negative", "neg", "non-reactive"]):
            return (FlagStatus.NORMAL, f"Qualitative result matches reference expectation ('{interval.raw_text}')")
        return (
            FlagStatus.INCONCLUSIVE,
            f"Qualitative reference interval '{interval.raw_text}' requires clinical correlation."
        )

    if value_numeric is None:
        return (
            FlagStatus.INCONCLUSIVE,
            f"Extracted value '{value_text}' is non-numeric and cannot be evaluated against numeric interval."
        )

    # Handle two-sided interval
    if interval.low is not None and interval.high is not None:
        if interval.low <= value_numeric <= interval.high:
            return (
                FlagStatus.NORMAL,
                f"{value_numeric} is within stated reference interval [{interval.low} - {interval.high}]"
            )
        elif value_numeric < interval.low:
            return (
                FlagStatus.LOW,
                f"{value_numeric} is below stated reference lower bound ({interval.low})"
            )
        else:
            return (
                FlagStatus.HIGH,
                f"{value_numeric} is above stated reference upper bound ({interval.high})"
            )

    # Handle single-sided upper bound (< X or <= X)
    if interval.high is not None and interval.comparator in ("<", "<="):
        if interval.comparator == "<=":
            if value_numeric <= interval.high:
                return (FlagStatus.NORMAL, f"{value_numeric} meets stated upper threshold (<= {interval.high})")
            else:
                return (FlagStatus.HIGH, f"{value_numeric} exceeds stated upper threshold (<= {interval.high})")
        else:  # "<"
            if value_numeric < interval.high:
                return (FlagStatus.NORMAL, f"{value_numeric} meets stated upper threshold (< {interval.high})")
            else:
                return (FlagStatus.HIGH, f"{value_numeric} exceeds stated upper threshold (< {interval.high})")

    # Handle single-sided lower bound (> X or >= X)
    if interval.low is not None and interval.comparator in (">", ">="):
        if interval.comparator == ">=":
            if value_numeric >= interval.low:
                return (FlagStatus.NORMAL, f"{value_numeric} meets stated lower threshold (>= {interval.low})")
            else:
                return (FlagStatus.LOW, f"{value_numeric} is below stated lower threshold (>= {interval.low})")
        else:  # ">"
            if value_numeric > interval.low:
                return (FlagStatus.NORMAL, f"{value_numeric} meets stated lower threshold (> {interval.low})")
            else:
                return (FlagStatus.LOW, f"{value_numeric} is below stated lower threshold (> {interval.low})")

    return (
        FlagStatus.INCONCLUSIVE,
        f"Unable to deterministically evaluate value {value_numeric} against '{interval.raw_text}'"
    )
