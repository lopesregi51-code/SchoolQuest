# Script para reiniciar o backend limpo
# Mata todos os processos Python/Uvicorn e reinicia

Write-Host "=== Reiniciando Backend SchoolQuest ===" -ForegroundColor Cyan

# Matar todos os processos python que possam estar rodando uvicorn
Write-Host "`nMatando processos Python antigos..." -ForegroundColor Yellow
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

Write-Host "`nIniciando backend..." -ForegroundColor Green
Write-Host "Executando: py -m uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host "`nO servidor estará disponível em: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar o servidor`n" -ForegroundColor Gray
Write-Host "⚠️  Para resetar o banco de dados, use o endpoint /admin/database/reset via API" -ForegroundColor Yellow

# Iniciar o uvicorn
py -m uvicorn app.main:app --reload
