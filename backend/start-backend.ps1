# Script para iniciar o servidor backend do SchoolQuest

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  SchoolQuest - Backend Server" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Navegar para o diretorio do backend
Set-Location -Path $PSScriptRoot

Write-Host "Diretorio: $PWD" -ForegroundColor Yellow
Write-Host ""

# Verificar se o ambiente virtual existe
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Ativando ambiente virtual..." -ForegroundColor Green
    & "venv\Scripts\Activate.ps1"
}
else {
    Write-Host "Ambiente virtual nao encontrado. Usando Python global..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Iniciando servidor backend na porta 8000..." -ForegroundColor Green
Write-Host "   URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

# Iniciar o servidor usando Python -m uvicorn
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
