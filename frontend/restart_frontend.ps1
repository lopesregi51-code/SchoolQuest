# Script para reiniciar o Frontend com configuração correta
Write-Host "🔄 Reiniciando Frontend do SchoolQuest..." -ForegroundColor Cyan

# Navegar para o diretório do frontend
# Navegar para o diretório do script
Set-Location $PSScriptRoot

# Parar qualquer processo npm anterior (opcional)
Write-Host "🛑 Parando processos anteriores..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*frontend*" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Aguardar um momento
Start-Sleep -Seconds 2

# Limpar cache do Vite (isso às vezes resolve problemas de config)
Write-Host "🧹 Limpando cache..." -ForegroundColor Yellow
Remove-Item -Recurse -Force .\.vite -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\node_modules\.vite -ErrorAction SilentlyContinue

# Iniciar servidor
Write-Host ""
Write-Host "🚀 Iniciando servidor Vite..." -ForegroundColor Green
Write-Host "Frontend rodando em: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

npm run dev
