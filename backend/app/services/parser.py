import re
from typing import Dict, List, Optional, Tuple

from backend.app.models.report import (
    EducationalContent,
    FlagStatus,
    ReferenceInterval,
    TestResult,
)
from backend.app.services.pdf_extractor import ExtractedPage
from backend.app.services.reference_ranges import (
    evaluate_reference_range,
    parse_reference_interval,
)


# Static Educational Knowledge Base for Laboratory Analytes
# Source: MediLens Deterministic Knowledge Base (Non-generative, verified educational facts)
ANALYTE_KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
    "Hemoglobin": {
        "category": "Complete Blood Count (CBC)",
        "role": "An iron-rich protein in red blood cells that carries oxygen from the lungs to tissues throughout the body.",
    },
    "Hematocrit": {
        "category": "Complete Blood Count (CBC)",
        "role": "The percentage of whole blood volume made up of red blood cells.",
    },
    "White Blood Cells (WBC)": {
        "category": "Complete Blood Count (CBC)",
        "role": "Cells of the immune system involved in defending the body against infections and foreign substances.",
    },
    "Red Blood Cells (RBC)": {
        "category": "Complete Blood Count (CBC)",
        "role": "Cells that transport oxygen from the lungs to bodily tissues and carry carbon dioxide back to the lungs.",
    },
    "Platelets": {
        "category": "Complete Blood Count (CBC)",
        "role": "Small cell fragments essential for normal blood clotting and blood vessel repair.",
    },
    "Mean Corpuscular Volume (MCV)": {
        "category": "Complete Blood Count (CBC)",
        "role": "Measures the average physical size of your red blood cells.",
    },
    "Glucose": {
        "category": "Metabolic Panel (CMP)",
        "role": "The primary sugar in the bloodstream that supplies energy to all body cells.",
    },
    "Calcium": {
        "category": "Metabolic Panel (CMP)",
        "role": "An essential mineral required for bone health, muscle contractions, nerve signaling, and blood clotting.",
    },
    "Sodium": {
        "category": "Metabolic Panel (CMP)",
        "role": "An essential electrolyte that helps maintain proper fluid balance, nerve impulses, and muscle function.",
    },
    "Potassium": {
        "category": "Metabolic Panel (CMP)",
        "role": "A vital electrolyte that supports normal heart rhythm, nerve function, and muscle contractions.",
    },
    "Chloride": {
        "category": "Metabolic Panel (CMP)",
        "role": "An electrolyte that works with sodium to balance fluid levels and electrical neutrality in cells.",
    },
    "Carbon Dioxide (CO2)": {
        "category": "Metabolic Panel (CMP)",
        "role": "An indicator of bicarbonate in the blood, helping regulate the body's acid-base (pH) balance.",
    },
    "Blood Urea Nitrogen (BUN)": {
        "category": "Metabolic Panel (CMP)",
        "role": "A waste product produced in the liver from protein breakdown and filtered out by healthy kidneys.",
    },
    "Creatinine": {
        "category": "Metabolic Panel (CMP)",
        "role": "A normal muscle breakdown waste product filtered out of the blood by the kidneys.",
    },
    "eGFR": {
        "category": "Metabolic Panel (CMP)",
        "role": "Estimated Glomerular Filtration Rate, estimating how efficiently the kidneys filter waste from blood.",
    },
    "Total Cholesterol": {
        "category": "Lipid Profile",
        "role": "A total measurement of all cholesterol types circulating in the blood.",
    },
    "Triglycerides": {
        "category": "Lipid Profile",
        "role": "The most common type of fat in the body, storing excess calories from food for energy between meals.",
    },
    "HDL Cholesterol": {
        "category": "Lipid Profile",
        "role": "High-Density Lipoprotein ('good cholesterol'), which helps carry cholesterol away from arteries back to the liver.",
    },
    "LDL Cholesterol": {
        "category": "Lipid Profile",
        "role": "Low-Density Lipoprotein ('bad cholesterol'), which can accumulate along artery walls when elevated.",
    },
    "TSH (Thyroid Stimulating Hormone)": {
        "category": "Thyroid Panel",
        "role": "A pituitary hormone that signals the thyroid gland to produce thyroid hormones controlling metabolism.",
    },
    "Free T4": {
        "category": "Thyroid Panel",
        "role": "The active, unbound form of thyroxine hormone that regulates how the body consumes energy.",
    },
}


