# 🧪 Guia de Testes - SchoolQuest v1.2.0

## 📋 Pré-requisitos

- [x] Python 3.8+ instalado
- [x] Node.js 16+ instalado
- [x] Navegador moderno (Chrome, Firefox, Edge)

---

## 🚀 Passo 1: Preparar Ambiente

### 1.1 Limpar Banco de Dados (Importante!)

```bash
# Deletar banco antigo para criar novas tabelas
cd c:\projetos\SchoolQuest\backend
del schoolquest.db
```

### 1.2 Instalar Dependências Backend

```bash
cd c:\projetos\SchoolQuest\backend
pip install -r requirements.txt
```

### 1.3 Instalar Dependências Frontend

```bash
cd c:\projetos\SchoolQuest\frontend
npm install
```

**Opcional:** Corrigir warning TypeScript
```bash
npm install --save-dev @types/node
```

---

## 🎬 Passo 2: Iniciar Aplicação

### Terminal 1 - Backend
```bash
cd c:\projetos\SchoolQuest\backend
uvicorn app.main:app --reload
```

**Aguarde ver:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Terminal 2 - Frontend
```bash
cd c:\projetos\SchoolQuest\frontend
npm run dev
```

**Aguarde ver:**
```
VITE ready in XXX ms
Local: http://localhost:5173/
```

---

## ✅ Passo 3: Teste 1 - Notificações WebSocket

### 3.1 Preparação
1. Abrir navegador: `http://localhost:5173`
2. Login: `admin@test.com` / `admin123`
3. Criar um professor e um aluno (ou usar existentes)

### 3.2 Abrir Duas Janelas

**Janela A (Professor):**
- Login como professor
- Ir para "Painel do Professor"

**Janela B (Aluno):**
- Login como aluno
- Ir para "Dashboard"
- **Verificar:** Console deve mostrar `WebSocket connected`

### 3.3 Testar Notificação de Missão

**Janela A (Professor):**
1. Criar nova missão:
   - Título: "Teste de Notificação"
   - Pontos: 100
   - Moedas: 50
2. Atribuir missão ao aluno

**Janela B (Aluno):**
1. **Verificar imediatamente:**
   - ✅ Toast aparece no canto superior direito
   - ✅ Sino mostra badge "1"
   - ✅ Som de notificação (se permitido)
2. Clicar no sino
   - ✅ Ver notificação "Nova Missão Atribuída"
3. Completar a missão

**Janela A (Professor):**
1. Ir para "Missões Pendentes"
2. Aprovar a missão

**Janela B (Aluno):**
1. **Verificar:**
   - ✅ Nova notificação "Missão Aprovada! 🎉"
   - ✅ XP e moedas atualizados

### 3.4 Resultado Esperado
- ✅ Notificações aparecem em < 1 segundo
- ✅ Badge atualiza automaticamente
- ✅ Dropdown mostra histórico
- ✅ Navegação funciona ao clicar

---

## 💬 Passo 4: Teste 2 - Chat de Clã

### 4.1 Criar Clã

**Janela A (Aluno 1):**
1. Ir para "Clãs"
2. Criar clã:
   - Nome: "Testadores"
   - Descrição: "Clã de testes"
3. Convidar outro aluno (buscar por email)

**Janela B (Aluno 2):**
1. Ir para "Clãs"
2. Aceitar convite

### 4.2 Testar Chat

**Ambas as Janelas:**
1. Ir para "Clãs"
2. Rolar até o final da página (Chat do Clã)

**Janela A:**
1. Enviar mensagem: "Olá do Aluno 1!"

**Janela B:**
1. **Verificar:**
   - ✅ Mensagem aparece instantaneamente
   - ✅ Avatar do Aluno 1 é exibido
   - ✅ Timestamp está correto

**Janela B:**
1. Enviar mensagem: "Olá do Aluno 2!"

**Janela A:**
1. **Verificar:**
   - ✅ Mensagem aparece em tempo real
   - ✅ Scroll automático para nova mensagem

### 4.3 Testar Recursos

1. **Contador de caracteres:**
   - Digitar mensagem longa
   - ✅ Ver "XXX/1000 caracteres"

2. **Agrupamento por data:**
   - ✅ Ver separador "Hoje"
   - ✅ Mensagens agrupadas corretamente

3. **Diferenciação visual:**
   - ✅ Suas mensagens à direita (azul)
   - ✅ Mensagens de outros à esquerda (cinza)

---

## 📱 Passo 5: Teste 3 - API Mobile

### 5.1 Obter Token JWT

