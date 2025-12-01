# 🎮 SchoolQuest - Sistema de Gamificação Escolar

Sistema completo de gamificação para escolas, transformando o aprendizado em uma experiência interativa e engajadora.

## 🚀 Funcionalidades

### 👥 Gestão de Usuários
- **4 tipos de usuários**: Admin, Gestor, Professor, Aluno
- Autenticação JWT com sessão persistente (30 dias)
- QR Code único para cada usuário
- Importação em massa via CSV

### 🎯 Sistema de Missões
- Criação de missões por professores
- Validação presencial via QR Code
- Missões individuais e de clã
- Sistema de XP, níveis e moedas
- Notificações em tempo real via WebSocket

### 🏆 Gamificação
- Sistema de níveis baseado em XP
- Loja virtual com itens
- Clãs e missões em grupo
- Ranking de alunos
- Conquistas e badges

### 📊 Analytics
- Dashboard com gráficos interativos
- Relatórios de participação
- Top escolas e professores
- Estatísticas por série

### 💬 Comunicação
- Mural de posts com curtidas
- Chat em tempo real
- Notificações push via WebSocket
- Sistema de convites para clãs

## 🛠️ Tecnologias

### Backend
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **SQLite** - Banco de dados
- **JWT** - Autenticação
- **WebSocket** - Comunicação em tempo real
- **Pydantic** - Validação de dados

### Frontend
- **React** + **TypeScript** - Interface moderna
- **Vite** - Build tool
- **TailwindCSS** - Estilização
- **Axios** - Cliente HTTP
- **Recharts** - Gráficos interativos
- **Lucide React** - Ícones

## 📦 Instalação

### Pré-requisitos
- Python 3.8+
- Node.js 16+
- Git

### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual (Windows)
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Iniciar servidor
python -m uvicorn app.main:app --reload
```

O backend estará rodando em `http://localhost:8000`

### Frontend

```bash
cd frontend

# Instalar dependências
npm install

# Iniciar servidor de desenvolvimento
npm run dev
```

O frontend estará rodando em `http://localhost:5173`

## 🔄 Resetar Banco de Dados

Para resetar o banco de dados e criar dados iniciais:

```bash
cd backend
python reset_database.py
```

Digite `SIM` quando solicitado.

## 👤 Credenciais Padrão

Após resetar o banco de dados:

| Tipo | Email | Senha |
|------|-------|-------|
| Admin | admin@test.com | admin123 |
| Gestor | gestor@test.com | gestor123 |
| Professor | professor@test.com | prof123 |
| Aluno 1 | aluno1@test.com | aluno123 |
| Aluno 2 | aluno2@test.com | aluno123 |

## 📁 Estrutura do Projeto

```
SchoolQuest/
├── backend/
│   ├── app/
│   │   ├── routers/        # Endpoints da API
│   │   ├── models.py       # Modelos do banco
│   │   ├── schemas.py      # Schemas Pydantic
│   │   ├── auth.py         # Autenticação JWT
│   │   ├── database.py     # Configuração do BD
│   │   ├── websocket.py    # WebSocket manager
│   │   └── main.py         # App principal
│   ├── reset_database.py   # Script de reset
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/          # Páginas React
    │   ├── components/     # Componentes
    │   ├── context/        # Context API
    │   ├── api/            # Cliente API
    │   └── hooks/          # Custom hooks
    └── package.json
```

## 🔧 Configuração

### Backend (.env)
```env
DATABASE_URL=sqlite:///./schoolquest.db
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:5173
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

## 📝 API Endpoints

### Autenticação
- `POST /auth/token` - Login

### Usuários
- `GET /users/me` - Dados do usuário atual
- `POST /users/import` - Importar usuários via CSV
- `POST /users/fix-qr-tokens` - Gerar QR tokens

### Missões
- `GET /missoes/` - Listar missões
- `POST /missoes/` - Criar missão
- `POST /missoes/{id}/completar` - Completar missão
- `POST /missoes/{id}/validar` - Validar missão

### Clãs
- `GET /clans/` - Listar clãs
- `POST /clans/` - Criar clã
- `POST /clans/{id}/invite` - Convidar membro

### Relatórios
- `GET /reports/stats` - Estatísticas gerais
- `GET /reports/top_schools` - Top escolas
- `GET /reports/top_professors` - Top professores

## 🎨 Funcionalidades Especiais

### Notificações em Tempo Real
- Alunos recebem notificação instantânea quando uma nova missão é criada
- Sistema de WebSocket para comunicação bidirecional
- Notificações do navegador (se permitido)

### Sistema de QR Code
- Cada usuário tem um QR code único
- Professores podem validar missões escaneando o QR do aluno
- Validação presencial rápida e segura

### Importação CSV
- Importação em massa de escolas, gestores e usuários
- Templates disponíveis para download
- Validação automática de dados

## 🐛 Troubleshooting

### WebSocket não conecta
```bash
# Instalar dependências WebSocket
pip install "uvicorn[standard]"
```

### Erro de CORS
Verifique se o `CORS_ORIGINS` no backend inclui a URL do frontend.

### Banco de dados corrompido
```bash
cd backend
python reset_database.py
```

## 📄 Licença

Este projeto é de código aberto.

## 👨‍💻 Desenvolvido por

REGINALDO LOPES

---

**Versão**: 1.0.0  
**Última atualização**: Novembro 2024