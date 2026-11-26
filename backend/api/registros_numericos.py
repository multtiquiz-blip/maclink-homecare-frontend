"""
Rotas de registro de medidas numéricas.

Pressão (com pulso), oxigênio (com pulso), temperatura e dextro.
Todas exigem permissão pela matriz COM o plano carregado, porque
cuidadora pode ter autorização no plano.

Regra dura: só enfermeiro verificado pode dextro.
"""

import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.api.deps import get_current_user
from backend.dados.repositorios import planos as repo_planos
from backend.dados.repositorios import registros as repo_registros
from backend.dados.repositorios import usuarios as repo_usuarios
from backend.dados.repositorios import vinculos as repo_vinculos
from backend.nucleo.limites import avaliar_numeros
from backend.nucleo.permissoes import Acao, Papel, Plano, Usuario, pode
from backend.nucleo.tarefas import dia_de_cuidado


router = APIRouter(prefix="/registros", tags=["registros-numericos"])


class NumeroIn(BaseModel):
    idoso_id: str
    valor: dict  # pressao: {"sis":160,"dia":100,"pulso":88} etc.


def _plano_para_checagem(idoso_id: str, plano_db) -> Plano:
    return Plano(
        idoso_id=idoso_id,
        liberacoes=plano_db.liberacoes if plano_db else {},
        autorizacoes=plano_db.autorizacoes if plano_db else {},
    )


def _formatar(tipo: str, valor: dict) -> str:
    if tipo == "pressao":
        s = f"Pressão {valor.get('sis')}/{valor.get('dia')}"
        if valor.get("pulso") is not None:
            s += f" · pulso {valor['pulso']}"
        return s
    if tipo == "oxigenio":
        s = f"Oxigênio {valor.get('spo')}%"
        if valor.get("pulso") is not None:
            s += f" · pulso {valor['pulso']}"
        return s
    if tipo == "temperatura":
        return f"Temperatura {valor.get('temp')} °C"
    if tipo == "dextro":
        return f"Dextro {valor.get('dextro')} mg/dL"
    return tipo


def _registrar_numerico(
    request: Request,
    user: Usuario,
    dados: NumeroIn,
    tipo: str,
    acao: Acao,
) -> dict:
    conn = request.app.state.conn

    if not repo_vinculos.tem_vinculo(conn, user.id, dados.idoso_id):
        raise HTTPException(status_code=403, detail="Sem vínculo com este paciente")

    plano_db = repo_planos.buscar_por_idoso(conn, dados.idoso_id)
    plano = _plano_para_checagem(dados.idoso_id, plano_db)

    if not pode(acao, user, plano):
        raise HTTPException(
            status_code=403,
            detail=f"Sem permissão para registrar {tipo}",
        )

    user_db = repo_usuarios.buscar(conn, user.id)
    agora = int(time.time())
    dia = dia_de_cuidado(agora)
    rid = f"r_{uuid.uuid4().hex[:12]}"

    limites_snapshot = plano_db.limites if plano_db else {}

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
        texto=_formatar(tipo, dados.valor),
        valor=json.dumps(dados.valor),
        limite_vigente=json.dumps(limites_snapshot),
    )

    aval = avaliar_numeros(tipo, dados.valor, limites_snapshot)

    return {
        "id": rid,
        "dia": dia,
        "ts": agora,
        "tipo": tipo,
        "fora_do_limite": aval["fora"],
        "motivos": aval["motivos"],
    }


@router.post("/pressao")
def pressao(
    dados: NumeroIn,
    request: Request,
    user: Usuario = Depends(get_current_user),
) -> dict:
    return _registrar_numerico(request, user, dados, "pressao", Acao.REGISTRAR_PRESSAO)


@router.post("/oxigenio")
def oxigenio(
    dados: NumeroIn,
    request: Request,
    user: Usuario = Depends(get_current_user),
) -> dict:
    return _registrar_numerico(request, user, dados, "oxigenio", Acao.REGISTRAR_OXIGENIO)


@router.post("/temperatura")
def temperatura(
    dados: NumeroIn,
    request: Request,
    user: Usuario = Depends(get_current_user),
) -> dict:
    return _registrar_numerico(request, user, dados, "temperatura", Acao.REGISTRAR_TEMPERATURA)


@router.post("/dextro")
def dextro(
    dados: NumeroIn,
    request: Request,
    user: Usuario = Depends(get_current_user),
) -> dict:
    return _registrar_numerico(request, user, dados, "dextro", Acao.REGISTRAR_DEXTRO)
