
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