# Known Analyte Aliases and Definitions
ANALYTE_DEFINITIONS = [
    # CBC
    {
        "canonical_name": "Hemoglobin",
        "category": "Complete Blood Count (CBC)",
        "aliases": [r"\bhemoglobin\b", r"\bhgb\b", r"\bhb\b"],
        "default_units": ["g/dL", "g/L"],
    },
    {
        "canonical_name": "Hematocrit",
        "category": "Complete Blood Count (CBC)",
        "aliases": [r"\bhematocrit\b", r"\bhct\b"],
        "default_units": ["%"],
    },
    {
        "canonical_name": "White Blood Cells (WBC)",
        "category": "Complete Blood Count (CBC)",
        "aliases": [r"\bwhite blood cells?(?:\s*\([A-Za-z]+\))?(?: count)?\b", r"\bwbc\b", r"\bleukocytes?\b"],
        "default_units": ["10^3/uL", "10^9/L", "K/uL", "/uL", "x10(3)/mcL"],
    },
    {
        "canonical_name": "Red Blood Cells (RBC)",
        "category": "Complete Blood Count (CBC)",
        "aliases": [r"\bred blood cells?(?:\s*\([A-Za-z]+\))?(?: count)?\b", r"\brbc\b", r"\berythrocytes?\b"],
        "default_units": ["10^6/uL", "10^12/L", "M/uL", "x10(6)/mcL"],
    },
    {
        "canonical_name": "Platelets",
        "category": "Complete Blood Count (CBC)",
        "aliases": [r"\bplatelets?(?: count)?\b", r"\bplt\b", r"\bthrombocytes?\b"],
        "default_units": ["10^3/uL", "10^9/L", "K/uL", "/uL", "x10(3)/mcL"],
    },
    {
        "canonical_name": "Mean Corpuscular Volume (MCV)",
        "category": "Complete Blood Count (CBC)",
        "aliases": [r"\bmean corpuscular volume\b", r"\bmcv\b"],
        "default_units": ["fL"],
    },
    # CMP / Glucose
    {
        "canonical_name": "Glucose",
        "category": "Metabolic Panel (CMP)",
        "aliases": [r"\bglucose(?:,?\s*fasting)?\b", r"\bfasting glucose\b", r"\bblood sugar\b"],
        "default_units": ["mg/dL", "mmol/L"],
    },
    {
        "canonical_name": "Calcium",
        "category": "Metabolic Panel (CMP)",
        "aliases": [r"\bcalcium\b", r"\bserum calcium\b"],
        "default_units": ["mg/dL", "mmol/L"],
    },
    {
        "canonical_name": "Sodium",
        "category": "Metabolic Panel (CMP)",
        "aliases": [r"\bsodium\b", r"\bserum sodium\b"],
        "default_units": ["mmol/L", "mEq/L"],
    },
    {
        "canonical_name": "Potassium",
        "category": "Metabolic Panel (CMP)",
        "aliases": [r"\bpotassium\b", r"\bserum potassium\b"],
        "default_units": ["mmol/L", "mEq/L"],
    },
    {
        "canonical_name": "Chloride",
        "category": "Metabolic Panel (CMP)",
        "aliases": [r"\bchloride\b", r"\bserum chloride\b"],
        "default_units": ["mmol/L", "mEq/L"],
    },
    {
        "canonical_name": "Carbon Dioxide (CO2)",
        "category": "Metabolic Panel (CMP)",
        "aliases": [r"\bcarbon dioxide\b", r"\bco2\b", r"\bbicarbonate\b"],
        "default_units": ["mmol/L", "mEq/L"],
    },
    {
        "canonical_name": "Blood Urea Nitrogen (BUN)",
        "category": "Metabolic Panel (CMP)",
        "aliases": [r"\bblood urea nitrogen\b", r"\bbun\b", r"\burea nitrogen\b"],
        "default_units": ["mg/dL", "mmol/L"],
    },
    {
        "canonical_name": "Creatinine",
        "category": "Metabolic Panel (CMP)",
        "aliases": [r"\bcreatinine\b", r"\bserum creatinine\b"],
        "default_units": ["mg/dL", "umol/L"],
    },
    {
        "canonical_name": "eGFR",
        "category": "Metabolic Panel (CMP)",
        "aliases": [r"\begfr\b", r"\bestimated gfr\b", r"\bglomerular filtration rate\b"],
        "default_units": ["mL/min/1.73m2", "mL/min"],
    },
    # Lipid Profile
    {
        "canonical_name": "Total Cholesterol",
        "category": "Lipid Profile",
        "aliases": [r"\btotal cholesterol\b", r"\bcholesterol,?\s*total\b"],
        "default_units": ["mg/dL", "mmol/L"],
    },
    {
        "canonical_name": "Triglycerides",
        "category": "Lipid Profile",
        "aliases": [r"\btriglycerides?\b"],
        "default_units": ["mg/dL", "mmol/L"],
    },
    {
        "canonical_name": "HDL Cholesterol",
        "category": "Lipid Profile",
        "aliases": [r"\bhdl cholesterol\b", r"\bhdl-c\b", r"\bhdl\b"],
        "default_units": ["mg/dL", "mmol/L"],
    },
    {
        "canonical_name": "LDL Cholesterol",
        "category": "Lipid Profile",
        "aliases": [r"\bldl cholesterol(?:,?\s*calc)?\b", r"\bldl-c\b", r"\bldl\b"],
        "default_units": ["mg/dL", "mmol/L"],
    },
    # Thyroid Panel
    {
        "canonical_name": "TSH (Thyroid Stimulating Hormone)",
        "category": "Thyroid Panel",
        "aliases": [r"\bthyroid stimulating hormone\b", r"\btsh\b"],
        "default_units": ["uIU/mL", "mIU/L", "mcIU/mL"],
    },
    {
        "canonical_name": "Free T4",
        "category": "Thyroid Panel",
        "aliases": [r"\bfree t4\b", r"\bt4,?\s*free\b", r"\bfree thyroxine\b"],
        "default_units": ["ng/dL", "pmol/L"],
    },
]


