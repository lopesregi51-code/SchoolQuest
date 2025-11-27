# Script para iniciar o servidor frontend do SchoolQuest

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  SchoolQuest - Frontend Server" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Navegar para o diretorio do frontend
Set-Location -Path $PSScriptRoot

Write-Host "Diretorio: $PWD" -ForegroundColor Yellow
Write-Host ""

# Verificar se node_modules existe
if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules nao encontrado. Instalando dependencias..." -ForegroundColor Yellow
    npm install
    Write-Host ""
}

Write-Host "Iniciando servidor frontend..." -ForegroundColor Green
Write-Host "   URL: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

# Iniciar o servidor de desenvolvimento
npm run dev
