# 🚀 Script de Inicialização Completa do SchoolQuest
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  🎮 SCHOOLQUEST - Setup Completo" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# Navegar para diretório do script
Set-Location $PSScriptRoot

# Ativar ambiente virtual (se existir localmente)
if (Test-Path "..\venv\Scripts\Activate.ps1") {
    Write-Host "📦 Ativando ambiente virtual..." -ForegroundColor Yellow
    & "..\venv\Scripts\Activate.ps1"
}
elseif (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "📦 Ativando ambiente virtual local..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}
else {
    Write-Host "⚠️ Nenhum ambiente virtual encontrado. Usando Python do sistema." -ForegroundColor Yellow
}

# Verificar/instalar uvicorn
Write-Host "📥 Verificando dependências..." -ForegroundColor Yellow
py -m pip install --quiet uvicorn[standard] 2>$null

# Criar/atualizar usuários
Write-Host ""
Write-Host "👥 Criando usuários de teste..." -ForegroundColor Yellow
py create_test_user.py

# Popular com dados de demonstração
Write-Host ""
Write-Host "🎯 Criando missões de demonstração..." -ForegroundColor Yellow
py populate_demo_data.py

# Iniciar servidor
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "  ✅ Backend Configurado com Sucesso!" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""
Write-Host "🌐 SERVIÇOS DISPONÍVEIS:" -ForegroundColor Cyan
Write-Host "   Backend API:      http://127.0.0.1:8000" -ForegroundColor White
Write-Host "   Documentação:     http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "📝 CREDENCIAIS:" -ForegroundColor Cyan
Write-Host "   Aluno:      aluno@escola.com / senha123" -ForegroundColor White
Write-Host "   Professor:  professor@escola.com / senha123" -ForegroundColor White
Write-Host ""
Write-Host "🎯 O sistema já possui 6 missões de demonstração!" -ForegroundColor Green
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o servidor" -ForegroundColor Yellow
Write-Host ""

py -m uvicorn app.main:app --reload
