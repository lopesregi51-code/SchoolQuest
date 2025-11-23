# Configuração de Ambiente - SchoolQuest

## Para Desenvolvimento Local

Crie um arquivo `.env` na pasta `frontend` com o seguinte conteúdo:

```
VITE_API_URL=http://127.0.0.1:8000
```

## Para Deploy na Vercel

Configure a variável de ambiente no painel da Vercel:

1. Acesse [Vercel Dashboard](https://vercel.com/dashboard)
2. Selecione o projeto `school-quest`
3. Vá em **Settings** → **Environment Variables**
4. Adicione:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://schoolquest-api.onrender.com`
   - **Environments**: Production, Preview, Development (marque todos)
5. Clique em **Save**
6. Faça **Redeploy** do último deployment

## Observação Importante

O arquivo `.env` está no `.gitignore` e **não deve** ser commitado no Git por questões de segurança.
