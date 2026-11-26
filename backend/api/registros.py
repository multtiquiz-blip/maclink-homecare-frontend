"""
Rotas de registro de cuidado.

Cada rota:
1. Exige permissão (via matriz)
2. Confere vínculo do usuário com o paciente
3. Grava no SQLite com snapshot de autor (nome, papel, COREN)
4. Retorna id, dia e timestamp

Regra dura: a permissão é revalidada SEMPRE. A tela pode esconder,
mas o backend nunca confia.
"""

import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.api.deps import get_current_user, require
from backend.dados.repositorios import idosos as repo_idosos
from backend.dados.repositorios import registros as repo_registros
from backend.dados.repositorios import usuarios as repo_usuarios
from backend.dados.repositorios import vinculos as repo_vinculos
from backend.nucleo.permissoes import Acao, Usuario
from backend.nucleo.tarefas import dia_de_cuidado


router = APIRouter(prefix="/registros", tags=["registros"])


class RegistroIn(BaseModel):
    idoso_id: str
    texto: str | None = None
    valor: str | None = None


def _registrar(
    request: Request,
    user: Usuario,
    dados: RegistroIn,
    tipo: str,
) -> dict:
    """Função compartilhada por todas as rotas de registro."""
    conn = request.app.state.conn

    if not repo_vinculos.tem_vinculo(conn, user.id, dados.idoso_id):
        raise HTTPException(status_code=403, detail="Sem vínculo com este paciente")

    user_db = repo_usuarios.buscar(conn, user.id)
    if user_db is None:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    agora = int(time.time())
    dia = dia_de_cuidado(agora)
    rid = f"r_{uuid.uuid4().hex[:12]}"

    repo_registros.criar(
        conn,
        id=rid,
        idoso_id=dados.idoso_id,
        dia=dia,
        tipo=tipo,
        autor_id=user.id,
        autor_nome=user_db.nome,
        autor_papel=user.papel.value,
        autor_coren=user_db.coren,
        texto=dados.texto,
        valor=dados.valor,
    )
    return {"id": rid, "dia": dia, "ts": agora, "tipo": tipo}


# ---------------------------------------------------------------------------
# Registros comuns (livres para qualquer perfil autorizado)
# ---------------------------------------------------------------------------

@router.post("/agua")
def agua(
    dados: RegistroIn,
    request: Request,
    user: Usuario = Depends(require(Acao.REGISTRAR_AGUA)),
) -> dict:
    return _registrar(request, user, dados, "agua")


@router.post("/banheiro")
def banheiro(
    dados: RegistroIn,
    request: Request,
    user: Usuario = Depends(require(Acao.REGISTRAR_BANHEIRO)),
) -> dict:
    return _registrar(request, user, dados, "banheiro")


@router.post("/sono")
def sono(
    dados: RegistroIn,
    request: Request,
    user: Usuario = Depends(require(Acao.REGISTRAR_SONO)),
) -> dict:
    return _registrar(request, user, dados, "sono")


@router.post("/humor")
def humor(
    dados: RegistroIn,
    request: Request,
    user: Usuario = Depends(require(Acao.REGISTRAR_HUMOR)),
) -> dict:
    return _registrar(request, user, dados, "humor")


@router.post("/passeio")
def passeio(
    dados: RegistroIn,
    request: Request,
    user: Usuario = Depends(require(Acao.REGISTRAR_PASSEIO)),
) -> dict:
    return _registrar(request, user, dados, "passeio")


@router.post("/dor")
def dor(
    dados: RegistroIn,
    request: Request,
    user: Usuario = Depends(require(Acao.REGISTRAR_DOR)),
) -> dict:
    return _registrar(request, user, dados, "dor")


@router.post("/queda")
def queda(
    dados: RegistroIn,
    request: Request,
    user: Usuario = Depends(require(Acao.REGISTRAR_QUEDA)),
) -> dict:
    return _registrar(request, user, dados, "queda")


# ---------------------------------------------------------------------------
# Leitura de registros do dia
# ---------------------------------------------------------------------------

@router.get("/{idoso_id}/dia")
def registros_do_dia(
    idoso_id: str,
    request: Request,
    user: Usuario = Depends(get_current_user),
) -> dict:
    """Lista registros do dia de cuidado do paciente."""
    conn = request.app.state.conn
    if not repo_vinculos.tem_vinculo(conn, user.id, idoso_id):
        raise HTTPException(status_code=403, detail="Sem vínculo com este paciente")

    dia = dia_de_cuidado(int(time.time()))
    lista = repo_registros.listar_por_dia(conn, idoso_id, dia)
    return {
        "dia": dia,
        "idoso_id": idoso_id,
        "registros": [
            {
                "id": r.id,
                "ts": r.ts,
                "tipo": r.tipo,
                "texto": r.texto,
                "valor": r.valor,
                "autor_nome": r.autor_nome,
                "autor_papel": r.autor_papel,
                "corrigido": r.corrigido,
            }
            for r in lista
        ],
    }
