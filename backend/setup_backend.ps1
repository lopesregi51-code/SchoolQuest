# Script para configurar e iniciar o backend do SchoolQuest
# Execute este arquivo: .\setup_backend.ps1

Write-Host "🚀 Configurando Backend do SchoolQuest..." -ForegroundColor Cyan
Write-Host ""

# Navegar para o diretório do backend
# Navegar para o diretório do script
Set-Location $PSScriptRoot

# Ativar ambiente virtual do SIAEP (que já existe)
Write-Host "📦 Ativando ambiente virtual..." -ForegroundColor Yellow
& "..\venv\Scripts\Activate.ps1"

# Instalar uvicorn
Write-Host "📥 Instalando uvicorn..." -ForegroundColor Yellow
python -m pip install uvicorn[standard] --quiet

# Criar usuários de teste
Write-Host ""
Write-Host "👥 Criando usuários de teste..." -ForegroundColor Yellow
python create_test_user.py

# Iniciar servidor
Write-Host ""
Write-Host "🌐 Iniciando servidor FastAPI..." -ForegroundColor Green
Write-Host "Backend rodando em: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Documentação: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn app.main:app --reload