COMMON_UNITS = [
    "10^12/L", "10^9/L", "x10^12/L", "x10^9/L", "10*12/L", "10*9/L", "x10(12)/mcL", "x10(9)/L", "x10(12)/L",
    "g/dL", "g/L", "mg/dL", "uIU/mL", "mIU/L", "mcIU/mL", "ng/dL", "pg/mL",
    "mmol/L", "mEq/L", "umol/L", "10^3/uL", "10^6/uL", "K/uL", "M/uL",
    "/uL", "x10(3)/mcL", "x10(6)/mcL", "fL", "pg", "%", "mL/min/1.73m2", "U/L", "IU/L"
]


class DeterministicLabParser:
    """
    Robust, deterministic parser for lab report lines and tables.
    Never guesses values or invents reference ranges.
    """

    def parse_pages(self, pages: List[ExtractedPage]) -> Tuple[List[TestResult], List[EducationalContent]]:
        """
        Scan all document pages and extract structured test results.
        Returns (test_results, educational_notes).
        """
        all_results: List[TestResult] = []
        analyte_matched_set = set()

        for page in pages:
            page_results = self._parse_single_page(page)
            all_results.extend(page_results)
            for res in page_results:
                analyte_matched_set.add(res.canonical_name)

        # Build educational content strictly for the detected analytes
        educational_notes: List[EducationalContent] = []
        for canonical_name in sorted(analyte_matched_set):
            if canonical_name in ANALYTE_KNOWLEDGE_BASE:
                info = ANALYTE_KNOWLEDGE_BASE[canonical_name]
                educational_notes.append(
                    EducationalContent(
                        analyte_name=canonical_name,
                        source="MediLens Deterministic Knowledge Base",
                        physiological_role=info["role"],
                    )
                )

        return (all_results, educational_notes)

    def _parse_single_page(self, page: ExtractedPage) -> List[TestResult]:
        """
        Parse page text lines into structured results.
        Supports both single-line formatted entries and multi-line/vertical table cells.
        """
        results: List[TestResult] = []
        lines = page.lines
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            if self._is_analyte_start(line):
                # 1. Try single-line parsing first
                single_res = self.parse_line(line, source_page=page.page_number)
                if single_res and single_res.value_numeric is not None and (single_res.reference_interval or single_res.unit):
                    results.append(single_res)
                    i += 1
                    continue

                # 2. Incomplete line (e.g. table cell on its own line): look ahead up to 5 lines
                combined_tokens = [line]
                best_res = single_res
                j = i + 1
                while j < n and (j - i) <= 5:
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    if self._is_analyte_start(next_line):
                        break
                    if re.search(r"^(notice|notes|sample|patient|laboratory|panel|facility|date|disclaimer|method|all results|informational|generated)\b", next_line, re.I):
                        break
                    combined_tokens.append(next_line)
                    j += 1

                    candidate_str = " ".join(combined_tokens)
                    candidate_res = self.parse_line(candidate_str, source_page=page.page_number)
                    if candidate_res and candidate_res.value_numeric is not None:
                        best_res = candidate_res
                        if candidate_res.unit and candidate_res.reference_interval:
                            break

                if best_res:
                    results.append(best_res)
                    i = j
                    continue

            i += 1

        return results

    def _is_analyte_start(self, line: str) -> bool:
        """Check if line begins with or contains a known analyte identifier."""
        clean = line.strip()
        if not clean or len(clean) < 2:
            return False
        if re.search(r"^(test name|component|analyte|flag|reference range|units|result|laboratory results|sample information|notes|illustrative)\b", clean, re.I):
            return False
        for definition in ANALYTE_DEFINITIONS:
            for alias_pattern in definition["aliases"]:
                if re.search(alias_pattern, clean, re.IGNORECASE):
                    return True
        return False

    def parse_line(self, line: str, source_page: Optional[int] = None) -> Optional[TestResult]:
        """
        Attempt to parse a single text line into a structured laboratory test.
        Returns TestResult if a known analyte pattern is recognized, else None.
        """
        line_clean = line.strip()
        if not line_clean or len(line_clean) < 3:
            return None

        # Ignore obvious header lines
        if re.search(r"^(test name|component|analyte|flag|reference range|units|result)\b", line_clean, re.I):
            return None

        for definition in ANALYTE_DEFINITIONS:
            for alias_pattern in definition["aliases"]:
                match = re.search(alias_pattern, line_clean, re.IGNORECASE)
                if match:
                    return self._extract_result_from_matched_line(
                        line=line_clean,
                        match_span=match.span(),
                        definition=definition,
                        source_page=source_page,
                    )

        return None

    def _extract_result_from_matched_line(
        self,
        line: str,
        match_span: Tuple[int, int],
        definition: dict,
        source_page: Optional[int] = None,
    ) -> TestResult:
        """
        Given a matched test name, extract value, unit, and reference interval.
        Flag ambiguities and missing units transparently.
        """
        matched_name = line[match_span[0]:match_span[1]].strip()
        remaining_text = line[match_span[1]:].strip()
        
        # Remove separator characters if present
        remaining_text = re.sub(r"^[:|\t-]+", "", remaining_text).strip()

        uncertainty_notes: List[str] = []

        # 1. Identify unit if present
        extracted_unit: Optional[str] = None
        for u in sorted(COMMON_UNITS, key=lambda x: len(x), reverse=True):
            if u == "%":
                pattern = re.compile(r"(?:^|(?<=[\s\d]))%(?=$|[\s\d,;:()/-])")
            else:
                pattern = re.compile(rf"(?:^|(?<=[\s\d])){re.escape(u)}(?=$|[\s\d,;:()/-])", re.IGNORECASE)
            u_match = pattern.search(remaining_text)
            if u_match:
                extracted_unit = u
                break

        # 2. Extract reference interval candidates
        # Look for patterns like "13.5 - 17.5" or "< 200" or ">= 40" or "70-99"
        ref_interval_text: Optional[str] = None
        ref_obj: Optional[ReferenceInterval] = None

        # Look for two-sided range at the end or middle
        range_match = re.search(r"(\d+(?:\.\d+)?\s*(?:-|–|—|to)\s*\d+(?:\.\d+)?(?:\s*[a-zA-Z/%^0-9]+)?)", remaining_text)
        if range_match:
            ref_interval_text = range_match.group(1).strip()
            ref_obj = parse_reference_interval(ref_interval_text)
            # Remove reference text from remaining text to isolate result value
            remaining_text = remaining_text[:range_match.start()] + " " + remaining_text[range_match.end():]
        else:
            # Check for single-sided range like (< 200, <= 100, > 40)
            bound_match = re.search(r"([<>]=?\s*\d+(?:\.\d+)?(?:\s*[a-zA-Z/%^0-9]+)?)", remaining_text)
            if bound_match:
                ref_interval_text = bound_match.group(1).strip()
                ref_obj = parse_reference_interval(ref_interval_text)
                remaining_text = remaining_text[:bound_match.start()] + " " + remaining_text[bound_match.end():]

        # 3. Extract the test's measured value from the remaining text
        # Look for numeric float or integer with optional trailing flag (*, H, L)
        val_match = re.search(r"([<>]?=?\s*-?\d+(?:\.\d+)?)\s*([*HL])?\b", remaining_text)
        
        if not val_match:
            # Check for non-numeric words (e.g. "Negative", "Normal", "Present")
            qual_match = re.search(r"\b(negative|non-reactive|normal|positive|reactive)\b", remaining_text, re.IGNORECASE)
            if qual_match:
                value_text = qual_match.group(1)
                value_numeric = None
            else:
                value_text = remaining_text.strip() or "UNKNOWN"
                value_numeric = None
                uncertainty_notes.append("Could not isolate a distinct numeric value in the line.")
        else:
            raw_value_token = val_match.group(1).strip()
            flag_char = val_match.group(2)
            value_text = raw_value_token + (flag_char if flag_char else "")
            try:
                # Strip comparator if present for numeric value
                num_str = re.sub(r"[^\d.-]", "", raw_value_token)
                value_numeric = float(num_str)
            except ValueError:
                value_numeric = None
                uncertainty_notes.append(f"Value '{value_text}' could not be cleanly converted to a number.")

        # Unit validation
        if not extracted_unit:
            uncertainty_notes.append("No explicit measurement unit was identified on this line.")

        # Flag and evaluation
        if ref_obj is None:
            uncertainty_notes.append("No laboratory reference interval was stated on this line.")
            flag = FlagStatus.INCONCLUSIVE
            flag_reason = "No reference interval stated by laboratory."
        elif value_numeric is None:
            flag, flag_reason = evaluate_reference_range(None, value_text, ref_obj)
        else:
            flag, flag_reason = evaluate_reference_range(value_numeric, value_text, ref_obj)

        return TestResult(
            name=matched_name,
            canonical_name=definition["canonical_name"],
            category=definition["category"],
            value_text=value_text,
            value_numeric=value_numeric,
            unit=extracted_unit,
            reference_interval=ref_obj,
            flag=flag,
            flag_reason=flag_reason,
            source_page=source_page,
            uncertainty_notes=uncertainty_notes,
            is_synthetic=False,
        )


deterministic_parser = DeterministicLabParser()
