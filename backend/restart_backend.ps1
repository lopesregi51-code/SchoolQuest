# Script para reiniciar o backend limpo
# Mata todos os processos Python/Uvicorn e reinicia

Write-Host "=== Reiniciando Backend SchoolQuest ===" -ForegroundColor Cyan

# Matar todos os processos python que possam estar rodando uvicorn
Write-Host "`nMatando processos Python antigos..." -ForegroundColor Yellow
Get-Process python* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Verificar se o banco de dados existe
if (Test-Path "schoolquest.db") {
    $response = Read-Host "`nBanco de dados encontrado. Deseja deletar? (s/n)"
    if ($response -eq 's' -or $response -eq 'S') {
        Remove-Item "schoolquest.db" -Force
        Write-Host "✓ Banco de dados deletado" -ForegroundColor Green
    }
}

Write-Host "`nIniciando backend..." -ForegroundColor Green
Write-Host "Executando: py -m uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host "`nO servidor estará disponível em: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar o servidor`n" -ForegroundColor Gray

# Iniciar o uvicorn
py -m uvicorn app.main:app --reload
