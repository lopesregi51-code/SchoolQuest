"""
Análise completa da estrutura do banco de dados
"""
import sqlite3
import os

db_path = 'schoolquest.db'

if not os.path.exists(db_path):
    print(f"ERRO: Banco de dados nao encontrado em {os.path.abspath(db_path)}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

with open('db_analysis_report.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("ANALISE DO BANCO DE DADOS - SchoolQuest\n")
    f.write("="*80 + "\n")
    f.write(f"\nLocalizacao: {os.path.abspath(db_path)}\n")
    f.write(f"Tamanho: {os.path.getsize(db_path) / 1024:.2f} KB\n\n")

    # 1. Listar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    f.write(f"TABELAS ENCONTRADAS ({len(tables)}):\n")
    f.write("-"*80 + "\n")
    for table in tables:
        f.write(f"  * {table[0]}\n")

    # 2. Para cada tabela, mostrar estrutura e contagem
    f.write("\n" + "="*80 + "\n")
    f.write("ESTRUTURA E DADOS DAS TABELAS\n")
    f.write("="*80 + "\n")

    for table in tables:
        table_name = table[0]
        f.write(f"\n[Tabela: {table_name}]\n")
        f.write("-"*80 + "\n")
        
        # Estrutura
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        f.write("Colunas:\n")
        for col in columns:
            col_id, name, type_, notnull, default, pk = col
            pk_str = " [PK]" if pk else ""
            notnull_str = " NOT NULL" if notnull else ""
            f.write(f"  - {name}: {type_}{pk_str}{notnull_str}\n")
        
        # Contagem de registros
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        f.write(f"Registros: {count}\n")
        
        # Se tiver poucos registros, mostrar alguns exemplos
        if count > 0 and count <= 5:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
            rows = cursor.fetchall()
            f.write("Exemplos:\n")
            for row in rows:
                f.write(f"  {row}\n")

    # 3. Verificar foreign keys
    f.write("\n" + "="*80 + "\n")
    f.write("FOREIGN KEYS (INTEGRIDADE REFERENCIAL)\n")
    f.write("="*80 + "\n")

    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA foreign_key_list({table_name});")
        fks = cursor.fetchall()
        if fks:
            f.write(f"\n{table_name}:\n")
            for fk in fks:
                id_, seq, table_ref, from_col, to_col, on_update, on_delete, match = fk
                f.write(f"  {from_col} -> {table_ref}.{to_col}\n")

    # 4. Diagnóstico de problemas potenciais
    f.write("\n" + "="*80 + "\n")
    f.write("DIAGNOSTICO\n")
    f.write("="*80 + "\n")

    issues = []

    # Verificar se tabelas críticas estão vazias
    critical_tables = ['escolas', 'users', 'missoes']
    for table_name in critical_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        if count == 0:
            issues.append(f"[!] Tabela '{table_name}' esta vazia")

    # Verificar se há usuários sem escola
    cursor.execute("SELECT COUNT(*) FROM users WHERE escola_id IS NULL;")
    orphan_users = cursor.fetchone()[0]
    if orphan_users > 0:
        issues.append(f"[!] {orphan_users} usuario(s) sem escola associada")

    # Verificar se há missões sem criador
    cursor.execute("SELECT COUNT(*) FROM missoes WHERE criador_id NOT IN (SELECT id FROM users);")
    orphan_missions = cursor.fetchone()[0]
    if orphan_missions > 0:
        issues.append(f"[!] {orphan_missions} missao(oes) com criador invalido")

    if issues:
        f.write("\nProblemas encontrados:\n")
        for issue in issues:
            f.write(f"  {issue}\n")
    else:
        f.write("\n[OK] Nenhum problema estrutural detectado\n")

    f.write("\n" + "="*80 + "\n")

conn.close()
print("Análise concluída. Veja o arquivo db_analysis_report.txt")
