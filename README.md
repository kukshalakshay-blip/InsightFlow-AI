# InsightFlow AI

InsightFlow AI is a Streamlit-based data analysis workspace that helps users upload tabular data, inspect data quality, explore visualizations, generate deterministic findings, optionally request AI-assisted interpretation, and export a PDF report.

## Features

- **Data upload:** Load CSV and Excel files.
- **Data validation and profiling:** Review dataset dimensions, column characteristics, missing values, and basic statistics.
- **Visualization recommendations:** Suggest charts based on column types and relationships.
- **Deterministic insights:** Explain distributions, correlations, category summaries, and time-series trends using calculated values.
- **Optional AI analysis:** Use the Gemini API to interpret a structured analytical context.
- **PDF reports:** Generate a downloadable report with analytical summaries and visualizations.
- **Automated tests:** Exercise core services, pages, reporting, and session-state behavior.

## Architecture

```text
main.py                  Streamlit entry point and navigation
app/pages/               Home, upload, profile, visualization, insights, reports
app/services/            Loading, validation, profiling, analysis, charts, AI, reports
app/core/                Shared application configuration
app/models/              Pydantic models
tests/                   Automated test suite
scripts/                 Optional command-line demos
```

The application separates page-level UI from reusable services. Statistical findings are calculated locally; the optional AI layer receives a structured context and should interpret, not replace, those calculations.

## Requirements

- Python 3.11 or another Python version compatible with the pinned dependencies
- pip
- A Gemini API key only if you want to use AI-assisted analysis

## Installation

Create and activate a virtual environment from the project root. For example, with Conda:

```powershell
conda create -n insightflow python=3.11 -y
conda activate insightflow
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

The `requirements.txt` file contains application dependencies. `requirements-dev.txt` installs those dependencies plus development tools and pytest.

## Configuration

Create a local `.env` file in the project root if you want Gemini-powered analysis:

```dotenv
GEMINI_API_KEY=replace_with_your_own_key
```

Never commit `.env` or share it in project archives. The app's non-AI analytical features should not require a Gemini key.

## Run the application

From the project root:

```powershell
streamlit run main.py
```

## Run tests

```powershell
python -m pytest
```

Pytest is configured to discover tests under `tests/`. Optional demos in `scripts/` are not executed during test collection.

## Optional demos

To run the recommendation demo with your own CSV file:

```powershell
python scripts/demo_recommendations.py path\to\your_dataset.csv
```

To run the AI demo, configure `GEMINI_API_KEY` first:

```powershell
python scripts/demo_ai.py
```

## Security and limitations

- Uploaded datasets may contain sensitive information; use appropriate local data-handling practices.
- AI output is generated text and should be checked against the deterministic findings before business decisions are made.
- Correlation and outlier detection indicate patterns, not causation or proof of data errors.
- The repository's automated tests do not replace an end-to-end smoke test in the target environment.

## License

See [LICENSE](LICENSE).
