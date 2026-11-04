$ErrorActionPreference = "Stop"

Write-Host "[1/3] Checking Python syntax..." -ForegroundColor Cyan
python -m compileall -q app main.py scripts tests
if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }

Write-Host "[2/3] Running the complete test suite..." -ForegroundColor Cyan
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Test suite failed." }

Write-Host "[3/3] Checking required project files..." -ForegroundColor Cyan
$required = @(
    "main.py", "requirements.txt", "requirements-dev.txt", "README.md",
    "Dockerfile", "compose.yaml", ".env.example", "LICENSE"
)
foreach ($file in $required) {
    if (-not (Test-Path $file)) { throw "Missing required file: $file" }
}

Write-Host "Release verification completed successfully." -ForegroundColor Green
