-- Migration script to add new columns for Mission Types and QR Code features
-- Run this on your Render PostgreSQL database

-- Add qr_token to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS qr_token VARCHAR;
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_qr_token ON users(qr_token);

-- Add moedas to clans table
ALTER TABLE clans ADD COLUMN IF NOT EXISTS moedas INTEGER DEFAULT 0;

-- Add tipo and clan_id to missoes table
ALTER TABLE missoes ADD COLUMN IF NOT EXISTS tipo VARCHAR DEFAULT 'individual';
ALTER TABLE missoes ADD COLUMN IF NOT EXISTS clan_id INTEGER;
ALTER TABLE missoes ADD CONSTRAINT IF NOT EXISTS fk_missoes_clan_id FOREIGN KEY (clan_id) REFERENCES clans(id);

-- Optional: Generate QR tokens for existing users (run this after the above)
-- UPDATE users SET qr_token = gen_random_uuid()::text WHERE qr_token IS NULL;
