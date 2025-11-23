# Script COMPLETO para reiniciar o Frontend com Tailwind v3
Write-Host "🔄 Reiniciando Frontend do SchoolQuest..." -ForegroundColor Cyan

# Navegar para frontend
Set-Location "C:\Users\regin\SISTEMA_SIAEP\SchoolQuest\frontend"

# Parar servidor anterior
Write-Host "🛑 Parando processos anteriores..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*frontend*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Limpar cache
Write-Host "🧹 Limpando cache..." -ForegroundColor Yellow
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue

# Reinstalar
Write-Host "📥 Instalando dependências..." -ForegroundColor Yellow
npm install

# Instalar Tailwind v3
Write-Host "🎨 Instalando Tailwind CSS v3..." -ForegroundColor Yellow
npm install -D tailwindcss@3.4.15 postcss autoprefixer

# Iniciar servidor
Write-Host ""
Write-Host "✅ Configuração completa!" -ForegroundColor Green
Write-Host "🚀 Iniciando servidor..." -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Yellow
Write-Host ""

npm run dev
