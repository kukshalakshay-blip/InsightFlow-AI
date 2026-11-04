# InsightFlow AI

InsightFlow AI is a Streamlit-based analytics workspace for tabular datasets. It combines deterministic data profiling, visualization recommendations, statistical findings, rule-based business recommendations, optional Gemini interpretation, and PDF export.

## Product capabilities

- CSV and Excel upload with validation and data preview.
- Dataset profiling, missing-value and duplicate summaries, and column-level characteristics.
- Automated visualization recommendations and interactive Plotly charts.
- Deterministic statistical findings and rule-based business recommendations.
- Optional Gemini-generated executive interpretation grounded in deterministic analysis.
- PDF reports with analytical findings, recommendations, and optional chart images.
- Dataset-signature-based invalidation of stale AI and PDF artifacts.

JSON and Parquet loading are supported by the lower-level loader service but are not exposed in the current Streamlit upload control.

## Requirements

- Python 3.11 (recommended; dependencies are tested/targeted for this version).
- pip.
- Gemini API key only for AI-assisted analysis. All deterministic features work without it.

## Local setup (Windows PowerShell)

```powershell
conda create -n insightflow python=3.11 -y
conda activate insightflow
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
streamlit run main.py
```

Open the local address printed by Streamlit, normally `http://localhost:8501`.

To enable Gemini, add your own `GEMINI_API_KEY` to `.env`. Never commit `.env` or share it in source archives.

## Run verification

```powershell
python -m pytest
python -m compileall -q app main.py
```

The chart-image export path uses Plotly + Kaleido. The pinned Kaleido 0.2.1 package includes its rendering runtime and avoids requiring a separately installed Chrome browser.

## Docker

```powershell
Copy-Item .env.example .env
# Add GEMINI_API_KEY to .env only if AI analysis is required.
docker compose up --build
```

Then open `http://localhost:8501`. To stop the service, run `docker compose down`.

## Repository layout

```text
main.py                  Streamlit entry point and navigation
app/pages/               User-facing Streamlit pages
app/services/            Loading, validation, profiling, analysis, charts, AI and PDF services
app/core/                Typed environment configuration
app/models/              Shared data models
data/                    Empty data directories; keep private datasets local
scripts/                 Optional command-line demos
tests/                   Automated tests
Dockerfile               Container image
compose.yaml             Local container orchestration
requirements.txt         Runtime dependencies
requirements-dev.txt     Runtime + development dependencies
```

## Data handling and limitations

- Uploaded data is held in the active Streamlit session; this project does not provide persistent user accounts or a database-backed dataset store.
- Do not upload confidential or regulated data to an environment you do not control.
- AI analysis sends a compact analytical context to Google's Gemini API when explicitly requested. Raw dataset rows are not intentionally sent by the AI service; inspect the context builder before using sensitive datasets.
- AI output is generated interpretation, not verified professional advice. Check conclusions against the underlying data.
- Correlation and outlier detection do not establish causation or prove data errors.
- The app is a single-user/session-oriented application. Multi-user authentication, tenant isolation, persistent storage, and operational monitoring are outside this release's current scope.

## License

MIT. See [LICENSE](LICENSE).
