# InsightFlow AI — Source Audit and Release-Candidate Record

## Scope reviewed

Reviewed the supplied ZIP's actual source tree: application entry point, six Streamlit pages, service layer, settings, README, tests, and dependency references. The archive was missing runtime/development dependency manifests and several deployment/configuration files. It also contained local datasets and compiled Python bytecode.

## Changes included in this package

- Added runtime and development dependency manifests, including the missing Plotly static-image renderer dependency (Kaleido).
- Replaced the invalid Pydantic v1 `BaseSettings` import with Pydantic Settings v2 configuration and validated environment-backed settings.
- Added `.env.example`, `.gitignore`, `.dockerignore`, Streamlit configuration, Dockerfile, Compose file, pytest/Ruff configuration, and MIT license.
- Reworked the upload page to avoid repeatedly parsing and validating an unchanged upload on Streamlit reruns.
- Added configurable upload-size validation.
- Preserved an existing valid dataset when a replacement upload fails to load or validate.
- Invalidated cached AI and PDF artifacts when a different valid dataset replaces the active dataset.
- Improved the landing page with a guided workflow, active-dataset summary, and direct navigation.
- Added Insights-page smoke tests and settings tests; aligned report-page tests with the current analysis-orchestrator architecture.
- Replaced the README with accurate setup, usage, testing, deployment, data-handling, and limitation documentation.
- Removed user datasets, `.pyc` files, and cache directories from this distributable archive. Empty data folders remain with `.gitkeep` files.

## Verification performed in this audit environment

- Python compilation: `python -m compileall -q app main.py scripts tests` passed.
- Core services and integration tests: 436 passed; one chart-image export test was deselected because Kaleido was not installed in this isolated audit environment. Kaleido 0.2.1 has been added to `requirements.txt` and Plotly is constrained to the compatible 5.x line.
- Settings tests: 4 passed.
- Report-page tests: 5 passed using a lightweight Streamlit API shim because Streamlit itself was not installed in the audit environment. This verifies page logic under the existing mocks, not browser rendering.
- AI service and integration imports used a local Google GenAI SDK shim because the SDK was not installed; tests mock the client and did not make external API calls.

## Not verified here

- Full test-suite execution in the actual InsightFlow Conda environment. The audit environment did not contain Streamlit, Google GenAI, or Kaleido, and outbound package installation was unavailable.
- Actual Streamlit AppTest/browser interaction for upload and Insights pages.
- Real Gemini API response with a user-provided key.
- Docker image build and container health check.
- Large-file performance and concurrent multi-user behavior.

## Product boundaries

- The current Streamlit upload control exposes CSV, XLSX, and XLS. The lower-level loader also supports JSON and Parquet, but those formats are not exposed in the UI.
- Uploaded datasets are session-scoped; no persistent database/object store or user account system is implemented.
- No authentication, tenant isolation, or production observability stack is included.
- Gemini analysis is optional and sends the prepared analytical context to Google's API only after the user explicitly requests AI analysis.

## Release status

This archive is a consolidated, source-reviewed **release candidate** with missing project scaffolding supplied and identified source-level issues addressed. It is not honestly described as fully runtime-certified until the target machine completes the full verification script, Streamlit smoke tests, and Docker build. No source package can guarantee that future audits or environment-specific checks will never be needed.
