# Script de lancement - Startup AI Agent (Optimisé)
$pythonExecutable = (Get-Command python).Source
$pythonPath = Split-Path $pythonExecutable

# Vérifier la clé API
if (-not (Get-Content .env | Select-String "GOOGLE_API_KEY=.+")) {
    Write-Host "ERREUR: GOOGLE_API_KEY non configurée dans .env" -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Startup AI Agent - Lancement rapide" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Demarrage du backend FastAPI..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath "$pythonPath\python.exe" -ArgumentList "-m uvicorn main:app --reload --port 8000"

Write-Host "[2/3] Attente du backend..." -ForegroundColor Yellow
$retries = 0
do {
    Start-Sleep -Seconds 1
    $retries++
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method GET -ErrorAction Stop
        Write-Host "  Backend OK!" -ForegroundColor Green
        break
    }
    catch {
        if ($retries -ge 10) {
            Write-Host "  Backend n'a pas demarre apres 10s" -ForegroundColor Red
            break
        }
    }
} while ($true)

Write-Host "[3/3] Demarrage de Streamlit..." -ForegroundColor Green
Write-Host ""
Write-Host "  -> Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "  -> Frontend:  http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
& "$pythonPath\python.exe" -m streamlit run streamlit_app.py
