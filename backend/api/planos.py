"""
Rotas do plano de cuidado.

Só enfermeiro verificado pode criar/atualizar (regra no `require`).
Exige vínculo com o paciente.

Validações de conteúdo:
- perfil em PERFIS_VALIDOS
- periodo em PERIODOS_VALIDOS
- pecas em PECAS_VALIDAS
- espera_min >= 1 (via Pydantic)

Regra dura: limites chegam como vieram do enfermeiro. O sistema
não preenche número clínico nenhum.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.api.deps import get_current_user, require
from backend.dados.repositorios import planos as repo_planos
from backend.dados.repositorios import vinculos as repo_vinculos
from backend.nucleo.permissoes import Acao, Usuario


router = APIRouter(prefix="/planos", tags=["planos"])


PERFIS_VALIDOS = {
    "independente", "ajuda_parcial", "acamada", "demencia", "recuperacao",
}
PERIODOS_VALIDOS = {"noite", "dia", "24h", "personalizado"}
PECAS_VALIDAS = {
    "sono", "banheiro", "agua", "comida", "fralda", "banho", "posicao",
    "remedio", "pressao", "oxigenio", "temperatura", "dor", "humor",
    "passeio", "queda", "dextro",
}


class PlanoIn(BaseModel):
    idoso_id: str
    perfil: str
    periodo: str
    pecas: list[str]
    limites: dict = Field(default_factory=dict)
    autorizacoes: dict = Field(default_factory=dict)
    liberacoes: dict = Field(default_factory=dict)
    escada: list[str] = Field(default_factory=list)
    espera_min: int = Field(default=3, ge=1)


@router.post("")
def criar_ou_atualizar(
    dados: PlanoIn,
    request: Request,
    user: Usuario = Depends(require(Acao.EDITAR_PLANO)),
) -> dict:
    """
    Cria ou atualiza o plano do paciente.

    Só enfermeiro verificado (via matriz de permissões).
    """
    conn = request.app.state.conn

    if not repo_vinculos.tem_vinculo(conn, user.id, dados.idoso_id):
        raise HTTPException(status_code=403, detail="Sem vínculo com este paciente")

    if dados.perfil not in PERFIS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Perfil inválido: {dados.perfil}")
    if dados.periodo not in PERIODOS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"Período inválido: {dados.periodo}")

    invalidas = [p for p in dados.pecas if p not in PECAS_VALIDAS]
    if invalidas:
        raise HTTPException(status_code=400, detail=f"Peças inválidas: {invalidas}")

    plano_id = repo_planos.criar_ou_atualizar(
        conn,
        idoso_id=dados.idoso_id,
        perfil=dados.perfil,
        periodo=dados.periodo,
        pecas=dados.pecas,
        limites=dados.limites,
        autorizacoes=dados.autorizacoes,
        liberacoes=dados.liberacoes,
        escada=dados.escada,
        espera_min=dados.espera_min,
        definido_por=user.id,
    )
    return {"id": plano_id, "ok": True}


@router.get("/{idoso_id}")
def buscar(
    idoso_id: str,
    request: Request,
    user: Usuario = Depends(get_current_user),
) -> dict:
    """Retorna o plano vigente do paciente."""
    conn = request.app.state.conn
    if not repo_vinculos.tem_vinculo(conn, user.id, idoso_id):
        raise HTTPException(status_code=403, detail="Sem vínculo com este paciente")

    plano = repo_planos.buscar_por_idoso(conn, idoso_id)
    if plano is None:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    return {
        "id": plano.id,
        "idoso_id": plano.idoso_id,
        "perfil": plano.perfil,
        "periodo": plano.periodo,
        "pecas": plano.pecas,
        "limites": plano.limites,
        "autorizacoes": plano.autorizacoes,
        "liberacoes": plano.liberacoes,
        "escada": plano.escada,
        "espera_min": plano.espera_min,
        "definido_por": plano.definido_por,
        "definido_em": plano.definido_em,
        "versao": plano.versao,
    }
