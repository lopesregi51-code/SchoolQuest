# Script para iniciar AMBOS os servidores do SchoolQuest

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  SchoolQuest - Iniciar Aplicacao" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

$projectRoot = $PSScriptRoot

# Funcao para iniciar processo em nova janela
function Start-ServerInNewWindow {
    param(
        [string]$Title,
        [string]$ScriptPath,
        [string]$WorkingDirectory
    )
    
    Write-Host "Iniciando $Title..." -ForegroundColor Green
    
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $ScriptPath -WorkingDirectory $WorkingDirectory
}

Write-Host "Iniciando servidores..." -ForegroundColor Cyan
Write-Host ""

# Iniciar Backend
Start-ServerInNewWindow -Title "Backend" -ScriptPath "$projectRoot\backend\start-backend.ps1" -WorkingDirectory "$projectRoot\backend"
Start-Sleep -Seconds 2

# Iniciar Frontend
Start-ServerInNewWindow -Title "Frontend" -ScriptPath "$projectRoot\frontend\start-frontend.ps1" -WorkingDirectory "$projectRoot\frontend"

Write-Host ""
Write-Host "Servidores iniciados!" -ForegroundColor Green
Write-Host ""
Write-Host "URLs:" -ForegroundColor Yellow
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Duas janelas do PowerShell foram abertas." -ForegroundColor Yellow
Write-Host "   Feche-as para parar os servidores." -ForegroundColor Yellow
Write-Host ""
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
