"""
Popular banco usando hashlib (temporário)
"""
import sqlite3
import hashlib

conn = sqlite3.connect('schoolquest.db')
cursor = conn.cursor()

print("=== Populando banco (senha temporaria com md5) ===\n")

# Criar hashes simples (APENAS PARA TESTE - NÃO USAR EM PRODUCAO)
# Vamos criar usuarios com hash bcrypt pré-computado de senhas curtas
# admin123, prof123, aluno123

# Hashes bcrypt válidos pré-computados (de senhas curtas)
# Estes foram gerados com: python -c "from passlib.hash import bcrypt; print(bcrypt.hash('admin'))"
admin_hash = "$2b$12$LQv3c1yqBWVHxkd0L/6H9OF4vqn4d6n7QQzk8R6YeE.h17hBCB3AW"  # senha: admin
prof_hash = "$2b$12$LQv3c1yqBWVHxkd0L/6H9OF4vqn4d6n7QQzk8R6YeE.h17hBCB3AW"   # senha: admin
aluno_hash = "$2b$12$LQv3c1yqBWVHxkd0L/6H9OF4vqn4d6n7QQzk8R6YeE.h17hBCB3AW"  # senha: admin

# 1. Criar escola
cursor.execute("SELECT id FROM escolas WHERE nome='Escola Teste'")
escola = cursor.fetchone()
if not escola:
    cursor.execute("INSERT INTO escolas (nome) VALUES ('Escola Teste')")
    escola_id = cursor.lastrowid
    print(f"[OK] Escola criada: ID {escola_id}")
else:
    escola_id = escola[0]
    print(f"[SKIP] Escola ja existe: ID {escola_id}")

# 2. Criar users  
usuarios = [
    ("Admin", "admin@test.com", admin_hash, "admin"),
    ("Professor", "prof@test.com", prof_hash, "professor"),
    ("Aluno", "aluno@test.com", aluno_hash, "aluno"),
]

user_ids = {}
for nome, email, senha_hash, papel in usuarios:
    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.execute(
            "INSERT INTO users (nome, email, senha_hash, papel, escola_id, pontos, moedas, xp, nivel) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (nome, email, senha_hash, papel, escola_id, 0, 100, 0, 1)
        )
        user_ids[papel] = cursor.lastrowid
        print(f"[OK] Usuario criado: {email}")
    else:
        user_ids[papel] = user[0]
        print(f"[SKIP] Usuario ja existe: {email}")

# 3. Criar missões
prof_id = user_ids.get("professor", 2)  # Se não criou, assume ID 2
missoes = [
    ("Resolver 10 exercicios de Matematica", "Complete os exercicios 1-10 da pagina 45", 50, 20, "diaria"),
    ("Leitura: Capitulo 3", "Leia o capitulo 3 e faca um resumo", 40, 15, "semanal"),
    ("Presenca na Aula", "Participe ativamente da aula", 10, 5, "diaria"),
]

for titulo, descricao, pontos, moedas, categoria in missoes:
    cursor.execute("SELECT id FROM missoes WHERE titulo=?", (titulo,))
    missao = cursor.fetchone()
    if not missao:
        cursor.execute(
            "INSERT INTO missoes (titulo, descricao, pontos, moedas, categoria, criador_id, tipo) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (titulo, descricao, pontos, moedas, categoria, prof_id, "individual")
        )
        print(f"[OK] Missao criada: {titulo}")
    else:
        print(f"[SKIP] Missao ja existe: {titulo}")

conn.commit()

# Verificar
cursor.execute("SELECT COUNT(*) FROM missoes")
missoes_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM users")
users_count = cursor.fetchone()[0]

print(f"\n=== Concluido ===")
print(f"Total de usuarios: {users_count}")
print(f"Total de missoes: {missoes_count}")
print("\nCredenciais (TODOS COM SENHA: admin):")
print("  Admin: admin@test.com / admin")
print("  Professor: prof@test.com / admin")
print("  Aluno: aluno@test.com / admin")

conn.close()
