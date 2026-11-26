-- =====================================================================
-- MacLink HomeCare — esquema SQLite (local) / PostgreSQL (nuvem)
-- Campos de sincronização: synced_at, device_id, origin_id
-- =====================================================================

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    papel TEXT NOT NULL,
    categoria TEXT,
    coren TEXT,
    coren_status TEXT,
    coren_verificado_em INTEGER,
    coren_proxima_verificacao INTEGER,
    verificado INTEGER NOT NULL DEFAULT 0,
    pin_hash TEXT NOT NULL,
    pin_salt TEXT NOT NULL,
    foto_path TEXT,
    telefone TEXT,
    email TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em INTEGER NOT NULL,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS idosos (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    idade INTEGER,
    quarto TEXT,
    alergia TEXT,
    dieta TEXT,
    obs TEXT,
    foto_path TEXT,
    consentimento_camera INTEGER DEFAULT 0,
    consentimento_app INTEGER DEFAULT 0,
    codigo_compartilhamento TEXT,
    codigo_expira_em INTEGER,
    codigo_gerado_por TEXT REFERENCES usuarios(id),
    codigo_usado_por TEXT REFERENCES usuarios(id),
    codigo_usado_em INTEGER,
    criado_em INTEGER NOT NULL,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS vinculos_paciente (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id),
    paciente_id TEXT NOT NULL REFERENCES idosos(id),
    papel TEXT NOT NULL,
    vinculado_por TEXT REFERENCES usuarios(id),
    origem TEXT NOT NULL DEFAULT 'codigo',
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em INTEGER NOT NULL,
    revogado_em INTEGER,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT,
    UNIQUE(usuario_id, paciente_id, papel)
);

