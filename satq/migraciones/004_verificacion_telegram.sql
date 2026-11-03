-- Campos para suscripciones originadas en Telegram y verificación por SMS.
ALTER TABLE suscriptores ADD COLUMN IF NOT EXISTS origen TEXT NOT NULL DEFAULT 'web';
ALTER TABLE suscriptores ADD COLUMN IF NOT EXISTS telegram_chat_id TEXT NOT NULL DEFAULT '';
ALTER TABLE suscriptores ADD COLUMN IF NOT EXISTS telegram_usuario TEXT NOT NULL DEFAULT '';
ALTER TABLE suscriptores ADD COLUMN IF NOT EXISTS verificado BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE suscriptores ADD COLUMN IF NOT EXISTS codigo_hash TEXT NOT NULL DEFAULT '';
ALTER TABLE suscriptores ADD COLUMN IF NOT EXISTS codigo_expira TIMESTAMP;
ALTER TABLE suscriptores ADD COLUMN IF NOT EXISTS intentos_codigo INTEGER NOT NULL DEFAULT 0;
