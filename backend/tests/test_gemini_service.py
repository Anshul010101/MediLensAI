import json
import logging
from unittest.mock import MagicMock
import pytest

from backend.app.models.report import (
    AIExplanationStatus,
    FlagStatus,
    ReferenceInterval,
    TestResult,
)
from backend.app.services.gemini_service import GeminiService
from backend.app.services.privacy_sanitizer import PrivacySanitizer, SanitizedPayload


@pytest.fixture
def sample_test_results():
    return [
        TestResult(
            name="Hemoglobin",
            canonical_name="Hemoglobin",
            category="Complete Blood Count",
            value_text="14.5",
            value_numeric=14.5,
            unit="g/dL",
            reference_interval=ReferenceInterval(raw_text="13.5 - 17.5", low=13.5, high=17.5, is_numeric=True),
            flag=FlagStatus.NORMAL,
        ),
        TestResult(
            name="Glucose",
            canonical_name="Glucose",
            category="CMP",
            value_text="106*",
            value_numeric=106.0,
            unit="mg/dL",
            reference_interval=ReferenceInterval(raw_text="70 - 99", low=70.0, high=99.0, is_numeric=True),
            flag=FlagStatus.HIGH,
        ),
    ]


@pytest.fixture
def valid_mock_response():
    response = MagicMock()
    response.text = json.dumps({
        "summary_text": "Your routine blood count is within standard reference intervals, while your fasting glucose is slightly above the laboratory reference upper bound.",
        "per_test_explanations": {
            "Hemoglobin": "Hemoglobin is an iron-rich protein that transports oxygen to bodily tissues. Your result is normal.",
            "Glucose": "Glucose is the primary sugar in blood providing cellular energy. Your value is slightly above the stated range."
        },
        "limitations_and_uncertainty": [
            "Dietary intake, hydration, and fasting duration can influence glucose readings."
        ],
        "questions_for_doctor": [
            "Does my fasting glucose level require a follow-up test or HbA1c screening?",
            "Are there dietary recommendations appropriate for my current results?"
        ],
        "disclaimer": "Informational only; non-diagnostic."
    })
    return response


def test_missing_api_key_returns_ai_unavailable(sample_test_results):
    service = GeminiService(api_key="")
    explanation = service.generate_explanation(sample_test_results)
    
    assert explanation.status == AIExplanationStatus.AI_UNAVAILABLE
    assert "not configured" in explanation.status_reason.lower()
    assert explanation.summary_text is None  # Never fabricates AI prose


def test_successful_structured_ai_response(sample_test_results, valid_mock_response):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = valid_mock_response

    service = GeminiService(api_key="mock_test_key", client=mock_client)
    explanation = service.generate_explanation(sample_test_results)

    assert explanation.status == AIExplanationStatus.COMPLETED
    assert explanation.provider == "Google Gemini"
    assert "routine blood count" in explanation.summary_text
    assert "Hemoglobin" in explanation.per_test_explanations
    assert len(explanation.questions_for_doctor) == 2
    assert explanation.questions_for_doctor[0].startswith("Does my fasting glucose")
    assert explanation.status_reason == "Explanation successfully generated and validated."


def test_malformed_json_response_handling(sample_test_results):
    mock_client = MagicMock()
    bad_response = MagicMock()
    bad_response.text = "This is not valid JSON string {"
    mock_client.models.generate_content.return_value = bad_response

    service = GeminiService(api_key="mock_test_key", client=mock_client)
    explanation = service.generate_explanation(sample_test_results)

    assert explanation.status == AIExplanationStatus.AI_UNAVAILABLE
    assert "malformed json" in explanation.status_reason.lower()
    assert explanation.summary_text is None


def test_invalid_schema_response_handling(sample_test_results):
    mock_client = MagicMock()
    bad_schema_response = MagicMock()
    # Missing required 'summary_text'
    bad_schema_response.text = json.dumps({"unrelated_field": 123})
    mock_client.models.generate_content.return_value = bad_schema_response

    service = GeminiService(api_key="mock_test_key", client=mock_client)
    explanation = service.generate_explanation(sample_test_results)

    assert explanation.status == AIExplanationStatus.AI_UNAVAILABLE
    assert "schema validation" in explanation.status_reason.lower()
    assert explanation.summary_text is None


def test_request_timeout_handling(sample_test_results):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = TimeoutError("Network timeout")

    service = GeminiService(api_key="mock_test_key", client=mock_client)
    explanation = service.generate_explanation(sample_test_results)

    assert explanation.status == AIExplanationStatus.AI_UNAVAILABLE
    assert "timed out" in explanation.status_reason.lower()
    assert explanation.summary_text is None


def test_rate_limit_handling(sample_test_results):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("429 ResourceExhausted: rate limit exceeded")

    service = GeminiService(api_key="mock_test_key", client=mock_client)
    explanation = service.generate_explanation(sample_test_results)

    assert explanation.status == AIExplanationStatus.AI_UNAVAILABLE
    assert "rate limit" in explanation.status_reason.lower()
    assert explanation.summary_text is None


