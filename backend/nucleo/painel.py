"""
Cálculo do resumo por paciente para o painel.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EstadoPaciente(str, Enum):
    EM_DIA = "em_dia"
    ATENCAO = "atencao"
    ATRASADO = "atrasado"
    ALERTA = "alerta"


@dataclass
class RegistroResumo:
    ts: int
    tipo: str
    texto: Optional[str] = None
    valor: Optional[str] = None
    fora_do_limite: bool = False
    motivos: list = field(default_factory=list)


@dataclass
class TarefaResumo:
    id: str
    nome: str
    hora_alvo: int
    feita: bool = False
    atrasada: bool = False
    minutos_para_vencer: int = 0


@dataclass
class ResumoPaciente:
    idoso_id: str
    estado: EstadoPaciente
    frase_curta: str
    ultima_acao_ts: Optional[int] = None
    ultima_acao_texto: Optional[str] = None
    pendencias: list = field(default_factory=list)
    proxima_tarefa: Optional[TarefaResumo] = None
    tem_alerta_critico: bool = False


def calcular_resumo(
    idoso_id: str,
    registros_hoje: list,
    tarefas_hoje: list,
    agora: int,
    janela_atencao_min: int = 30,
) -> ResumoPaciente:
    tem_alerta = any(r.fora_do_limite for r in registros_hoje)
    tarefas_atrasadas = [t for t in tarefas_hoje if t.atrasada and not t.feita]
    tarefas_proximas = [
        t for t in tarefas_hoje
        if not t.feita and 0 <= t.minutos_para_vencer <= janela_atencao_min
    ]
    ultima = max(registros_hoje, key=lambda r: r.ts, default=None)

    if tem_alerta:
        estado = EstadoPaciente.ALERTA
        frase = _frase_alerta(registros_hoje)
    elif tarefas_atrasadas:
        estado = EstadoPaciente.ATRASADO
        frase = f"{len(tarefas_atrasadas)} tarefa(s) atrasada(s)"
    elif tarefas_proximas:
        estado = EstadoPaciente.ATENCAO
        frase = f"{tarefas_proximas[0].nome} em breve"
    else:
        estado = EstadoPaciente.EM_DIA
        frase = "Tudo em dia"

    proxima = min(
        (t for t in tarefas_hoje if not t.feita and t.minutos_para_vencer >= 0),
        key=lambda t: t.minutos_para_vencer,
        default=None,
    )

    return ResumoPaciente(
        idoso_id=idoso_id,
        estado=estado,
        frase_curta=frase,
        ultima_acao_ts=ultima.ts if ultima else None,
        ultima_acao_texto=ultima.texto if ultima else None,
        pendencias=tarefas_atrasadas,
        proxima_tarefa=proxima,
        tem_alerta_critico=tem_alerta,
    )


def _frase_alerta(registros_hoje: list) -> str:
    """
    Monta a frase acionável do alerta.

    Preferência:
    1. Primeiro motivo detalhado (do avaliar_numeros) — "Pressão sistólica 170 acima do limite 150"
    2. Texto + valor do registro — "Pressão 180/110 fora do limite"
    3. Texto sozinho — "Pressão fora do limite"
    4. Fallback genérico — "Alerta ativo"
    """
    criticos = [r for r in registros_hoje if r.fora_do_limite]
    if not criticos:
        return "Alerta ativo"

    r = criticos[-1]

    # 1. Motivo detalhado (do lote 7)
    if r.motivos:
        return r.motivos[0]

    # 2. Texto + valor (compatível com testes anteriores)
    if r.texto and r.valor:
        return f"{r.texto} {r.valor} fora do limite"

    # 3. Texto sozinho
    if r.texto:
        return f"{r.texto} fora do limite"

    # 4. Fallback
    return "Alerta ativo"
