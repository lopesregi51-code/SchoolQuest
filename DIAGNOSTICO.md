# 🔍 Script de Diagnóstico - SchoolQuest

## Teste 1: Verificar se Backend está Rodando

```powershell
# Testar endpoint raiz
Invoke-RestMethod -Uri "http://localhost:8000/"
```

**Resultado Esperado:**
```json
{
  "message": "SchoolQuest API",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## Teste 2: Verificar Endpoints do Chat

```powershell
# Obter token primeiro
$body = @{
    username = "aluno@test.com"
    password = "senha123"
}
$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/token" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
$token = $response.access_token

# Testar endpoint de chat (deve dar 403 se não estiver em clã)
$headers = @{
    Authorization = "Bearer $token"
}
Invoke-RestMethod -Uri "http://localhost:8000/chat/clan/1/messages" -Headers $headers
```

---

## Teste 3: Verificar Perfil do Usuário

```powershell
# Usar o token do teste anterior
Invoke-RestMethod -Uri "http://localhost:8000/users/1/profile" -Headers $headers
```

---

## Teste 4: Verificar Documentação da API

Abrir no navegador: http://localhost:8000/docs

**Verificar se aparecem:**
- ✅ `/chat/clan/{clan_id}/messages` (GET, POST)
- ✅ `/api/mobile/v1/me` (GET)
- ✅ `/ws/{user_id}` (WebSocket)

---

## Possíveis Problemas e Soluções

### Problema 1: Backend não recarregou
**Sintoma:** Endpoints de chat não aparecem em `/docs`

**Solução:**
```powershell
# Parar o backend (Ctrl+C no terminal)
# Reiniciar:
cd c:\projetos\SchoolQuest\backend
py -m uvicorn app.main:app --reload
```

### Problema 2: Erro no perfil
**Sintoma:** "Erro ao carregar perfil"

**Causas possíveis:**
1. Usuário não existe no banco
2. Erro no campo `posts` (já corrigido)
3. Token JWT inválido

**Solução:**
- Verificar console do navegador (F12)
- Ver erro específico na aba Network

### Problema 3: Chat 404
**Sintoma:** "Not Found" ao enviar mensagem

**Causas possíveis:**
1. Router não foi incluído (já corrigido)
2. Backend não recarregou
3. URL incorreta no frontend

**Solução:**
- Verificar `/docs` se endpoint existe
- Recarregar página do frontend (F5)

---

## Como Usar Este Script

1. **Abrir PowerShell**
2. **Copiar e colar os comandos** um por vez
3. **Anotar os resultados** (sucesso ou erro)
4. **Me enviar os erros** que aparecerem

---

## Informações para Debug

**Por favor, me envie:**

1. **Console do navegador** (F12 → Console)
   - Copie qualquer erro em vermelho

2. **Aba Network** (F12 → Network)
   - Filtre por "Fetch/XHR"
   - Clique na requisição que falhou
   - Me envie o Status Code e a Response

3. **URL que está tentando acessar**
   - Ex: `http://localhost:5173/profile/1`

---

**Última atualização:** 2025-11-23 20:07
