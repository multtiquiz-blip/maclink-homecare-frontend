"""
Ponto de entrada do modo local (notebook/tablet).

Uso:
    uvicorn backend.modo_local.main:app --reload

O banco fica em `maclink.sqlite` na pasta atual (configurável via
variável de ambiente MACLINK_DB).
"""

import os

from backend.api.main import create_app
from backend.dados.conexao import conectar, inicializar


DB_PATH = os.environ.get("MACLINK_DB", "maclink.sqlite")

inicializar(DB_PATH)
_conn = conectar(DB_PATH)

app = create_app(_conn)
