"""
Script simplificado para aplicar migração usando urllib (sem dependências externas)
"""

import urllib.request
import urllib.parse
import json

# URL do banco de dados
DB_URL = "postgresql://schoolquest:4b5oKuGzD93ViZBKnXOL10YLm3iua2sJ@dpg-d4ida18gjchc739vgn2g-a.oregon-postgres.render.com/schoolquest"

# Comandos SQL para executar
SQL_COMMANDS = """
-- Adicionar qr_token aos usuários
ALTER TABLE users ADD COLUMN IF NOT EXISTS qr_token VARCHAR;
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_qr_token ON users(qr_token);

-- Adicionar moedas aos clãs
ALTER TABLE clans ADD COLUMN IF NOT EXISTS moedas INTEGER DEFAULT 0;

-- Adicionar tipo e clan_id às missões
ALTER TABLE missoes ADD COLUMN IF NOT EXISTS tipo VARCHAR DEFAULT 'individual';
ALTER TABLE missoes ADD COLUMN IF NOT EXISTS clan_id INTEGER;

-- Gerar QR tokens para usuários existentes
UPDATE users SET qr_token = gen_random_uuid()::text WHERE qr_token IS NULL;
"""

print("=" * 60)
print("⚠️  INSTRUÇÕES PARA EXECUTAR A MIGRAÇÃO")
print("=" * 60)
print()
print("Como o ambiente Python local tem problemas de dependências,")
print("você tem 2 opções para executar a migração:")
print()
print("OPÇÃO 1 - Usar o Console da Render (RECOMENDADO):")
print("-" * 60)
print("1. Acesse: https://dashboard.render.com")
print("2. Vá até seu banco PostgreSQL")
print("3. Procure por 'Shell', 'Console' ou 'Query'")
print("4. Cole e execute os comandos SQL abaixo:")
print()
print(SQL_COMMANDS)
print()
print("OPÇÃO 2 - Instalar psycopg2 manualmente:")
print("-" * 60)
print("Execute no terminal:")
print("cd backend")
print("python -m pip install --upgrade pip")
print("python -m pip install psycopg2-binary")
print("python run_migration.py")
print()
print("=" * 60)

# Salvar SQL em arquivo para facilitar
with open("migration_commands.sql", "w", encoding="utf-8") as f:
    f.write(SQL_COMMANDS)

print("✅ Comandos SQL salvos em: migration_commands.sql")
print()
print("Você pode copiar o conteúdo deste arquivo e colar no console da Render!")