**Usando PowerShell:**
```powershell
$body = @{
    username = "aluno@test.com"
    password = "senha123"
}

$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/token" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
$token = $response.access_token
Write-Host "Token: $token"
```

**Ou usando cURL:**
```bash
curl -X POST http://localhost:8000/auth/token -H "Content-Type: application/x-www-form-urlencoded" -d "username=aluno@test.com&password=senha123"
```

### 5.2 Testar Endpoints

**Health Check (sem autenticação):**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/mobile/v1/health"
```

**Perfil do Usuário:**
```powershell
$headers = @{
    Authorization = "Bearer $token"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/mobile/v1/me" -Headers $headers
```

**Estatísticas:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/mobile/v1/stats" -Headers $headers
```

**Missões:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/mobile/v1/missions?limit=5" -Headers $headers
```

**Ranking:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/mobile/v1/ranking" -Headers $headers
```

### 5.3 Resultado Esperado

Cada endpoint deve retornar JSON formatado:
- ✅ `/health` - Status "healthy"
- ✅ `/me` - Dados do usuário
- ✅ `/stats` - Estatísticas agregadas
- ✅ `/missions` - Lista de missões
- ✅ `/ranking` - Top 10 + posição

---

## 🔍 Passo 6: Verificar Banco de Dados

```bash
cd c:\projetos\SchoolQuest\backend
sqlite3 schoolquest.db
```

**Comandos SQL:**
```sql
-- Ver todas as tabelas
.tables

-- Verificar mensagens de chat
SELECT * FROM clan_messages ORDER BY created_at DESC LIMIT 5;

-- Verificar device tokens
SELECT * FROM device_tokens;

-- Sair
.quit
```

**Resultado Esperado:**
- ✅ Tabela `clan_messages` existe
- ✅ Tabela `device_tokens` existe
- ✅ Mensagens do chat estão salvas

---

## 🐛 Solução de Problemas

### Problema: WebSocket não conecta

**Sintoma:** Console mostra erro de WebSocket

**Solução:**
1. Verificar se backend está rodando
2. Verificar URL do WebSocket em `useWebSocket.ts`
3. Limpar cache do navegador (Ctrl+Shift+Del)

### Problema: Chat não aparece

**Sintoma:** Componente de chat não é exibido

**Solução:**
1. Verificar se está em um clã
2. Atualizar página (F5)
3. Verificar console por erros

### Problema: API Mobile retorna 401

**Sintoma:** "Unauthorized" ao chamar endpoints

**Solução:**
1. Verificar se token está correto
2. Gerar novo token
3. Verificar header `Authorization: Bearer TOKEN`

### Problema: Tabelas não existem

**Sintoma:** Erro ao consultar `clan_messages`

**Solução:**
```bash
# Deletar banco e reiniciar backend
cd backend
del schoolquest.db
uvicorn app.main:app --reload
```

---

## ✅ Checklist de Testes

### Notificações WebSocket
- [ ] WebSocket conecta (ver console)
- [ ] Notificação de missão atribuída
- [ ] Notificação de missão aprovada
- [ ] Badge atualiza
- [ ] Toast aparece
- [ ] Som funciona (opcional)
- [ ] Dropdown mostra histórico
- [ ] Marcar como lida funciona

### Chat de Clã
- [ ] Criar clã
- [ ] Convidar membro
- [ ] Aceitar convite
- [ ] Enviar mensagem
- [ ] Receber mensagem em tempo real
- [ ] Agrupamento por data
- [ ] Avatares aparecem
- [ ] Contador de caracteres
- [ ] Scroll automático

### API Mobile
- [ ] Health check funciona
- [ ] Obter token JWT
- [ ] GET /me retorna perfil
- [ ] GET /stats retorna estatísticas
- [ ] GET /missions retorna missões
- [ ] GET /ranking retorna top 10
- [ ] Versionamento (/v1/) funciona

### Banco de Dados
- [ ] Tabela clan_messages existe
- [ ] Tabela device_tokens existe
- [ ] Mensagens são salvas
- [ ] Timestamps corretos

---

## 📊 Relatório de Testes

Após completar os testes, preencha:

**Data:** ___________  
**Testador:** ___________

**Funcionalidades Testadas:**
- [ ] Notificações WebSocket - Status: ___________
- [ ] Chat de Clã - Status: ___________
- [ ] API Mobile - Status: ___________

**Bugs Encontrados:**
1. ___________
2. ___________
3. ___________

**Observações:**
___________________________________________
___________________________________________

---

**Versão:** 1.2.0  
**Data do Guia:** 2025-11-23  
**Próximo:** Corrigir bugs encontrados ou continuar implementação
