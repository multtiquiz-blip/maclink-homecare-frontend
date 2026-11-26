"""
Conexão com o SQLite e inicialização do esquema.

O banco vive no aparelho (tablet/notebook). Um arquivo único.
Zero servidor, zero configuração.

`inicializar()` é idempotente: pode rodar várias vezes sem
recriar tabelas ou perder dados (usa CREATE TABLE IF NOT EXISTS).

IMPORTANTE: `check_same_thread=False` é necessário porque o
TestClient do FastAPI executa as rotas em um thread pool diferente
do thread que criou a conexão. Sem isso, o SQLite levanta
"SQLite objects created in a thread can only be used in that same thread".
"""

import sqlite3
from pathlib import Path


CAMINHO_ESQUEMA = Path(__file__).parent / "esquema.sql"


def conectar(caminho_db: str) -> sqlite3.Connection:
    """
    Abre conexão com o SQLite.

    Configurações:
    - check_same_thread=False: permite uso entre threads (FastAPI)
    - foreign_keys ON (integridade referencial)
    - row_factory = sqlite3.Row (acesso por nome de coluna)
    """
    conn = sqlite3.connect(caminho_db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar(caminho_db: str) -> None:
    """
    Cria o banco e executa o esquema.

    Idempotente: pode rodar quantas vezes precisar.
    """
    esquema = CAMINHO_ESQUEMA.read_text(encoding="utf-8")
    conn = conectar(caminho_db)
    try:
        conn.executescript(esquema)
        conn.commit()
    finally:
        conn.close()


def em_memoria() -> sqlite3.Connection:
    """
    Banco em memória — para testes.

    O esquema é executado na hora. Cada chamada cria um banco novo.
    check_same_thread=False pelo mesmo motivo de `conectar`.
    """
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    esquema = CAMINHO_ESQUEMA.read_text(encoding="utf-8")
    conn.executescript(esquema)
    return conn
