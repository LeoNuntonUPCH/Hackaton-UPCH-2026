CREATE TABLE IF NOT EXISTS suscriptores (
    telefono       TEXT NOT NULL,
    canal          TEXT NOT NULL DEFAULT 'SMS',
    quebrada       TEXT NOT NULL,
    nombre         TEXT NOT NULL DEFAULT '',
    lat            DOUBLE PRECISION,
    lon            DOUBLE PRECISION,
    consentimiento BOOLEAN NOT NULL DEFAULT FALSE,
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    creado         TIMESTAMP NOT NULL,
    origen         TEXT NOT NULL DEFAULT 'web',
    telegram_chat_id TEXT NOT NULL DEFAULT '',
    telegram_usuario TEXT NOT NULL DEFAULT '',
    verificado     BOOLEAN NOT NULL DEFAULT TRUE,
    codigo_hash    TEXT NOT NULL DEFAULT '',
    codigo_expira  TIMESTAMP,
    intentos_codigo INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (canal, telefono)
);

CREATE INDEX IF NOT EXISTS idx_suscriptores_quebrada
    ON suscriptores (quebrada);
