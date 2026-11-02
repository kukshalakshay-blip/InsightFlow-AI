# InsightFlow-AI — Analysis Orchestrator Upgrade

## Included files

Copy the contents of this ZIP into the root of your existing repository, preserving folders:

- `app/services/analysis_orchestrator.py` — new deterministic orchestration service.
- `app/services/insight_engine.py` — backward-compatible optional precomputed findings support.
- `app/pages/insights.py` — reuses orchestrated results; removes duplicate insight/context/business-rule execution.
- `app/pages/reports.py` — reuses the same orchestrated results; PDF generation API is unchanged.
- `tests/test_analysis_orchestrator.py` — new orchestration tests.
- `verify_orchestrator.ps1` — focused and full regression verification.

The package intentionally does not modify the PDF generator, dataset-signature service, AI service, or session-state service.

## Apply

1. Make sure your working tree is clean and your latest changes are pushed.
2. Extract this ZIP directly into `C:\project\DA\insightflow`.
3. Allow Windows to overwrite the two existing page/service files when prompted.
4. Activate your environment:

   ```powershell
   conda activate insightflow
   ```

5. Run the verification script from the repository root:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\verify_orchestrator.ps1
   ```

6. Do not commit unless all three verification stages pass.

## What changes

`run_deterministic_analysis(df)` calls visualization recommendation, deterministic insight, and business recommendation engines once. It returns an `AnalysisResult` containing the summary, recommendations, computed findings, and AI-ready context. The Insights and Reports pages consume that shared result.

`build_analysis_context(df, recommendations)` remains valid for existing callers. The optional `deterministic_findings` parameter allows the orchestrator to pass already-computed findings, preventing a second call to `generate_insight`.

Gemini remains button-triggered from the Insights page. The orchestrator does not call Gemini and has no Streamlit dependency.

## After successful verification

Inspect:

```powershell
git status
git diff --check
git diff
```

Then commit and push:

```powershell
git add app/services/analysis_orchestrator.py app/services/insight_engine.py app/pages/insights.py app/pages/reports.py tests/test_analysis_orchestrator.py verify_orchestrator.ps1 README_APPLY.txt
git commit -m "refactor: centralize deterministic analysis orchestration"
git push origin main
```

If any test fails, do not commit. Share the complete terminal output so the failure can be diagnosed first.
