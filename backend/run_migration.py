"""
Script para aplicar migração no banco de dados PostgreSQL da Render
Execute este script localmente após configurar a DATABASE_URL
"""

import os
import psycopg2
from psycopg2 import sql

# URL do banco de dados PostgreSQL na Render
DATABASE_URL = "postgresql://schoolquest:4b5oKuGzD93ViZBKnXOL10YLm3iua2sJ@dpg-d4ida18gjchc739vgn2g-a.oregon-postgres.render.com/schoolquest"

# Se preferir, cole a URL diretamente aqui (NÃO COMMITE ISSO NO GIT):
# DATABASE_URL = "sua-url-aqui"

def run_migration():
    print("🔄 Conectando ao banco de dados...")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        print("✅ Conectado com sucesso!")
        print("\n📝 Aplicando migrações...\n")
        
        # Migração 1: Adicionar qr_token aos usuários
        print("1️⃣ Adicionando coluna qr_token à tabela users...")
        cursor.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS qr_token VARCHAR;
        """)
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_users_qr_token ON users(qr_token);
        """)
        print("   ✅ qr_token adicionado")
        
        # Migração 2: Adicionar moedas aos clãs
        print("2️⃣ Adicionando coluna moedas à tabela clans...")
        cursor.execute("""
            ALTER TABLE clans ADD COLUMN IF NOT EXISTS moedas INTEGER DEFAULT 0;
        """)
        print("   ✅ moedas adicionado")
        
        # Migração 3: Adicionar tipo e clan_id às missões
        print("3️⃣ Adicionando colunas tipo e clan_id à tabela missoes...")
        cursor.execute("""
            ALTER TABLE missoes ADD COLUMN IF NOT EXISTS tipo VARCHAR DEFAULT 'individual';
        """)
        cursor.execute("""
            ALTER TABLE missoes ADD COLUMN IF NOT EXISTS clan_id INTEGER;
        """)
        
        # Adicionar foreign key se não existir
        try:
            cursor.execute("""
                ALTER TABLE missoes 
                ADD CONSTRAINT fk_missoes_clan_id 
                FOREIGN KEY (clan_id) REFERENCES clans(id);
            """)
        except psycopg2.errors.DuplicateObject:
            print("   ⚠️  Foreign key já existe (ok)")
        
        print("   ✅ tipo e clan_id adicionados")
        
        # Opcional: Gerar QR tokens para usuários existentes
        print("\n4️⃣ Gerando QR tokens para usuários existentes...")
        cursor.execute("""
            UPDATE users 
            SET qr_token = gen_random_uuid()::text 
            WHERE qr_token IS NULL;
        """)
        rows_updated = cursor.rowcount
        print(f"   ✅ {rows_updated} usuários atualizados com QR tokens")
        
        # Commit das mudanças
        conn.commit()
        
        print("\n🎉 Migração concluída com sucesso!")
        print("✅ Todas as colunas foram adicionadas ao banco de dados")
        
    except psycopg2.Error as e:
        print(f"\n❌ Erro ao executar migração: {e}")
        print("\nVerifique:")
        print("- A DATABASE_URL está correta?")
        print("- Você tem permissão para alterar o banco?")
        print("- O banco de dados está acessível?")
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("\n🔌 Conexão fechada")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 MIGRAÇÃO DO BANCO DE DADOS - SchoolQuest")
    print("=" * 60)
    print()
    
    if "postgresql://" not in DATABASE_URL:
        print("⚠️  ATENÇÃO: Configure a DATABASE_URL antes de executar!")
        print()
        print("Como obter a URL:")
        print("1. Acesse https://dashboard.render.com")
        print("2. Vá até seu banco PostgreSQL")
        print("3. Clique em 'Connect' → 'External Connection'")
        print("4. Copie a URL e cole neste script")
        print()
        print("Ou defina como variável de ambiente:")
        print("export DATABASE_URL='sua-url-aqui'")
        print()
    else:
        confirm = input("⚠️  Tem certeza que deseja executar a migração? (sim/não): ")
        if confirm.lower() in ['sim', 's', 'yes', 'y']:
            run_migration()
        else:
            print("❌ Migração cancelada")
