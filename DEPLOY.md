# 🚀 Guia de Deploy - Vercel + Render com PostgreSQL

## 📋 Pré-requisitos

- Conta no [Vercel](https://vercel.com)
- Conta no [Render](https://render.com)
- Repositório no GitHub com o código

---

## 🗄️ Parte 1: Configurar PostgreSQL no Render

### 1.1 Criar Banco de Dados PostgreSQL

1. Acesse https://dashboard.render.com
2. Clique em **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `schoolquest-db`
   - **Database**: `schoolquest`
   - **User**: `schoolquest_user` (gerado automaticamente)
   - **Region**: Escolha a mais próxima
   - **Plan**: **Free** (0$/mês)
4. Clique em **"Create Database"**
5. **IMPORTANTE**: Copie e salve:
   - **Internal Database URL** (para o backend)
   - **External Database URL** (para acesso externo, se necessário)

### 1.2 Instalar Dependências PostgreSQL

Adicione ao `backend/requirements.txt`:

```txt
psycopg2-binary==2.9.9
```

---

## 🔧 Parte 2: Adaptar o Código para PostgreSQL

### 2.1 Atualizar `backend/app/config.py`

```python
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-CHANGE-IN-PRODUCTION")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 days
    
    # Database - Suporta SQLite (dev) e PostgreSQL (prod)
    database_url: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./schoolquest.db"
    )
    
    # CORS
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    )
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def database_url_fixed(self) -> str:
        """Fix Render's postgres:// to postgresql://"""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

settings = Settings()
```

### 2.2 Atualizar `backend/app/database.py`

```python
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Use the fixed database URL
SQLALCHEMY_DATABASE_URL = settings.database_url_fixed

# Create engine with appropriate settings
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite specific settings
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    # Configure SQLite for better reliability
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()
        logger.info("SQLite pragmas configured for better reliability")
else:
    # PostgreSQL settings
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    logger.info("PostgreSQL engine created")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 🚀 Parte 3: Deploy no Render (Backend)

### 3.1 Criar Web Service

1. No Render Dashboard, clique em **"New +"** → **"Web Service"**
2. Conecte seu repositório GitHub
3. Configure:
   - **Name**: `schoolquest-api`
   - **Region**: Mesma do banco de dados
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: **Free**

### 3.2 Configurar Variáveis de Ambiente

Na aba **"Environment"**, adicione:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | Cole a **Internal Database URL** do PostgreSQL |
| `SECRET_KEY` | Gere uma chave: `openssl rand -hex 32` |
| `CORS_ORIGINS` | `https://seu-app.vercel.app` (adicione depois) |
| `ENVIRONMENT` | `production` |

### 3.3 Deploy

1. Clique em **"Create Web Service"**
2. Aguarde o build (5-10 minutos)
3. Copie a URL do backend (ex: `https://schoolquest-api.onrender.com`)

---

## 🌐 Parte 4: Deploy no Vercel (Frontend)

### 4.1 Preparar Frontend

Crie `frontend/.env.production`:

```env
VITE_API_URL=https://schoolquest-api.onrender.com
```

### 4.2 Deploy no Vercel

1. Acesse https://vercel.com/new
2. Importe seu repositório do GitHub
3. Configure:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Em **Environment Variables**, adicione:
   - `VITE_API_URL` = `https://schoolquest-api.onrender.com`
5. Clique em **"Deploy"**
6. Aguarde o deploy (2-3 minutos)
7. Copie a URL do frontend (ex: `https://schoolquest.vercel.app`)

### 4.3 Atualizar CORS no Backend

1. Volte ao Render
2. Vá em **Environment** do backend
3. Atualize `CORS_ORIGINS`:
   ```
   https://schoolquest.vercel.app,https://seu-dominio-custom.com
   ```
4. Clique em **"Save Changes"**
5. O Render fará redeploy automático

---

## ✅ Parte 5: Verificação

### 5.1 Testar Backend

```bash
curl https://schoolquest-api.onrender.com/
```

Deve retornar:
```json
{
  "message": "SchoolQuest API",
  "version": "1.0.0",
  "environment": "production"
}
```

### 5.2 Testar Frontend

1. Acesse `https://schoolquest.vercel.app`
2. Faça login com:
   - Email: `admin@test.com`
   - Senha: `admin123`

---

## 🔄 Parte 6: Deploys Futuros

### Automático via Git

Sempre que você fizer `git push`:

1. **Vercel**: Deploy automático do frontend ✅
2. **Render**: Deploy automático do backend ✅

### Manual (se necessário)

**Render**:
- Dashboard → Seu serviço → **"Manual Deploy"** → **"Deploy latest commit"**

**Vercel**:
- Dashboard → Seu projeto → **"Deployments"** → **"Redeploy"**

---

## 🗄️ Parte 7: Gerenciar Banco de Dados

### 7.1 Acessar PostgreSQL

**Via Render Dashboard**:
1. PostgreSQL → `schoolquest-db` → **"Connect"**
2. Use **psql** ou cliente SQL favorito

**Via Linha de Comando**:
```bash
psql <EXTERNAL_DATABASE_URL>
```

### 7.2 Resetar Banco (Produção)

⚠️ **CUIDADO**: Isso apaga todos os dados!

```bash
# Conectar ao banco
psql <EXTERNAL_DATABASE_URL>

# Deletar todas as tabelas
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

# Sair
\q
```

Depois, faça redeploy no Render para recriar as tabelas.

### 7.3 Backup Manual

```bash
# Fazer backup
pg_dump <EXTERNAL_DATABASE_URL> > backup.sql

# Restaurar backup
psql <EXTERNAL_DATABASE_URL> < backup.sql
```

---

## 📊 Limites do Plano Free

### Render (Backend)
- ✅ 750 horas/mês grátis
- ⚠️ Servidor "hiberna" após 15 min de inatividade
- ⚠️ Primeiro acesso pode demorar ~30s (cold start)
- ✅ Deploy automático via Git

### Render (PostgreSQL)
- ✅ 1 GB de armazenamento
- ✅ Backup automático por 7 dias
- ⚠️ Expira após 90 dias de inatividade
- ✅ Conexões ilimitadas

### Vercel (Frontend)
- ✅ 100 GB de bandwidth/mês
- ✅ Deploy ilimitado
- ✅ SSL automático
- ✅ CDN global

---

## 🔧 Troubleshooting

### Erro: "Application failed to respond"
- Verifique se `PORT` está sendo usado: `--port $PORT`
- Verifique logs no Render Dashboard

### Erro: CORS
- Adicione a URL do Vercel em `CORS_ORIGINS`
- Formato: `https://seu-app.vercel.app` (sem barra no final)

### Erro: Database connection
- Verifique se `DATABASE_URL` está correto
- Use **Internal Database URL** (não External)
- Certifique-se que `postgres://` foi convertido para `postgresql://`

### Cold Start lento
- Normal no plano Free
- Considere upgrade para manter servidor ativo 24/7

---

## 🎯 Próximos Passos

1. ✅ Configurar domínio customizado no Vercel
2. ✅ Configurar monitoramento (Render tem logs)
3. ✅ Configurar backups automáticos do PostgreSQL
4. ✅ Adicionar analytics (Google Analytics, etc.)

---

**Pronto!** 🎉 Seu SchoolQuest está no ar com banco de dados persistente!
