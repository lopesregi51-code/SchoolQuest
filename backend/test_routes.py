"""
Script para testar todas as rotas usadas pelas paginas Professor e Aluno
"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("="*80)
print("TESTE DE ROTAS - Professor e Aluno")
print("="*80)

# Login como professor
print("\n[1] Login como Professor...")
login_data = {"username": "prof@test.com", "password": "admin"}
response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
if response.status_code == 200:
    prof_token = response.json()["access_token"]
    prof_headers = {"Authorization": f"Bearer {prof_token}"}
    print("[OK] Login Professor OK")
else:
    print(f"[ERRO] Login Professor FALHOU: {response.status_code}")
    exit(1)

# Login como aluno
print("\n[2] Login como Aluno...")
login_data = {"username": "aluno@test.com", "password": "admin"}
response = requests.post(f"{BASE_URL}/auth/token", data=login_data)
if response.status_code == 200:
    aluno_token = response.json()["access_token"]
    aluno_headers = {"Authorization": f"Bearer {aluno_token}"}
    print("[OK] Login Aluno OK")
else:
    print(f"[ERRO] Login Aluno FALHOU: {response.status_code}")
    exit(1)

print("\n" + "="*80)
print("ROTAS DO PROFESSOR")
print("="*80)

# Rotas do Professor
rotas_professor = [
    ("GET", "/clans/", "Buscar clans"),
    ("GET", "/missoes/pendentes", "Missoes pendentes"),
    ("GET", "/missoes/professor/concluidas", "Missoes concluidas"),
    ("GET", "/missoes/", "Listar missoes"),
]

resultados = {"ok": 0, "erro": 0}

for method, rota, descricao in rotas_professor:
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{rota}", headers=prof_headers)
        print(f"\n[{method}] {rota} - {descricao}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"[OK] Retornou {len(data)} itens")
                resultados["ok"] += 1
            else:
                print(f"[OK] Retornou dados")
                resultados["ok"] += 1
        else:
            print(f"[ERRO] {response.text[:200]}")
            resultados["erro"] += 1
    except Exception as e:
        print(f"[EXCECAO] {e}")
        resultados["erro"] += 1

print("\n" + "="*80)
print("ROTAS DO ALUNO")
print("="*80)

# Rotas do Aluno
rotas_aluno = [
    ("GET", "/missoes/", "Listar missoes disponiveis"),
    ("GET", "/missoes/recebidas", "Missoes recebidas"),
]

for method, rota, descricao in rotas_aluno:
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{rota}", headers=aluno_headers)
        print(f"\n[{method}] {rota} - {descricao}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"[OK] Retornou {len(data)} itens")
                if len(data) > 0:
                    print(f"Exemplo: {data[0].get('titulo', 'N/A')}")
                resultados["ok"] += 1
            else:
                print(f"[OK] Retornou dados")
                resultados["ok"] += 1
        else:
            print(f"[ERRO] {response.text[:200]}")
            resultados["erro"] += 1
    except Exception as e:
        print(f"[EXCECAO] {e}")
        resultados["erro"] += 1

print("\n" + "="*80)
print("RESUMO")
print("="*80)
print(f"\nRotas OK: {resultados['ok']}")
print(f"Rotas com ERRO: {resultados['erro']}")
print(f"Total testado: {resultados['ok'] + resultados['erro']}")
