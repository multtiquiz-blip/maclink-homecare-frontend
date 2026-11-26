"""
Endpoint do painel de pacientes.

Agora calcula fora_do_limite de verdade: usa o snapshot `limite_vigente`
gravado em cada registro (não o plano atual — histórico importa).
"""

import json
import time

from fastapi import APIRouter, Depends, Request

from backend.api.deps import get_current_user
from backend.dados.repositorios import idosos as repo_idosos
from backend.dados.repositorios import registros as repo_registros
from backend.dados.repositorios import vinculos as repo_vinculos
from backend.nucleo.limites import avaliar_numeros
from backend.nucleo.painel import (
    EstadoPaciente,
    RegistroResumo,
    calcular_resumo,
)
from backend.nucleo.permissoes import Usuario
from backend.nucleo.tarefas import dia_de_cuidado


router = APIRouter(prefix="/painel", tags=["painel"])


TIPOS_NUMERICOS = {"pressao", "oxigenio", "temperatura", "dextro"}


@router.get("")
def painel(
    request: Request,
    user: Usuario = Depends(get_current_user),
) -> dict:
    conn = request.app.state.conn
    agora = int(time.time())
    dia = dia_de_cuidado(agora)

    paciente_ids = repo_vinculos.listar_pacientes_do_usuario(conn, user.id)
    pacientes_db = repo_idosos.listar_por_ids(conn, paciente_ids)

    resultado = []
    for idoso in pacientes_db:
        registros_rows = repo_registros.listar_por_dia(conn, idoso.id, dia)
        regs_resumo = [_resumo_de_registro(r) for r in registros_rows]
        resumo = calcular_resumo(idoso.id, regs_resumo, [], agora=agora)
        resultado.append({
            "idoso_id": idoso.id,
            "nome": idoso.nome,
            "estado": resumo.estado.value,
            "frase": resumo.frase_curta,
            "ultima_acao_ts": resumo.ultima_acao_ts,
            "ultima_acao_texto": resumo.ultima_acao_texto,
            "tem_alerta_critico": resumo.tem_alerta_critico,
        })

    return {"dia": dia, "total": len(resultado), "pacientes": resultado}


def _resumo_de_registro(r) -> RegistroResumo:
    fora = False
    motivos: list = []
    if r.tipo in TIPOS_NUMERICOS and r.valor and r.limite_vigente:
        try:
            valor = json.loads(r.valor)
            limite = json.loads(r.limite_vigente)
            aval = avaliar_numeros(r.tipo, valor, limite)
            fora = aval["fora"]
            motivos = aval["motivos"]
        except (json.JSONDecodeError, TypeError):
            pass
    return RegistroResumo(
        ts=r.ts,
        tipo=r.tipo,
        texto=r.texto,
        valor=r.valor,
        fora_do_limite=fora,
        motivos=motivos,
    )
