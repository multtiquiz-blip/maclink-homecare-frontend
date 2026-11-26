"""
Dependências FastAPI: sessão, usuário atual, checagem de permissão.

A sessão fica em memória (dict token → usuario_id) por simplicidade
no piloto. Fase 2: migrar para JWT ou tabela no banco.
"""

import secrets
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request

from backend.dados.repositorios import usuarios as repo_usuarios
from backend.nucleo.permissoes import Acao, Papel, Usuario, pode


# Sessões em memória: token → usuario_id
_sessions: dict[str, str] = {}


def create_session(usuario_id: str) -> str:
    """Cria um token de sessão para o usuário."""
    token = secrets.token_urlsafe(32)
    _sessions[token] = usuario_id
    return token


def destroy_session(token: str) -> None:
    """Invalida um token de sessão."""
    _sessions.pop(token, None)


def _usuario_db_para_usuario(db) -> Usuario:
    """Converte o registro do banco para o dataclass de permissão."""
    return Usuario(
        id=db.id,
        papel=Papel(db.papel),
        categoria=db.categoria,
        verificado=db.verificado,
        ativo=db.ativo,
    )


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> Usuario:
    """
    Extrai o usuário atual do token de sessão.

    Levanta 401 se o token estiver ausente, inválido ou o usuário
    não existir mais (ou estiver inativo).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")
    token = authorization.removeprefix("Bearer ")
    usuario_id = _sessions.get(token)
    if not usuario_id:
        raise HTTPException(status_code=401, detail="Sessão inválida")
    conn = request.app.state.conn
    db = repo_usuarios.buscar(conn, usuario_id)
    if db is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return _usuario_db_para_usuario(db)


def require(acao: Acao):
    """
    Fábrica de dependência que exige uma permissão.

    Uso:
        @app.post("/registrar/dextro")
        def dextro(user: Usuario = Depends(require(Acao.REGISTRAR_DEXTRO))):
            ...
    """
    def checker(user: Usuario = Depends(get_current_user)) -> Usuario:
        if not pode(acao, user):
            raise HTTPException(
                status_code=403,
                detail=f"Sem permissão para: {acao.value}",
            )
        return user
    return checker