def test_provider_503_error_handling(sample_test_results):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("503 Service Unavailable: server overloaded")

    service = GeminiService(api_key="mock_test_key", client=mock_client)
    explanation = service.generate_explanation(sample_test_results)

    assert explanation.status == AIExplanationStatus.AI_UNAVAILABLE
    assert "unavailable" in explanation.status_reason.lower() or "503" in explanation.status_reason.lower()
    assert explanation.summary_text is None


def test_blocked_sanitization_prevents_gemini_call(sample_test_results):
    mock_client = MagicMock()
    mock_sanitizer = MagicMock()
    mock_sanitizer.sanitize_test_results.return_value = SanitizedPayload(
        analytes=[],
        total_tests_input=2,
        total_tests_allowed=0,
        is_blocked=True,
        blocked_reason="Severe PII leakage detected",
    )

    service = GeminiService(api_key="mock_test_key", client=mock_client, sanitizer=mock_sanitizer)
    explanation = service.generate_explanation(sample_test_results)

    assert explanation.status == AIExplanationStatus.AI_UNAVAILABLE
    assert "blocked by privacy layer" in explanation.status_reason.lower()
    # Confirm Gemini SDK was NEVER invoked
    mock_client.models.generate_content.assert_not_called()


def test_logging_does_not_expose_credentials_or_pii(caplog, sample_test_results, valid_mock_response):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = valid_mock_response

    secret_key = "AIzaSy_SUPER_CONFIDENTIAL_KEY_12345"
    service = GeminiService(api_key=secret_key, client=mock_client)

    with caplog.at_level(logging.INFO):
        service.generate_explanation(sample_test_results)

    captured = caplog.text
    assert secret_key not in captured
    assert "SUPER_CONFIDENTIAL" not in captured
    assert "14.5" not in captured  # Raw medical analyte value not in operational metrics


def test_gemini_failure_preserves_deterministic_flags(sample_test_results):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Fatal Gemini Error")

    service = GeminiService(api_key="mock_test_key", client=mock_client)
    explanation = service.generate_explanation(sample_test_results)

    # Explanation failed
    assert explanation.status == AIExplanationStatus.AI_UNAVAILABLE
    
    # Assert deterministic flags on input results remain exactly intact
    assert sample_test_results[0].flag == FlagStatus.NORMAL
    assert sample_test_results[1].flag == FlagStatus.HIGH


def test_gemini_schema_compatibility_with_sdk():
    """Verify GeminiStructuredResponse conforms to Google GenAI OpenAPI requirements without additionalProperties."""
    from google.genai import types
    from backend.app.services.gemini_prompt import GeminiStructuredResponse, TestExplanationItem

    # Should not raise ValueError("additionalProperties is only supported in Gemini Enterprise...")
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=GeminiStructuredResponse,
    )
    assert config.response_schema == GeminiStructuredResponse


def test_gemini_service_maps_list_explanations(sample_test_results):
    """Verify that List[TestExplanationItem] from Gemini API maps to Dict[str, str] in AIExplanation."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "summary_text": "Overall healthy CBC.",
        "per_test_explanations": [
            {"test_name": "Hemoglobin", "explanation": "Carries oxygen throughout the body."},
            {"test_name": "Glucose", "explanation": "Supplies cellular energy."}
        ],
        "limitations_and_uncertainty": [],
        "questions_for_doctor": ["How often should I test?"],
        "disclaimer": "Informational only."
    })
    mock_client.models.generate_content.return_value = mock_response

    service = GeminiService(api_key="mock_key", client=mock_client)
    explanation = service.generate_explanation(sample_test_results)

    assert explanation.status == AIExplanationStatus.COMPLETED
    assert isinstance(explanation.per_test_explanations, dict)
    assert "Hemoglobin" in explanation.per_test_explanations
    assert explanation.per_test_explanations["Hemoglobin"] == "Carries oxygen throughout the body."
    assert "Glucose" in explanation.per_test_explanations


def test_gemini_model_fallback_on_404(sample_test_results, valid_mock_response):
    """Verify that if the primary model returns 404/retired, the service attempts fallback."""
    mock_client = MagicMock()

    # First call with gemini-2.5-flash raises 404, second call with fallback succeeds
    call_count = 0
    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("404 NOT_FOUND: This model models/gemini-2.5-flash is no longer available to new users.")
        return valid_mock_response

    mock_client.models.generate_content.side_effect = side_effect

    service = GeminiService(api_key="mock_key", model="gemini-2.5-flash", client=mock_client)
    explanation = service.generate_explanation(sample_test_results)

    assert explanation.status == AIExplanationStatus.COMPLETED
    assert call_count == 2  # Proves fallback was attempted and succeeded
    assert explanation.model == "gemini-3.5-flash"

