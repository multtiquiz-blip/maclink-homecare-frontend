"""
Conferencia humana obrigatoria antes de gravar qualquer afericao.

REGRA DO PROPRIETARIO: o sistema captura, propoe e PARA. Nada entra no
historico do paciente sem que uma pessoa toque em Confirmar ou Corrigir.
Assim o erro do OCR nao vira erro no prontuario.

Fluxo:
  OCR -> interpretar() -> montar_proposta()  [nao grava nada]
                            |
                            +-- corrigir_campo()  (humano ajusta)
                            +-- confirmar()       (humano valida) -> registro
                            +-- descartar()       (humano rejeita) -> nada

Este modulo nao importa banco, camera, OCR nem HTTP. Regra pura, testavel.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EstadoConferencia(str, Enum):
    AGUARDANDO = "aguardando_conferencia"
    CORRIGIDA = "corrigida_pelo_humano"
    CONFIRMADA = "confirmada"
    DESCARTADA = "descartada"


OBRIGATORIOS = {
    "pressao": ("sis", "dia"),
    "oximetria": ("spo2",),
    "glicemia": ("glicemia",),
}

ROTULOS = {
    "sis": "Sistolica",
    "dia": "Diastolica",
    "pulso": "Pulso",
    "spo2": "Saturacao SpO2",
    "glicemia": "Glicemia",
}

UNIDADE_PADRAO = {
    "sis": "mmHg", "dia": "mmHg", "pulso": "bpm",
    "spo2": "%", "glicemia": "mg/dL",
}

ORDEM_CAMPOS = {
    "pressao": ("sis", "dia", "pulso"),
    "oximetria": ("spo2", "pulso"),
    "glicemia": ("glicemia",),
}


@dataclass
class CampoProposto:
    chave: str
    rotulo: str
    valor_proposto: Optional[float] = None
    valor_especial: Optional[str] = None
    unidade_proposta: Optional[str] = None
    origem: str = "ausente"
    confianca: float = 0.0
    inferido: bool = False
    obrigatorio: bool = False
    valor_confirmado: Optional[float] = None
    unidade_confirmada: Optional[str] = None
    especial_confirmado: Optional[str] = None
    corrigido: bool = False
    ausente: bool = True

    def tem_valor(self) -> bool:
        return self.valor_confirmado is not None or self.especial_confirmado is not None

    def para_exibir(self) -> dict:
        return {
            "chave": self.chave,
            "rotulo": self.rotulo,
            "proposto": self.valor_especial if self.valor_especial else self.valor_proposto,
            "unidade_proposta": self.unidade_proposta,
            "confirmado": self.especial_confirmado if self.especial_confirmado else self.valor_confirmado,
            "unidade_confirmada": self.unidade_confirmada,
            "origem": self.origem,
            "inferido": self.inferido,
            "corrigido": self.corrigido,
            "obrigatorio": self.obrigatorio,
            "ausente": self.ausente,
            "confianca": round(self.confianca, 3),
        }


@dataclass
class Proposta:
    tipo: str
    campos: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    ilegivel: bool = False
    exige_atencao: bool = False
    texto_bruto: str = ""
    unidade_detectada: Optional[str] = None
    estado: EstadoConferencia = EstadoConferencia.AGUARDANDO
    confirmada_por: Optional[str] = None
    confirmada_em: Optional[int] = None
    ts_efetivo: Optional[int] = None
    ts_programado: Optional[int] = None
    tarefa_id: Optional[str] = None
    observacao: str = ""
    motivo_descarte: str = ""

    def campo(self, chave: str) -> Optional[CampoProposto]:
        for c in self.campos:
            if c.chave == chave:
                return c
        return None

    def resumo(self) -> dict:
        return {
            "tipo": self.tipo,
            "estado": self.estado.value,
            "campos": [c.para_exibir() for c in self.campos],
            "avisos": list(self.avisos),
            "ilegivel": self.ilegivel,
            "exige_atencao": self.exige_atencao,
            "unidade_detectada": self.unidade_detectada,
            "ts_programado": self.ts_programado,
            "ts_efetivo": self.ts_efetivo,
            "tarefa_id": self.tarefa_id,
            "confirmada_por": self.confirmada_por,
            "confirmada_em": self.confirmada_em,
        }


def montar_proposta(leitura, *, ts_programado=None, tarefa_id=None, ts_efetivo=None) -> Proposta:
    """
    Converte a leitura do OCR em proposta para conferencia.
    NAO grava nada. NAO confirma nada.
    """
    tipo = getattr(leitura.tipo, "value", leitura.tipo)
    obr = OBRIGATORIOS.get(tipo, ())
    p = Proposta(
        tipo=tipo,
        avisos=list(getattr(leitura, "avisos", []) or []),
        ilegivel=bool(getattr(leitura, "ilegivel", False)),
        texto_bruto=getattr(leitura, "texto_bruto", "") or "",
        unidade_detectada=getattr(leitura, "unidade_detectada", None),
        ts_programado=ts_programado,
        ts_efetivo=ts_efetivo,
        tarefa_id=tarefa_id,
    )
    src = getattr(leitura, "campos", {}) or {}
    for chave in ORDEM_CAMPOS.get(tipo, ()):
        c = src.get(chave)
        cp = CampoProposto(
            chave=chave,
            rotulo=ROTULOS.get(chave, chave),
            obrigatorio=chave in obr,
        )
        if c is not None:
            cp.valor_proposto = getattr(c, "valor", None)
            cp.valor_especial = getattr(c, "valor_especial", None)
            cp.unidade_proposta = getattr(c, "unidade", None) or UNIDADE_PADRAO.get(chave)
            cp.origem = getattr(c, "origem", "rotulo")
            cp.confianca = float(getattr(c, "confianca", 0.0) or 0.0)
            cp.inferido = bool(getattr(c, "inferido", False))
            cp.ausente = cp.valor_proposto is None and cp.valor_especial is None
            cp.valor_confirmado = cp.valor_proposto
            cp.especial_confirmado = cp.valor_especial
            cp.unidade_confirmada = cp.unidade_proposta
        else:
            cp.unidade_proposta = UNIDADE_PADRAO.get(chave)
            cp.unidade_confirmada = cp.unidade_proposta
        p.campos.append(cp)

    p.exige_atencao = bool(
        p.ilegivel or p.avisos
        or any(c.inferido or c.ausente for c in p.campos if c.obrigatorio)
    )
    if p.ilegivel:
        p.avisos.append("Nada foi reconhecido com seguranca. Digite os valores do visor ou capture de novo.")
    for c in p.campos:
        if c.obrigatorio and c.ausente:
            p.avisos.append("Falta " + c.rotulo + ". Leia no aparelho e digite.")
        elif c.inferido:
            p.avisos.append(c.rotulo + " foi inferido sem rotulo no visor. Confira antes de confirmar.")
    return p


def corrigir_campo(proposta, chave: str, valor, unidade=None, especial=None) -> Proposta:
    """
    Humano corrige um campo. Aceita numero, HI/LO/ERR, ou None para limpar.
    Marca o campo como corrigido e a proposta como CORRIGIDA.
    """
    if proposta.estado in (EstadoConferencia.CONFIRMADA, EstadoConferencia.DESCARTADA):
        raise ValueError("Proposta ja encerrada: nao pode ser corrigida.")
    c = proposta.campo(chave)
    if c is None:
        raise ValueError("Campo desconhecido para este tipo: " + str(chave))

    if especial is not None:
        esp = str(especial).strip().upper()
        if esp not in ("HI", "LO", "ERR"):
            raise ValueError("Indicador especial invalido. Use HI, LO ou ERR.")
        if proposta.tipo != "glicemia":
            raise ValueError("HI/LO so se aplica a glicemia.")
        c.especial_confirmado = esp
        c.valor_confirmado = None
    elif valor is None or valor == "":
        c.valor_confirmado = None
        c.especial_confirmado = None
    else:
        try:
            n = float(str(valor).replace(",", "."))
        except (TypeError, ValueError):
            raise ValueError("Valor nao numerico. Digite o numero do visor ou use HI/LO.")
        if n != n:
            raise ValueError("Valor invalido.")
        c.valor_confirmado = n
        c.especial_confirmado = None

    if unidade:
        c.unidade_confirmada = str(unidade)
    c.corrigido = True
    c.ausente = not c.tem_valor()
    proposta.estado = EstadoConferencia.CORRIGIDA
    return proposta


def pode_confirmar(proposta) -> tuple:
    """Retorna (pode, motivo). Nunca confirma com obrigatorio vazio."""
    if proposta.estado in (EstadoConferencia.CONFIRMADA, EstadoConferencia.DESCARTADA):
        return False, "Esta proposta ja foi encerrada."
    faltam = [c.rotulo for c in proposta.campos if c.obrigatorio and not c.tem_valor()]
    if faltam:
        return False, "Preencha antes de confirmar: " + ", ".join(faltam) + "."
    for c in proposta.campos:
        if c.tem_valor() and not c.unidade_confirmada:
            return False, "Informe a unidade de " + c.rotulo + "."
    if proposta.tipo == "pressao":
        s = proposta.campo("sis")
        d = proposta.campo("dia")
        if s and d and s.valor_confirmado is not None and d.valor_confirmado is not None:
            if s.valor_confirmado <= d.valor_confirmado:
                return False, "Sistolica deve ser maior que diastolica. Confira os dois numeros."
    return True, ""


def confirmar(proposta, *, usuario_id: str, ts_efetivo: int, observacao: str = "") -> dict:
    """
    Confirmacao humana explicita. Unico caminho que produz registro.
    Devolve o payload pronto para persistir, com o que o OCR propos
    e o que a pessoa confirmou — para auditoria.
    """
    if not usuario_id:
        raise ValueError("Confirmacao exige pessoa identificada.")
    if ts_efetivo is None:
        raise ValueError("Informe o horario efetivo da medicao.")
    ok, motivo = pode_confirmar(proposta)
    if not ok:
        raise ValueError(motivo)

    proposta.estado = EstadoConferencia.CONFIRMADA
    proposta.confirmada_por = usuario_id
    proposta.confirmada_em = ts_efetivo
    proposta.ts_efetivo = ts_efetivo
    proposta.observacao = observacao or ""

    nums, especiais, proposed, confirmed, corrigidos = {}, {}, {}, {}, []
    for c in proposta.campos:
        proposed[c.chave] = c.valor_especial if c.valor_especial else c.valor_proposto
        if c.especial_confirmado:
            especiais[c.chave] = c.especial_confirmado
            confirmed[c.chave] = c.especial_confirmado
        elif c.valor_confirmado is not None:
            nums[c.chave] = c.valor_confirmado
            confirmed[c.chave] = c.valor_confirmado
        else:
            confirmed[c.chave] = None
        if c.corrigido:
            corrigidos.append(c.chave)

    partes = []
    for c in proposta.campos:
        if c.especial_confirmado:
            partes.append(c.rotulo + " " + c.especial_confirmado)
        elif c.valor_confirmado is not None:
            v = c.valor_confirmado
            txt = str(int(v)) if float(v).is_integer() else str(v).replace(".", ",")
            partes.append(c.rotulo + " " + txt + " " + (c.unidade_confirmada or ""))
    valor_txt = " · ".join(partes).strip()

    return {
        "schema": "maclink.homecare.measurement.v1",
        "tipo": proposta.tipo,
        "ts_efetivo": ts_efetivo,
        "ts_programado": proposta.ts_programado,
        "tarefa_id": proposta.tarefa_id,
        "nums": nums,
        "especiais": especiais,
        "unidades": {c.chave: c.unidade_confirmada for c in proposta.campos if c.tem_valor()},
        "valor": valor_txt,
        "observacao": proposta.observacao,
        "confirmado_por": usuario_id,
        "confirmado_em": ts_efetivo,
        "origem_leitura": "ocr_camera" if proposta.texto_bruto else "digitacao_manual",
        "conferencia": {
            "proposto": proposed,
            "confirmado": confirmed,
            "corrigidos": corrigidos,
            "inferidos": [c.chave for c in proposta.campos if c.inferido],
            "ilegivel": proposta.ilegivel,
            "avisos": list(proposta.avisos),
            "texto_bruto": proposta.texto_bruto,
            "houve_correcao": bool(corrigidos),
        },
    }


def descartar(proposta, *, usuario_id: str, motivo: str) -> dict:
    """Humano rejeita a leitura. Nada e gravado no historico clinico."""
    if not usuario_id:
        raise ValueError("Descarte exige pessoa identificada.")
    if not motivo or not motivo.strip():
        raise ValueError("Descreva por que a leitura foi descartada.")
    if proposta.estado is EstadoConferencia.CONFIRMADA:
        raise ValueError("Leitura ja confirmada: nao pode ser descartada.")
    proposta.estado = EstadoConferencia.DESCARTADA
    proposta.motivo_descarte = motivo.strip()
    return {
        "schema": "maclink.homecare.measurement-discarded.v1",
        "tipo": proposta.tipo,
        "descartado_por": usuario_id,
        "motivo": proposta.motivo_descarte,
        "texto_bruto": proposta.texto_bruto,
        "gera_registro_clinico": False,
    }
