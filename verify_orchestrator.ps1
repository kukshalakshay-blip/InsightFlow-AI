$ErrorActionPreference = "Stop"

Write-Host "`n=== InsightFlow Orchestrator Upgrade Verification ===" -ForegroundColor Cyan

Write-Host "`n[1/3] Focused orchestrator and insight-engine tests..." -ForegroundColor Yellow

python -m pytest -q tests/test_analysis_orchestrator.py tests/test_insight_engine.py

if ($LASTEXITCODE -ne 0) {
    throw "Focused tests failed. Do not commit."
}

Write-Host "`n[2/3] Session-state and integration tests..." -ForegroundColor Yellow

python -m pytest -q tests/test_session_state.py tests/test_integration_pipeline.py

if ($LASTEXITCODE -ne 0) {
    throw "Integration tests failed. Do not commit."
}

Write-Host "`n[3/3] Complete regression suite..." -ForegroundColor Yellow

python -m pytest -q

if ($LASTEXITCODE -ne 0) {
    throw "Full regression suite failed. Do not commit."
}

Write-Host "`nAll verification stages passed!" -ForegroundColor Green
Write-Host "Review git diff before committing." -ForegroundColor Green
