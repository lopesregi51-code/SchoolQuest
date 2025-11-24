import sqlite3

conn = sqlite3.connect('schoolquest.db')
c = conn.cursor()

print('=== ESCOLAS ===')
c.execute('SELECT * FROM escolas')
escolas = c.fetchall()
for e in escolas:
    print(f'ID: {e[0]}, Nome: {e[1]}')

print('\n=== GESTORES ===')
c.execute('SELECT id, nome, email, papel, escola_id FROM users WHERE papel=?', ('gestor',))
gestores = c.fetchall()
for g in gestores:
    print(f'ID: {g[0]}, Nome: {g[1]}, Email: {g[2]}, Escola: {g[4]}')

print('\n=== ADMIN ===')
c.execute('SELECT id, nome, email, papel, escola_id FROM users WHERE papel=?', ('admin',))
admin = c.fetchone()
if admin:
    print(f'ID: {admin[0]}, Nome: {admin[1]}, Email: {admin[2]}, Escola: {admin[4]}')

print('\n=== TOTAIS ===')
c.execute('SELECT COUNT(*) FROM users')
print(f'Total usuários: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM escolas')
print(f'Total escolas: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM missoes')
print(f'Total missões: {c.fetchone()[0]}')

conn.close()
