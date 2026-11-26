"""
Rotas de autenticação: login e logout.

O login recebe usuario_id + pin, confere no banco (via repositorio)
e devolve um token de sessão.
"""

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from backend.api.deps import create_session, destroy_session
from backend.dados.repositorios import usuarios as repo_usuarios


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    usuario_id: str
    pin: str


class LoginOut(BaseModel):
    token: str
    usuario_id: str
    nome: str
    papel: str


@router.post("/login", response_model=LoginOut)
def login(dados: LoginIn, request: Request) -> LoginOut:
    """
    Autentica o usuário.

    Retorna 401 se o usuário não existe ou o PIN está errado.
    Nunca revela qual dos dois falhou (evita enumeração).
    """
    conn = request.app.state.conn
    if not repo_usuarios.autenticar(conn, dados.usuario_id, dados.pin):
        raise HTTPException(status_code=401, detail="Usuário ou PIN inválido")

    db = repo_usuarios.buscar(conn, dados.usuario_id)
    token = create_session(dados.usuario_id)
    return LoginOut(
        token=token,
        usuario_id=db.id,
        nome=db.nome,
        papel=db.papel,
    )


@router.post("/logout")
def logout(authorization: str = Header(...)) -> dict:
    """Invalida o token de sessão."""
    token = authorization.removeprefix("Bearer ")
    destroy_session(token)
    return {"ok": True}
