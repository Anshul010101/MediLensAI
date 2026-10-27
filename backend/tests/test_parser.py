import pytest

from backend.app.models.report import FlagStatus
from backend.app.services.parser import deterministic_parser
from backend.app.services.pdf_extractor import ExtractedPage


def test_parse_cbc_line():
    line = "Hemoglobin 14.5 g/dL 13.5 - 17.5"
    result = deterministic_parser.parse_line(line, source_page=1)
    assert result is not None
    assert result.canonical_name == "Hemoglobin"
    assert result.value_text == "14.5"
    assert result.value_numeric == 14.5
    assert result.unit == "g/dL"
    assert result.reference_interval is not None
    assert result.reference_interval.low == 13.5
    assert result.reference_interval.high == 17.5
    assert result.flag == FlagStatus.NORMAL
    assert result.source_page == 1


def test_parse_glucose_elevated():
    line = "Glucose 106* H mg/dL 70 - 99"
    result = deterministic_parser.parse_line(line, source_page=1)
    assert result is not None
    assert result.canonical_name == "Glucose"
    assert "106" in result.value_text
    assert result.value_numeric == 106.0
    assert result.unit == "mg/dL"
    assert result.flag == FlagStatus.HIGH


def test_parse_lipid_single_sided():
    line = "Total Cholesterol 215 H mg/dL < 200"
    result = deterministic_parser.parse_line(line, source_page=1)
    assert result is not None
    assert result.canonical_name == "Total Cholesterol"
    assert result.value_numeric == 215.0
    assert result.flag == FlagStatus.HIGH
    assert result.reference_interval.comparator == "<"


def test_parse_missing_unit():
    line = "Hemoglobin 14.2 13.5 - 17.5"
    result = deterministic_parser.parse_line(line, source_page=2)
    assert result is not None
    assert result.unit is None
    assert any("No explicit measurement unit" in note for note in result.uncertainty_notes)


def test_parse_missing_reference_range():
    line = "TSH 2.45 uIU/mL"
    result = deterministic_parser.parse_line(line, source_page=1)
    assert result is not None
    assert result.reference_interval is None
    assert result.flag == FlagStatus.INCONCLUSIVE
    assert any("No laboratory reference interval" in note for note in result.uncertainty_notes)


def test_parse_full_page_and_educational_notes():
    page = ExtractedPage(
        page_number=1,
        text="Sample CBC\nHemoglobin 14.5 g/dL 13.5 - 17.5\nPlatelets 240 10^3/uL 140 - 400",
        lines=[
            "Sample CBC",
            "Hemoglobin 14.5 g/dL 13.5 - 17.5",
            "Platelets 240 10^3/uL 140 - 400",
        ],
    )
    results, edu_notes = deterministic_parser.parse_pages([page])
    assert len(results) == 2
    assert len(edu_notes) == 2
    assert any(n.analyte_name == "Hemoglobin" for n in edu_notes)
    assert all("MediLens Deterministic Knowledge Base" in n.source for n in edu_notes)


def test_parse_multiline_table_cbc():
    """Regression test: Table layout where test name, value, unit, and range are on sequential lines."""
    table_lines = [
        "Laboratory results",
        "Test",
        "Result",
        "Unit",
        "Illustrative reference interval",
        "WBC",
        "7.2",
        "10^9/L",
        "4.0 - 11.0",
        "RBC",
        "4.7",
        "10^12/L",
        "4.2 - 5.9",
        "Hemoglobin",
        "14.1",
        "g/dL",
        "12.0 - 17.5",
        "Hematocrit",
        "42.0",
        "%",
        "36.0 - 50.0",
        "Platelets",
        "250",
        "10^9/L",
        "150 - 400",
        "MCV",
        "89",
        "fL",
        "80 - 100",
        "Notes",
    ]
    page = ExtractedPage(
        page_number=1,
        text="\n".join(table_lines),
        lines=table_lines,
    )
    results, _ = deterministic_parser.parse_pages([page])
    assert len(results) == 6
    by_name = {r.canonical_name: r for r in results}

    assert "White Blood Cells (WBC)" in by_name
    wbc = by_name["White Blood Cells (WBC)"]
    assert wbc.value_numeric == 7.2
    assert wbc.unit == "10^9/L"
    assert wbc.reference_interval is not None
    assert wbc.reference_interval.low == 4.0
    assert wbc.reference_interval.high == 11.0
    assert wbc.flag == FlagStatus.NORMAL

    assert "Red Blood Cells (RBC)" in by_name
    rbc = by_name["Red Blood Cells (RBC)"]
    assert rbc.value_numeric == 4.7
    assert rbc.unit == "10^12/L"
    assert rbc.flag == FlagStatus.NORMAL

    assert "Hemoglobin" in by_name
    hgb = by_name["Hemoglobin"]
    assert hgb.value_numeric == 14.1
    assert hgb.unit == "g/dL"
    assert hgb.flag == FlagStatus.NORMAL

    assert "Hematocrit" in by_name
    hct = by_name["Hematocrit"]
    assert hct.value_numeric == 42.0
    assert hct.unit == "%"
    assert hct.flag == FlagStatus.NORMAL

    assert "Platelets" in by_name
    plt = by_name["Platelets"]
    assert plt.value_numeric == 250.0
    assert plt.unit == "10^9/L"
    assert plt.flag == FlagStatus.NORMAL

    assert "Mean Corpuscular Volume (MCV)" in by_name
    mcv = by_name["Mean Corpuscular Volume (MCV)"]
    assert mcv.value_numeric == 89.0
    assert mcv.unit == "fL"
    assert mcv.flag == FlagStatus.NORMAL

