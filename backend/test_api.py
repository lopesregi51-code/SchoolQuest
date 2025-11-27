"""
Script para testar a API e verificar por que as missões não aparecem
"""
import requests

BASE_URL = "http://localhost:8000"

print("="*80)
print("TESTE DA API - SchoolQuest")
print("="*80)

# 1. Testar login
print("\n1. Testando login do aluno...")
login_data = {
    "username": "aluno@test.com",
    "password": "admin"
}

try:
    response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        token_data = response.json()
        token = token_data["access_token"]
        print(f"[OK] Login bem-sucedido!")
        print(f"Token: {token[:50]}...")
        headers = {"Authorization": f"Bearer {token}"}
    else:
        print(f"[ERRO] Login falhou: {response.text}")
        exit(1)
except Exception as e:
    print(f"[ERRO] Exceção: {e}")
    exit(1)

# 2. Testar endpoint de missões
print("\n2. Testando endpoint /missoes/...")
try:
    response = requests.get(f"{BASE_URL}/missoes/", headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        missoes = response.json()
        print(f"[OK] API retornou {len(missoes)} missões")
        if missoes:
            print("\nMissões retornadas:")
            for i, missao in enumerate(missoes, 1):
                print(f"\n  {i}. {missao.get('titulo', 'SEM TITULO')}")
                print(f"     Pontos: {missao.get('pontos', 0)}")
                print(f"     Status: {missao.get('status', 'N/A')}")
                print(f"     Tipo: {missao.get('tipo', 'N/A')}")
        else:
            print("[AVISO] Lista de missões vazia!")
    else:
        print(f"[ERRO] API retornou erro: {response.text}")
except Exception as e:
    print(f"[ERRO] Exceção: {e}")

# 3. Testar diretamente o banco
print("\n3. Verificando banco de dados...")
import sqlite3
conn = sqlite3.connect('c:/projetos/SchoolQuest/backend/schoolquest.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM missoes")
count = cursor.fetchone()[0]
print(f"Total de missões no banco: {count}")

if count > 0:
    cursor.execute("SELECT id, titulo, criador_id, tipo FROM missoes LIMIT 5")
    missoes_db = cursor.fetchall()
    print("\nMissões no banco:")
    for missao in missoes_db:
        print(f"  - ID: {missao[0]}, Título: {missao[1]}, Criador: {missao[2]}, Tipo: {missao[3]}")

# 4. Verificar usuários
cursor.execute("SELECT id, email, papel, escola_id FROM users")
users = cursor.fetchall()
print(f"\nTotal de usuários: {len(users)}")
for user in users:
    print(f"  - ID: {user[0]}, Email: {user[1]}, Papel: {user[2]}, Escola: {user[3]}")

conn.close()

print("\n" + "="*80)
