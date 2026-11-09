$ProjectRoot = $PSScriptRoot

Write-Host "Starting AI Intake Validator development environment..."

# ------------------------------------------------------------
# PostgreSQL
# ------------------------------------------------------------

Write-Host "Starting PostgreSQL container..."

docker start ai-postgres

# ------------------------------------------------------------
# FastAPI
# ------------------------------------------------------------

Write-Host "Starting FastAPI..."

Start-Process powershell -ArgumentList `
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectRoot'; .\venv\Scripts\Activate.ps1; python -m uvicorn app.main:app --reload"

# ------------------------------------------------------------
# Node API Gateway
# ------------------------------------------------------------

Write-Host "Starting Node API..."

Start-Process powershell -ArgumentList `
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectRoot\node-api'; npm run dev"

# ------------------------------------------------------------
# React Frontend
# ------------------------------------------------------------

Write-Host "Starting React frontend..."

Start-Process powershell -ArgumentList `
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectRoot\web'; npm run dev"

# ------------------------------------------------------------
# Transactional Outbox Publisher
# ------------------------------------------------------------

Write-Host "Starting outbox publisher..."

Start-Process powershell -ArgumentList `
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectRoot'; .\venv\Scripts\Activate.ps1; python -m app.messaging.outbox_publisher"

Write-Host ""
Write-Host "Development services launched."
Write-Host ""
Write-Host "Validation consumer is NOT started automatically."
Write-Host "Run manually when needed:"
Write-Host ""
Write-Host "    python -m app.consumers.intake_validation_consumer"