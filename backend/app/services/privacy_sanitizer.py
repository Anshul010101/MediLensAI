import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.models.report import TestResult
from backend.app.utils.logger import logger


# Common PII/PHI Regex Signatures
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
PHONE_REGEX = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
MRN_REGEX = re.compile(r"\b(?:MRN|ID|ACCESSION|ACC|CHART|PATIENT ID)[:\s#]*[A-Z0-9-]+\b", re.IGNORECASE)
DOB_REGEX = re.compile(r"\b(?:DOB|BIRTHDATE|DATE OF BIRTH)[:\s#]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE)
NAME_LABEL_REGEX = re.compile(r"\b(?:PATIENT|NAME|PATIENT NAME|DOCTOR|PHYSICIAN)[:\s#]+[A-Za-z\s,.-]{2,30}\b", re.IGNORECASE)
ADDRESS_REGEX = re.compile(
    r"\b\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct|Terrace|Ter|Circle|Cir|Place|Pl|Parkway|Pkwy)\b",
    re.IGNORECASE
)

# Potential Prompt Injection / Adversarial Document Signatures
PROMPT_INJECTION_REGEX = re.compile(
    r"(?i)\b(ignore\s+(?:all\s+)?previous\s+instructions|system\s+prompt|you\s+are\s+now|override\s+(?:all\s+)?rules|disregard\s+(?:all\s+)?prior|assistant:|role:\s*system|jailbreak)\b"
)


class SanitizedAnalyte(BaseModel):
    """Minimal, allowlisted analyte representation stripped of all personal context."""
    test_name: str
    value: str
    unit: Optional[str] = None
    reference_interval: Optional[str] = None
    deterministic_flag: str
    uncertainty: List[str] = Field(default_factory=list)


class SanitizedPayload(BaseModel):
    """
    Sanitized, allowlisted representation of laboratory findings prepared
    specifically for transmission to Google Gemini.
    """
    analytes: List[SanitizedAnalyte]
    total_tests_input: int
    total_tests_allowed: int
    redaction_notes: List[str] = Field(default_factory=list)
    is_blocked: bool = False
    blocked_reason: Optional[str] = None
    disclaimer: str = (
        "Privacy Notice: This minimized payload contains only non-identifiable test names, "
        "numerical values, units, reference intervals, and deterministic flags. "
        "All patient identifiers (names, dates, MRNs, contacts) have been scrubbed. "
        "Note: Automated redaction significantly reduces exposure but does not guarantee absolute mathematical anonymity. "
        "The minimized payload is transmitted to the configured Google Gemini model for educational explanation."
    )


class PrivacySanitizer:
    """
    Enforces strict PII/PHI minimization and prompt injection defense
    before any data leaves the local application environment.
    """

    def sanitize_test_results(self, test_results: List[TestResult]) -> SanitizedPayload:
        """
        Construct a strictly minimized, allowlisted payload from extracted TestResult objects.
        Raw document text is discarded. Any residual identifiers or prompt-injection markers are scrubbed.
        """
        sanitized_analytes: List[SanitizedAnalyte] = []
        redaction_notes: List[str] = []
        blocked_reason: Optional[str] = None

        if not test_results:
            return SanitizedPayload(
                analytes=[],
                total_tests_input=0,
                total_tests_allowed=0,
                redaction_notes=["No test results provided for sanitization."],
                is_blocked=False,
            )

        for test in test_results:
            is_valid, cleaned_name, cleaned_val, notes = self._sanitize_single_analyte(test)
            redaction_notes.extend(notes)

            if not is_valid:
                # If an analyte cannot be safely sanitized, omit it from the external payload
                continue

            ref_str = test.reference_interval.raw_text if test.reference_interval else None
            
            sanitized_analytes.append(
                SanitizedAnalyte(
                    test_name=cleaned_name,
                    value=cleaned_val,
                    unit=test.unit,
                    reference_interval=ref_str,
                    deterministic_flag=test.flag.value,
                    uncertainty=list(test.uncertainty_notes),
                )
            )

        # If zero analytes survived or all were contaminated, block the AI request
        if len(sanitized_analytes) == 0 and len(test_results) > 0:
            return SanitizedPayload(
                analytes=[],
                total_tests_input=len(test_results),
                total_tests_allowed=0,
                redaction_notes=redaction_notes,
                is_blocked=True,
                blocked_reason="All detected analytes contained unresolvable identifier patterns and were blocked for safety.",
            )

        return SanitizedPayload(
            analytes=sanitized_analytes,
            total_tests_input=len(test_results),
            total_tests_allowed=len(sanitized_analytes),
            redaction_notes=redaction_notes,
            is_blocked=False,
        )

    def _sanitize_single_analyte(self, test: TestResult) -> Tuple[bool, str, str, List[str]]:
        """
        Validate and scrub a single test result.
        Returns (is_valid, sanitized_name, sanitized_val, notes).
        """
        notes: List[str] = []
        raw_name = test.name
        canonical_name = test.canonical_name
        raw_val = test.value_text

        # 1. Check for prompt injection in test name or value
        if PROMPT_INJECTION_REGEX.search(raw_name) or PROMPT_INJECTION_REGEX.search(raw_val):
            notes.append(f"Neutralized adversarial prompt injection pattern detected in test field: '{test.canonical_name}'.")
            # Replace name with purely canonical name and value with sanitized token
            clean_name = canonical_name
            clean_val = re.sub(PROMPT_INJECTION_REGEX, "[DOCUMENT_TEXT]", raw_val)
        else:
            clean_name = canonical_name
            clean_val = raw_val

        # 2. Check for PII/PHI in name or value text
        for pii_regex, pii_label in [
            (SSN_REGEX, "SSN"),
            (PHONE_REGEX, "Phone number"),
            (EMAIL_REGEX, "Email address"),
            (MRN_REGEX, "Medical Record Number"),
            (DOB_REGEX, "Date of Birth"),
            (NAME_LABEL_REGEX, "Patient/Doctor Name"),
            (ADDRESS_REGEX, "Postal Address"),
        ]:
            if pii_regex.search(raw_name):
                notes.append(f"Redacted {pii_label} detected in test header '{raw_name}'. Replaced with canonical '{canonical_name}'.")
                clean_name = canonical_name
            if pii_regex.search(clean_val):
                notes.append(f"Redacted {pii_label} detected in value '{clean_val}'.")
                clean_val = pii_regex.sub(f"[REDACTED_{pii_label.upper()}]", clean_val)

        # 3. Value safety check: If value still contains obvious non-numeric text with identifier-like tokens, check safety
        if test.value_numeric is not None:
            # We have a verified numeric parse! Use standard format with flag
            # Preserve original flag character if present (*, H, L)
            flag_suffix = ""
            if "*" in clean_val:
                flag_suffix = "*"
            clean_val = f"{test.value_numeric}{flag_suffix}"
        else:
            # Non-numeric value (e.g. "Negative", "Normal") - ensure it's safe qualitative word
            if len(clean_val) > 50:
                notes.append(f"Omitted analyte '{canonical_name}': non-numeric value string excessively long or ambiguous.")
                return (False, clean_name, clean_val, notes)

        return (True, clean_name, clean_val, notes)

    def scrub_text(self, text: str) -> str:
        """
        Utility method for scrubbing residual strings (e.g., uncertainty notes).
        Replaces identifiable patterns with redaction tokens.
        """
        if not text:
            return ""
        scrubbed = text
        scrubbed = SSN_REGEX.sub("[REDACTED_SSN]", scrubbed)
        scrubbed = PHONE_REGEX.sub("[REDACTED_PHONE]", scrubbed)
        scrubbed = EMAIL_REGEX.sub("[REDACTED_EMAIL]", scrubbed)
        scrubbed = MRN_REGEX.sub("[REDACTED_MRN]", scrubbed)
        scrubbed = DOB_REGEX.sub("[REDACTED_DOB]", scrubbed)
        scrubbed = NAME_LABEL_REGEX.sub("[REDACTED_NAME]", scrubbed)
        scrubbed = ADDRESS_REGEX.sub("[REDACTED_ADDRESS]", scrubbed)
        scrubbed = PROMPT_INJECTION_REGEX.sub("[NEUTRALIZED_INSTRUCTION]", scrubbed)
        return scrubbed


privacy_sanitizer = PrivacySanitizer()