CREATE TABLE IF NOT EXISTS planos (
    id TEXT PRIMARY KEY,
    idoso_id TEXT NOT NULL REFERENCES idosos(id),
    perfil TEXT,
    periodo TEXT,
    pecas TEXT NOT NULL,
    limites TEXT NOT NULL,
    autorizacoes TEXT NOT NULL,
    liberacoes TEXT NOT NULL,
    escada TEXT NOT NULL,
    espera_min INTEGER NOT NULL DEFAULT 3,
    definido_por TEXT REFERENCES usuarios(id),
    definido_em INTEGER,
    versao INTEGER NOT NULL DEFAULT 1,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS config_reafericao (
    id TEXT PRIMARY KEY,
    plano_id TEXT NOT NULL REFERENCES planos(id),
    tipo_medida TEXT NOT NULL,
    condicao TEXT NOT NULL,
    valor_gatilho TEXT NOT NULL,
    intervalos TEXT NOT NULL,
    acao_se_persistir TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tarefas (
    id TEXT PRIMARY KEY,
    idoso_id TEXT NOT NULL REFERENCES idosos(id),
    peca TEXT NOT NULL,
    nome TEXT NOT NULL,
    hora TEXT,
    obs TEXT,
    so_enfermagem INTEGER NOT NULL DEFAULT 0,
    origem TEXT NOT NULL DEFAULT 'plano',
    registro_origem_id TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS registros (
    id TEXT PRIMARY KEY,
    idoso_id TEXT NOT NULL REFERENCES idosos(id),
    dia TEXT NOT NULL,
    ts INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    texto TEXT,
    valor TEXT,
    autor_id TEXT REFERENCES usuarios(id),
    autor_nome TEXT NOT NULL,
    autor_papel TEXT NOT NULL,
    autor_coren TEXT,
    limite_vigente TEXT,
    vinculo_reafericao TEXT,
    corrigido INTEGER NOT NULL DEFAULT 0,
    excluido INTEGER NOT NULL DEFAULT 0,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS registros_historico (
    id TEXT PRIMARY KEY,
    registro_id TEXT NOT NULL REFERENCES registros(id),
    ts INTEGER NOT NULL,
    autor_id TEXT REFERENCES usuarios(id),
    autor_nome TEXT NOT NULL,
    motivo TEXT NOT NULL,
    antes_texto TEXT,
    antes_valor TEXT
);

CREATE TABLE IF NOT EXISTS avisos (
    id TEXT PRIMARY KEY,
    idoso_id TEXT NOT NULL REFERENCES idosos(id),
    ts INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    descricao TEXT,
    estado TEXT NOT NULL,
    degrau INTEGER NOT NULL DEFAULT 0,
    escada TEXT NOT NULL,
    espera_min INTEGER NOT NULL,
    proximo_degrau_em INTEGER,
    encerrado INTEGER NOT NULL DEFAULT 0,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS avisos_tentativas (
    id TEXT PRIMARY KEY,
    aviso_id TEXT NOT NULL REFERENCES avisos(id),
    ts INTEGER NOT NULL,
    degrau INTEGER NOT NULL,
    contato_nome TEXT,
    resultado TEXT
);

CREATE TABLE IF NOT EXISTS envios (
    id TEXT PRIMARY KEY,
    idoso_id TEXT NOT NULL REFERENCES idosos(id),
    ts INTEGER NOT NULL,
    tipo_relatorio TEXT NOT NULL,
    destinatario_nome TEXT,
    destinatario_fone TEXT,
    destinatario_email TEXT,
    motivo TEXT,
    estado TEXT NOT NULL,
    pdf_hash TEXT NOT NULL,
    quem_gerou TEXT REFERENCES usuarios(id),
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS estoque (
    id TEXT PRIMARY KEY,
    idoso_id TEXT NOT NULL REFERENCES idosos(id),
    nome TEXT NOT NULL,
    qtd REAL NOT NULL DEFAULT 0,
    min REAL NOT NULL DEFAULT 0,
    unid TEXT,
    liga TEXT,
    critico INTEGER NOT NULL DEFAULT 0,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS estoque_movimentos (
    id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL REFERENCES estoque(id),
    ts INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    quantidade REAL NOT NULL,
    registrado_por TEXT REFERENCES usuarios(id),
    origem TEXT,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS comida (
    id TEXT PRIMARY KEY,
    idoso_id TEXT NOT NULL REFERENCES idosos(id),
    nome TEXT NOT NULL,
    pode INTEGER NOT NULL DEFAULT 1,
    obs TEXT,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS visitas (
    id TEXT PRIMARY KEY,
    idoso_id TEXT NOT NULL REFERENCES idosos(id),
    quem TEXT,
    que TEXT,
    dia TEXT,
    hora TEXT,
    obs TEXT,
    status TEXT NOT NULL DEFAULT 'agendado',
    realizado_em INTEGER,
    reagendado_para TEXT,
    registrado_por TEXT REFERENCES usuarios(id),
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS dor (
    id TEXT PRIMARY KEY,
    idoso_id TEXT NOT NULL REFERENCES idosos(id),
    registro_id TEXT REFERENCES registros(id),
    ts INTEGER NOT NULL,
    nivel INTEGER NOT NULL,
    local TEXT,
    quem_relatou TEXT,
    remedio_dado TEXT,
    intervencao TEXT,
    autor_id TEXT REFERENCES usuarios(id),
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS eventos_camera (
    id TEXT PRIMARY KEY,
    idoso_id TEXT NOT NULL REFERENCES idosos(id),
    ts INTEGER NOT NULL,
    tipo TEXT NOT NULL,
    confianca REAL,
    confirmado_por TEXT REFERENCES usuarios(id),
    confirmado_em INTEGER,
    acao_tomada TEXT,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS autorizacoes_cuidador (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id),
    tipo_autorizacao TEXT NOT NULL,
    fonte_validade TEXT NOT NULL,
    data_validade INTEGER,
    documento_hash TEXT,
    documento_path TEXT,
    status TEXT NOT NULL DEFAULT 'ativo',
    verificado_por TEXT REFERENCES usuarios(id),
    verificado_em INTEGER NOT NULL,
    synced_at INTEGER,
    device_id TEXT,
    origin_id TEXT
);

CREATE TABLE IF NOT EXISTS termos_versoes (
    versao TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,
    hash_documento TEXT NOT NULL,
    texto TEXT NOT NULL,
    vigente_desde INTEGER NOT NULL,
    vigente_ate INTEGER
);

CREATE TABLE IF NOT EXISTS aceites_termos (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id),
    tipo_termo TEXT NOT NULL,
    versao_termo TEXT NOT NULL,
    hash_documento TEXT NOT NULL,
    ts INTEGER NOT NULL,
    foto_path TEXT NOT NULL,
    hash_foto TEXT NOT NULL,
    scroll_completo INTEGER NOT NULL DEFAULT 0,
    device_id TEXT,
    ip TEXT,
    user_agent TEXT
);

CREATE TABLE IF NOT EXISTS dispositivos (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id),
    nome TEXT,
    ultimo_acesso INTEGER,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS auditoria (
    id TEXT PRIMARY KEY,
    ts INTEGER NOT NULL,
    usuario_id TEXT,
    usuario_nome TEXT,
    acao TEXT NOT NULL,
    detalhe TEXT,
    negado INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_registros_idoso_dia ON registros(idoso_id, dia);
CREATE INDEX IF NOT EXISTS idx_registros_ts ON registros(ts);
CREATE INDEX IF NOT EXISTS idx_dor_idoso_ts ON dor(idoso_id, ts);
CREATE INDEX IF NOT EXISTS idx_tarefas_idoso ON tarefas(idoso_id, ativo);
CREATE INDEX IF NOT EXISTS idx_vinculos_usuario ON vinculos_paciente(usuario_id, ativo);
CREATE INDEX IF NOT EXISTS idx_avisos_idoso ON avisos(idoso_id, encerrado);
CREATE INDEX IF NOT EXISTS idx_estoque_mov_ts ON estoque_movimentos(item_id, ts);
