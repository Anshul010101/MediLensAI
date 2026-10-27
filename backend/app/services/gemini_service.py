import json
import time
from typing import Any, List, Optional
from pydantic import ValidationError

from backend.app.config import settings
from backend.app.models.report import (
    AIExplanation,
    AIExplanationStatus,
    TestResult,
)
from backend.app.services.gemini_prompt import (
    GeminiStructuredResponse,
    build_gemini_prompt,
)
from backend.app.services.privacy_sanitizer import (
    PrivacySanitizer,
    SanitizedPayload,
    privacy_sanitizer,
)
from backend.app.utils.logger import log_processing_event, logger


class GeminiService:
    """
    Manages safe communication with the Google Gemini API using the official google-genai SDK.
    Enforces privacy sanitization, structured Pydantic response validation,
    bounded retry logic, and zero-fabrication failure handling.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        sanitizer: Optional[PrivacySanitizer] = None,
        client: Optional[Any] = None,
    ):
        self._custom_api_key = api_key
        self._custom_model = model
        self.sanitizer = sanitizer or privacy_sanitizer
        self._injected_client = client

    @property
    def api_key(self) -> str:
        return self._custom_api_key if self._custom_api_key is not None else settings.gemini_api_key

    @property
    def model_name(self) -> str:
        return self._custom_model if self._custom_model is not None else settings.gemini_model

    def is_configured(self) -> bool:
        """Check if a non-empty API key is configured."""
        key = self.api_key
        return bool(key and key.strip())

    def _get_client(self) -> Any:
        """Initialize or return the google-genai Client."""
        if self._injected_client is not None:
            return self._injected_client

        if not self.is_configured():
            return None

        from google import genai
        # Initialize official google-genai client with the configured key
        return genai.Client(api_key=self.api_key)

    def generate_explanation(self, test_results: List[TestResult]) -> AIExplanation:
        """
        Generate a safe, plain-language explanation for structured lab results.
        
        Guarantees:
        1. Pre-sanitizes results into an allowlisted minimal payload.
        2. Explicitly returns AI_UNAVAILABLE on missing key or failure.
        3. Never fabricates AI prose when unconfigured or failing.
        4. Validates structured JSON response against Pydantic schema.
        5. Does not log sensitive patient data, full prompts, or keys.
        """
        start_time = time.time()

        # Step 1: Check configuration
        if not self.is_configured():
            log_processing_event("gemini_explanation_skipped", {
                "status": "ai_unavailable",
                "error_type": "missing_api_key",
            })
            return AIExplanation(
                status=AIExplanationStatus.AI_UNAVAILABLE,
                provider="Google Gemini",
                model=self.model_name,
                status_reason="Gemini API key is not configured in backend environment.",
            )

        # Step 2: Privacy Sanitization & Minimization
        sanitized_payload: SanitizedPayload = self.sanitizer.sanitize_test_results(test_results)

        if sanitized_payload.is_blocked:
            log_processing_event("gemini_explanation_blocked", {
                "status": "blocked",
                "error_type": "privacy_violation_guard",
            })
            return AIExplanation(
                status=AIExplanationStatus.AI_UNAVAILABLE,
                provider="Google Gemini",
                model=self.model_name,
                status_reason=f"Analysis blocked by privacy layer: {sanitized_payload.blocked_reason}",
            )

        if len(sanitized_payload.analytes) == 0:
            return AIExplanation(
                status=AIExplanationStatus.AI_UNAVAILABLE,
                provider="Google Gemini",
                model=self.model_name,
                status_reason="No valid laboratory tests were available for AI explanation.",
            )

        # Step 3: Build Prompt
        system_instruction, user_prompt = build_gemini_prompt(sanitized_payload)

        # Step 4: Execute with bounded retries and timeout
        client = self._get_client()
        if client is None:
            return AIExplanation(
                status=AIExplanationStatus.AI_UNAVAILABLE,
                provider="Google Gemini",
                model=self.model_name,
                status_reason="Failed to initialize Google Gemini client.",
            )

        retries_remaining = max(0, settings.gemini_max_retries)
        last_error_reason = "Unknown provider error."

        while retries_remaining >= 0:
            try:
                explanation = self._execute_api_call(client, system_instruction, user_prompt)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                log_processing_event("gemini_explanation_success", {
                    "status": "completed",
                    "latency_ms": elapsed_ms,
                    "test_count": len(sanitized_payload.analytes),
                })
                return explanation
            except TimeoutError as ex:
                last_error_reason = f"Gemini API request timed out after {settings.gemini_timeout_seconds} seconds."
                logger.warning(f"Gemini timeout: {str(ex)}")
                retries_remaining -= 1
            except ValidationError as ex:
                last_error_reason = "Gemini response failed Pydantic schema validation."
                logger.warning(f"Schema validation error: {str(ex)}")
                # Schema errors are deterministic; do not retry
                break
            except json.JSONDecodeError as ex:
                last_error_reason = "Gemini response contained malformed JSON."
                logger.warning(f"JSON decode error: {str(ex)}")
                retries_remaining -= 1
            except Exception as ex:
                err_str = str(ex).lower()
                if "rate limit" in err_str or "resource_exhausted" in err_str or "429" in err_str:
                    last_error_reason = "Gemini service rate limit reached. Please retry in a few moments."
                    retries_remaining -= 1
                    time.sleep(1.0)
                elif "503" in err_str or "unavailable" in err_str or "overloaded" in err_str:
                    last_error_reason = "Gemini provider service temporarily unavailable (503)."
                    retries_remaining -= 1
                    time.sleep(1.0)
                else:
                    last_error_reason = f"Gemini API request failed: {type(ex).__name__}"
                    logger.warning(f"Gemini provider exception: {type(ex).__name__}")
                    break

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        log_processing_event("gemini_explanation_failed", {
            "status": "ai_unavailable",
            "latency_ms": elapsed_ms,
            "error_type": last_error_reason,
        })

        return AIExplanation(
            status=AIExplanationStatus.AI_UNAVAILABLE,
            provider="Google Gemini",
            model=self.model_name,
            status_reason=last_error_reason,
        )

    def _execute_api_call(self, client: Any, system_instruction: str, user_prompt: str) -> AIExplanation:
        """Low-level SDK call with structured output schema configuration."""
        from google.genai import types

        # Build GenerateContentConfig using official SDK types
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=settings.gemini_temperature,
            response_mime_type="application/json",
            response_schema=GeminiStructuredResponse,
        )

        models_to_try = [self.model_name]
        for fallback_model in ("gemini-3.5-flash", "gemini-3.8-flash"):
            if fallback_model not in models_to_try:
                models_to_try.append(fallback_model)

        response = None
        used_model = self.model_name
        last_error = None

        for model_candidate in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_candidate,
                    contents=user_prompt,
                    config=config,
                )
                used_model = model_candidate
                break
            except Exception as ex:
                err_text = str(ex).lower()
                if "404" in err_text or "not found" in err_text or "no longer available" in err_text:
                    logger.warning(f"Model {model_candidate} unavailable (404/retired), attempting fallback.")
                    last_error = ex
                    continue
                raise

        if response is None and last_error:
            raise last_error

        if not response or not response.text:
            raise ValueError("Empty response received from Gemini.")

        raw_json = response.text.strip()
        # Clean any accidental markdown wrap
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:]
        if raw_json.startswith("```"):
            raw_json = raw_json[3:]
        if raw_json.endswith("```"):
            raw_json = raw_json[:-3]
        raw_json = raw_json.strip()

        parsed_data = json.loads(raw_json)
        validated = GeminiStructuredResponse.model_validate(parsed_data)

        # Convert List[TestExplanationItem] to Dict[str, str] for AIExplanation model
        per_test_dict = {}
        if isinstance(validated.per_test_explanations, list):
            for item in validated.per_test_explanations:
                if hasattr(item, "test_name") and hasattr(item, "explanation"):
                    per_test_dict[item.test_name] = item.explanation
                elif isinstance(item, dict) and "test_name" in item and "explanation" in item:
                    per_test_dict[item["test_name"]] = item["explanation"]
        elif isinstance(validated.per_test_explanations, dict):
            per_test_dict = validated.per_test_explanations

        return AIExplanation(
            status=AIExplanationStatus.COMPLETED,
            provider="Google Gemini",
            model=used_model,
            summary_text=validated.summary_text,
            per_test_explanations=per_test_dict,
            limitations_and_uncertainty=validated.limitations_and_uncertainty,
            questions_for_doctor=validated.questions_for_doctor,
            disclaimer=validated.disclaimer,
            status_reason="Explanation successfully generated and validated.",
        )


gemini_service = GeminiService()
