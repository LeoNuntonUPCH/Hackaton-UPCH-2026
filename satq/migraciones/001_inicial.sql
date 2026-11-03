CREATE TABLE IF NOT EXISTS quebradas (
    codigo       TEXT PRIMARY KEY,
    nombre       TEXT NOT NULL,
    distrito     TEXT NOT NULL,
    provincia    TEXT NOT NULL,
    departamento TEXT NOT NULL,
    lat          DOUBLE PRECISION NOT NULL,
    lon          DOUBLE PRECISION NOT NULL,
    destinatarios INTEGER NOT NULL DEFAULT 0,
    grupo        TEXT NOT NULL DEFAULT 'Comité local de prevención',
    destacada    BOOLEAN NOT NULL DEFAULT FALSE,
    lecturas     JSONB NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS alertas (
    codigo      TEXT PRIMARY KEY,
    quebrada    TEXT NOT NULL,
    momento     TIMESTAMP NOT NULL,
    nivel       TEXT NOT NULL,
    estado      TEXT NOT NULL,
    fuente      TEXT NOT NULL,
    acumulado   DOUBLE PRECISION NOT NULL,
    nota        TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS comunicaciones (
    id            SERIAL PRIMARY KEY,
    momento       TIMESTAMP NOT NULL,
    quebrada      TEXT NOT NULL,
    destinatarios INTEGER NOT NULL,
    canal         TEXT NOT NULL,
    resultado     TEXT NOT NULL,
    entrega_real  TEXT NOT NULL DEFAULT 'No disponible',
    proveedor     TEXT NOT NULL DEFAULT 'No disponible',
    id_externo    TEXT NOT NULL DEFAULT '',
    error         TEXT NOT NULL DEFAULT '',
    intentos      INTEGER NOT NULL DEFAULT 0,
    destino       TEXT NOT NULL DEFAULT '',
    clave_idempotencia TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS historial_parametros (
    id          SERIAL PRIMARY KEY,
    momento     TIMESTAMP NOT NULL,
    parametro   TEXT NOT NULL,
    responsable TEXT NOT NULL,
    critico     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS umbrales (
    id            INTEGER PRIMARY KEY CHECK (id = 1),
    bajo          DOUBLE PRECISION NOT NULL,
    moderado      DOUBLE PRECISION NOT NULL,
    alto          DOUBLE PRECISION NOT NULL,
    critico       DOUBLE PRECISION NOT NULL,
    ventana_horas INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alertas_quebrada
    ON alertas (quebrada);
CREATE INDEX IF NOT EXISTS idx_comunicaciones_quebrada
    ON comunicaciones (quebrada);

CREATE TABLE IF NOT EXISTS ingestas (
    clave     TEXT PRIMARY KEY,
    huella    TEXT NOT NULL,
    resultado JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS alertas_clave (
    clave     TEXT PRIMARY KEY,
    huella    TEXT NOT NULL,
    resultado JSONB NOT NULL
);