import logging
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors
from pydantic import BaseModel, Field, ValidationError


load_dotenv()

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-3.5-flash-lite"
MAX_RETRIES = 4
REQUEST_TIMEOUT_MS = 30_000

# ==========================================================
# AI RESPONSE SCHEMA
# ==========================================================

class AIAnalysis(BaseModel):
    """Structured response expected from the AI analyst."""

    executive_summary: str = Field(
        description=(
            "A concise summary of the most important "
            "business-level findings."
        )
    )

    key_findings: list[str] = Field(
        description=(
            "Three to five important findings supported "
            "by the provided analytical facts."
        )
    )

    recommendations: list[str] = Field(
        description=(
            "Three to five practical business recommendations "
            "based only on the provided analytical facts."
        )
    )

    risks_or_anomalies: list[str] = Field(
        description=(
            "Important risks, unusual patterns, or areas "
            "that deserve further investigation. Return an "
            "empty list when none are supported by the data."
        )
    )


# ==========================================================
# GEMINI CLIENT
# ==========================================================

def get_gemini_client():
    """Create a Gemini client using the environment API key."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured.")

    return genai.Client(
        api_key=api_key,
        http_options={
            "timeout": REQUEST_TIMEOUT_MS,
        },
    )


# ==========================================================
# RETRY CLASSIFICATION
# ==========================================================

def _is_retryable_error(error: Exception) -> bool:
    """Return whether a failure is likely to succeed on retry."""

    if isinstance(error, errors.ServerError):
        return True

    if isinstance(error, errors.APIError):
        # Rate limiting and transient server-side failures.
        return getattr(error, "code", None) in (408, 429, 500, 502, 503, 504)

    # Do not retry malformed output or schema validation failures.
    if isinstance(error, (ValueError, ValidationError)):
        return False

    # Unknown exceptions may be programming/configuration errors.
    # Fail fast rather than repeatedly issuing requests.
    return False


# ==========================================================
# AI ANALYSIS
# ==========================================================

def generate_ai_analysis(
    analysis_context: dict,
) -> AIAnalysis:
    """
    Generate structured business analysis from deterministic facts.

    Only classified transient API failures are retried. Invalid
    responses and non-retryable errors are raised immediately.
    """

    client = get_gemini_client()

    prompt = f"""
You are the analytical intelligence layer of InsightFlow,
an automated data analysis platform.

Your job is to interpret the analytical facts provided below.

IMPORTANT RULES:

1. Use ONLY the information contained in the provided context.
2. Do NOT invent numbers, trends, relationships, or causes.
3. Do NOT claim causation unless the data explicitly supports it.
4. Prefer specific numerical findings when available.
5. Focus on business meaning rather than describing Python,
   Pandas, charts, or implementation details.
6. Recommendations must be practical and connected to the findings.
7. If the available information is insufficient for a claim,
   say so instead of guessing.
8. Distinguish observed facts from interpretations and hypotheses.
9. When stating a numerical finding, preserve its actual value
   and meaning from the supplied context.
10. Do not imply that a correlation, statistical outlier, or
    unusual pattern proves a business cause or data error.
11. Explain the evidence supporting an important conclusion
    whenever that evidence is available in the context.
12. If the context contains conflicting or insufficient evidence,
    acknowledge the limitation instead of forcing a conclusion.
13. Treat business_recommendations as rule-based findings and
    suggested actions, not as proof of causation.
14. Preserve the distinction between observed_finding,
    suggested_action, and rationale.
15. Do not describe a suggested action as an action already taken.
16. Prioritize high-priority findings when discussing business risks,
    while considering the supporting evidence.

ANALYTICAL CONTEXT:

{analysis_context}

Return a concise professional analysis suitable for a
business analyst or executive dashboard.
"""

    for attempt in range(MAX_RETRIES):
        try:
            interaction = client.interactions.create(
                model=MODEL_NAME,
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": AIAnalysis.model_json_schema(),
                },
                stream=False,
            )

            output_text = getattr(interaction, "output_text", None)

            if not output_text:
                raise ValueError("Gemini returned no output.")

            return AIAnalysis.model_validate_json(output_text)

        except Exception as error:
            is_final_attempt = attempt == MAX_RETRIES - 1

            if is_final_attempt or not _is_retryable_error(error):
                logger.error(
                    "Gemini analysis failed on attempt %s/%s.",
                    attempt + 1,
                    MAX_RETRIES,
                    exc_info=True,
                )
                raise

            delay = 2 ** attempt

            logger.warning(
                "Transient Gemini failure on attempt %s/%s. "
                "Retrying in %s seconds.",
                attempt + 1,
                MAX_RETRIES,
                delay,
                exc_info=True,
            )

            time.sleep(delay)

    raise RuntimeError("Gemini request failed after all retry attempts.")
