# SchoolQuest - Sistema de Gerenciamento Escolar Gamificado

## 🎮 Como Usar

### Iniciando a Aplicação

1. **Backend** (Terminal 1):
   ```powershell
   cd C:\projetos\SchoolQuest\backend
   py -m uvicorn app.main:app --reload
   ```

2. **Frontend** (Terminal 2):
   ```powershell
   cd C:\projetos\SchoolQuest\frontend
   npm run dev
   ```

3. **Acessar**: http://localhost:5173

### 👤 Credenciais de Teste

**Admin:**
- Email: `admin@test.com`
- Senha: `admin123`

### ✨ Funcionalidades Recém-Implementadas

#### Gerenciamento de Séries (Novo!)
- **Localização**: Painel do Gestor → Botão "Gerenciar Séries"
- **Funcionalidades**:
  - ✅ Criar novas séries (ex: "5º Ano A", "6º Ano B")
  - ✅ Editar nomes de séries existentes
  - ✅ Excluir séries (com validação para evitar exclusão de séries com alunos)
  - ✅ Visualizar todas as séries da escola

#### Outras Funcionalidades
- **Mural**: Sistema de posts com imagens e curtidas
- **Loja**: Sistema de recompensas com moedas
- **Missões**: Criação e validação de missões
- **Relatórios**: Top professores e estatísticas de participação
- **Admin**: Gerenciamento de escolas (criar/excluir)

### 🔧 Solução de Problemas

**Erro de Conexão com Backend:**
1. Certifique-se de que o backend está rodando (veja logs no terminal)
2. Verifique se a porta 8000 está livre
3. Se necessário, delete `schoolquest.db` e reinicie o backend

**Banco de Dados Vazio:**
- Execute: `py test_create_user_direct.py` para criar um usuário admin
- Ou use o script: `py setup_test_data.py` (se disponível)

### 📝 Notas Técnicas

- **Banco de Dados**: SQLite (`schoolquest.db`)
- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Vite
- **Autenticação**: JWT tokens
