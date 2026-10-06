import os
import time

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field


load_dotenv()


# ==========================================================
# AI RESPONSE SCHEMA
# ==========================================================

class AIAnalysis(BaseModel):
    """
    Structured response expected from the AI analyst.
    """

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
    """
    Create a Gemini client using the environment API key.
    """

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured."
        )

    return genai.Client(
        api_key=api_key
    )


# ==========================================================
# AI ANALYSIS
# ==========================================================

def generate_ai_analysis(
    analysis_context: dict,
) -> AIAnalysis:
    """
    Send deterministic analytical facts to Gemini
    and receive a structured business analysis.

    Temporary Gemini service failures are retried
    using exponential backoff.
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

ANALYTICAL CONTEXT:

{analysis_context}

Return a concise professional analysis suitable for a
business analyst or executive dashboard.
"""

    # ------------------------------------------------------
    # RETRY CONFIGURATION
    # ------------------------------------------------------

    max_retries = 4

    for attempt in range(max_retries):

        try:

            # --------------------------------------------------
            # SEND REQUEST TO GEMINI
            # --------------------------------------------------

            interaction = client.interactions.create(
                model="gemini-3.5-flash-lite",
                input=prompt,
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": AIAnalysis.model_json_schema(),
                },
                stream=False,
            )

            # --------------------------------------------------
            # VALIDATE RESPONSE
            # --------------------------------------------------

            output_text = getattr(
                interaction,
                "output_text",
                None,
            )

            if not output_text:
                raise ValueError(
                    "Gemini returned no output."
                )

            return AIAnalysis.model_validate_json(
                output_text
            )

        # ------------------------------------------------------
        # TEMPORARY FAILURE
        # ------------------------------------------------------

        except Exception as error:

            # If this was the final attempt,
            # allow the original error to reach the caller.
            if attempt == max_retries - 1:
                raise error

            # Exponential backoff:
            #
            # attempt 0 → 1 second
            # attempt 1 → 2 seconds
            # attempt 2 → 4 seconds
            #
            delay = 2 ** attempt

            print(
                f"Gemini request failed. "
                f"Retrying in {delay} seconds..."
            )

            time.sleep(delay)

    raise RuntimeError(
        "Gemini request failed after all retry attempts."
    )