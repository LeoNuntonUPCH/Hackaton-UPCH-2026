-- Migración para bases creadas con la versión anterior del esquema.
ALTER TABLE comunicaciones ADD COLUMN IF NOT EXISTS proveedor TEXT NOT NULL DEFAULT 'No disponible';
ALTER TABLE comunicaciones ADD COLUMN IF NOT EXISTS id_externo TEXT NOT NULL DEFAULT '';
ALTER TABLE comunicaciones ADD COLUMN IF NOT EXISTS error TEXT NOT NULL DEFAULT '';
ALTER TABLE comunicaciones ADD COLUMN IF NOT EXISTS intentos INTEGER NOT NULL DEFAULT 0;
ALTER TABLE comunicaciones ADD COLUMN IF NOT EXISTS destino TEXT NOT NULL DEFAULT '';
ALTER TABLE comunicaciones ADD COLUMN IF NOT EXISTS clave_idempotencia TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_comunicaciones_clave
    ON comunicaciones (clave_idempotencia);
