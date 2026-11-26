"""
App FastAPI do MacLink HomeCare.

Routers:
- /auth      → login/logout
- /registros → registros comuns (água, banheiro, sono, humor, passeio, dor, queda)
- /registros → medidas numéricas (pressão, oxigênio, temperatura, dextro) [novo]
- /painel    → painel de pacientes (com alerta real)
- /planos    → plano de cuidado

Rotas /registrar/* e /editar/* são apenas de TESTE de permissão.
"""

import sqlite3

from fastapi import Depends, FastAPI

from backend.api import auth, painel, planos, registros, registros_numericos
from backend.api.deps import get_current_user, require
from backend.nucleo.permissoes import Acao, Usuario


def create_app(conn: sqlite3.Connection) -> FastAPI:
    app = FastAPI(title="MacLink HomeCare", version="0.1.0")
    app.state.conn = conn

    # Routers reais
    app.include_router(auth.router)
    app.include_router(registros.router)
    app.include_router(registros_numericos.router)
    app.include_router(painel.router)
    app.include_router(planos.router)

    # Rotas de teste de permissão
    @app.get("/me")
    def me(user: Usuario = Depends(get_current_user)) -> dict:
        return {
            "id": user.id,
            "papel": user.papel.value,
            "verificado": user.verificado,
            "categoria": user.categoria,
        }

    @app.post("/registrar/agua")
    def teste_registrar_agua(
        user: Usuario = Depends(require(Acao.REGISTRAR_AGUA)),
    ) -> dict:
        return {"ok": True, "por": user.id, "acao": "agua"}

    @app.post("/registrar/dextro")
    def teste_registrar_dextro(
        user: Usuario = Depends(require(Acao.REGISTRAR_DEXTRO)),
    ) -> dict:
        return {"ok": True, "por": user.id, "acao": "dextro"}

    @app.post("/editar/plano")
    def teste_editar_plano(
        user: Usuario = Depends(require(Acao.EDITAR_PLANO)),
    ) -> dict:
        return {"ok": True, "por": user.id, "acao": "editar_plano"}

    return app
