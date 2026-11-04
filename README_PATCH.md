# InsightFlow — Intelligent Data Understanding (Milestone 1 patch)

This patch adds a privacy-conscious dataset profile and Gemini-powered domain/column understanding.
It does **not** change existing analysis pages or replace deterministic calculations.

## Files
- `app/intelligence/__init__.py`
- `app/intelligence/dataset_understanding.py`
- `tests/test_dataset_understanding.py`

## Integration status
This is an isolated first milestone. It is intentionally not wired into the upload flow yet.
Next, after the tests pass in the user's `insightflow` environment, we will connect the result to the analysis orchestrator and display the detected domain and semantic map. This avoids changing the currently working workflow before the new component is validated.

## API behavior
- Uses the existing Gemini client factory in `app.services.ai_service`.
- Uses `INSIGHTFLOW_GEMINI_MODEL` through typed application settings.
- Sends schema and aggregate statistics only; no row samples or raw cell values.
- Validates Gemini's response with Pydantic and rejects mappings to nonexistent columns.
- Does not execute model-generated Python or SQL.

## Install
Copy the `app` and `tests` folders into the existing project root, preserving folder structure. Then run:

```powershell
python -m pytest tests/test_dataset_understanding.py -q
```

The live Gemini call is not exercised by these unit tests. A configured `GEMINI_API_KEY` is required when `understand_dataset(df)` is called.
