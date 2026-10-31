$ErrorActionPreference = "Stop"

Write-Host "`n[1/4] Focused data-validator tests" -ForegroundColor Cyan
python -m pytest tests/test_data_validator.py -q
if ($LASTEXITCODE -ne 0) { throw "Data-validator tests failed." }

Write-Host "`n[2/4] Complete project test suite" -ForegroundColor Cyan
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Full project test suite failed." }

Write-Host "`n[3/4] Git whitespace check" -ForegroundColor Cyan
git diff --check
if ($LASTEXITCODE -ne 0) { throw "git diff --check failed." }

Write-Host "`n[4/4] Changed files" -ForegroundColor Cyan
git status --short

Write-Host "`nVerification completed successfully. Review git status before committing." -ForegroundColor Green
