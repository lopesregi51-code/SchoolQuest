# SchoolQuest Mobile API

## Visão Geral

A API Mobile do SchoolQuest fornece endpoints otimizados para aplicativos móveis nativos (iOS e Android), com respostas leves, versionamento e suporte a push notifications.

**Base URL:** `/api/mobile/v1`

---

## Autenticação

Todos os endpoints requerem autenticação via Bearer Token (JWT).

```http
Authorization: Bearer <seu_token_jwt>
```

Para obter o token, use o endpoint de login padrão:

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=usuario@email.com&password=senha123
```

---

## Endpoints

### 1. Perfil do Usuário

#### GET `/api/mobile/v1/me`

Retorna o perfil do usuário autenticado.

**Response:**
```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao@email.com",
  "papel": "aluno",
  "xp": 1500,
  "nivel": 15,
  "moedas": 250,
  "avatar_url": "/media/avatars/user_1.png",
  "streak_count": 7,
  "escola_id": 1,
  "serie_id": 3
}
```

---

### 2. Estatísticas do Dashboard

#### GET `/api/mobile/v1/stats`

Retorna estatísticas agregadas para o dashboard mobile.

**Response:**
```json
{
  "total_xp": 1500,
  "nivel": 15,
  "moedas": 250,
  "missoes_concluidas": 42,
  "streak_count": 7,
  "ranking_posicao": 3,
  "clan_nome": "Os Guerreiros"
}
```

---

### 3. Listar Missões

#### GET `/api/mobile/v1/missions`

Retorna lista de missões disponíveis.

**Query Parameters:**
- `limit` (opcional): Número máximo de missões (padrão: 20)

**Response:**
```json
[
  {
    "id": 1,
    "titulo": "Resolver 10 exercícios de matemática",
    "descricao": "Complete os exercícios do capítulo 5",
    "pontos": 100,
    "moedas": 50,
    "categoria": "tarefa",
    "data_limite": "2025-12-01T23:59:59",
    "status": "disponivel"
  },
  {
    "id": 2,
    "titulo": "Participar da aula",
    "descricao": "Estar presente e participativo",
    "pontos": 50,
    "moedas": 25,
    "categoria": "comportamento",
    "data_limite": null,
    "status": "pendente"
  }
]
```

**Status possíveis:**
- `disponivel`: Missão disponível para aceitar
- `pendente`: Missão enviada para validação
- `aprovada`: Missão aprovada e XP creditado

---

### 4. Completar Missão

#### POST `/api/mobile/v1/missions/{mission_id}/complete`

Marca uma missão como concluída e envia para validação.

**Response:**
```json
{
  "success": true,
  "message": "Missão enviada para validação!",
  "xp_pendente": 100,
  "moedas_pendentes": 50
}
```

**Erros:**
- `404`: Missão não encontrada
- `400`: Missão já enviada para validação

---

### 5. Ranking

#### GET `/api/mobile/v1/ranking`

Retorna o ranking da escola do usuário.

**Query Parameters:**
- `limit` (opcional): Número de usuários no top (padrão: 10)

**Response:**
```json
{
  "ranking": [
    {
      "posicao": 1,
      "nome": "Maria Santos",
      "xp": 2500,
      "nivel": 25,
      "avatar_url": "/media/avatars/user_5.png",
      "is_current_user": false
    },
    {
      "posicao": 2,
      "nome": "Pedro Costa",
      "xp": 2100,
      "nivel": 21,
      "avatar_url": null,
      "is_current_user": false
    },
    {
      "posicao": 3,
      "nome": "João Silva",
      "xp": 1500,
      "nivel": 15,
      "avatar_url": "/media/avatars/user_1.png",
      "is_current_user": true
    }
  ],
  "user_position": 3,
  "total_users": 45
}
```

---

### 6. Registrar Token de Dispositivo

#### POST `/api/mobile/v1/device-token`

Registra o token do dispositivo para receber push notifications.

**Request Body:**
```json
{
  "device_token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
  "platform": "ios"
}
```

**Platforms:** `ios`, `android`

**Response:**
```json
{
  "success": true,
  "message": "Token registrado com sucesso"
}
```

---

### 7. Remover Token de Dispositivo

#### DELETE `/api/mobile/v1/device-token`

Remove o token do dispositivo (logout ou desinstalação).

**Query Parameters:**
- `device_token`: Token a ser removido

**Response:**
```json
{
  "success": true,
  "message": "Token removido"
}
```

---

### 8. Health Check

#### GET `/api/mobile/v1/health`

Verifica o status da API mobile.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-23T22:30:00.000000"
}
```

---

## Códigos de Status HTTP

- `200 OK`: Requisição bem-sucedida
- `201 Created`: Recurso criado com sucesso
- `400 Bad Request`: Dados inválidos
- `401 Unauthorized`: Token inválido ou ausente
- `403 Forbidden`: Sem permissão
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro no servidor

---

## Versionamento

A API usa versionamento na URL (`/v1/`). Versões futuras serão:
- `/api/mobile/v2/` - Próxima versão
- `/api/mobile/v3/` - Versão seguinte

Versões antigas serão mantidas por pelo menos 6 meses após lançamento de nova versão.

---

## Rate Limiting

- **Limite:** 100 requisições por minuto por usuário
- **Headers de resposta:**
  - `X-RateLimit-Limit`: Limite total
  - `X-RateLimit-Remaining`: Requisições restantes
  - `X-RateLimit-Reset`: Timestamp do reset

---

## Push Notifications

### Tipos de Notificações

1. **mission_assigned**: Nova missão atribuída
2. **mission_validated**: Missão aprovada
3. **mission_rejected**: Missão rejeitada
4. **clan_message**: Nova mensagem no clã
5. **new_achievement**: Conquista desbloqueada
6. **system_announcement**: Anúncio do sistema

### Payload de Notificação

```json
{
  "title": "Nova Missão Atribuída",
  "body": "Você recebeu a missão: Resolver exercícios",
  "data": {
    "type": "mission_assigned",
    "mission_id": 123,
    "points": 100
  }
}
```

---

## Exemplo de Integração (React Native)

```javascript
import axios from 'axios';
import * as Notifications from 'expo-notifications';

const API_BASE = 'https://api.schoolquest.com/api/mobile/v1';

// Configurar cliente
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Adicionar token JWT
api.interceptors.request.use(config => {
  const token = await AsyncStorage.getItem('jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Buscar perfil
const getProfile = async () => {
  const response = await api.get('/me');
  return response.data;
};

// Buscar missões
const getMissions = async () => {
  const response = await api.get('/missions?limit=20');
  return response.data;
};

// Completar missão
const completeMission = async (missionId) => {
  const response = await api.post(`/missions/${missionId}/complete`);
  return response.data;
};

// Registrar token de push
const registerPushToken = async () => {
  const token = await Notifications.getExpoPushTokenAsync();
  await api.post('/device-token', {
    device_token: token.data,
    platform: Platform.OS
  });
};
```

---

## Suporte

Para dúvidas ou problemas:
- **Email:** suporte@schoolquest.com
- **Documentação completa:** https://docs.schoolquest.com
- **Status da API:** https://status.schoolquest.com
