# Script COMPLETO para reiniciar o Frontend com Tailwind v3
Write-Host "🔧 SOLUÇÃO COMPLETA - Reiniciando Frontend" -ForegroundColor Cyan
Write-Host ""

# 1. Parar servidor anterior
Write-Host "1️⃣ Parando servidor Vite..." -ForegroundColor Yellow
Get-Process node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*frontend*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

#  2. Navegar para diretório do script
Set-Location $PSScriptRoot

# 3. Limpar cache e node_modules
Write-Host "2️⃣ Limpando cache e reinstalando..." -ForegroundColor Yellow
Remove-Item -Recurse -Force .\node_modules -ErrorAction SilentlyContinue
Remove-Item -Force package-lock.json -ErrorAction SilentlyContinue

# 4. Reinstalar TUDO do zero
Write-Host "3️⃣ Instalando dependências..." -ForegroundColor Yellow
npm install

# 5. Instalar Tailwind v3 especificamente
Write-Host "4️⃣ Instalando Tailwind CSS v3..." -ForegroundColor Yellow
npm install -D tailwindcss@3.4.15 postcss autoprefixer

# 6. Iniciar servidor
Write-Host ""
Write-Host "✅ Configuração completa!" -ForegroundColor Green
Write-Host "🚀 Iniciando servidor..." -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para parar" -ForegroundColor Yellow
Write-Host ""

npm run dev
