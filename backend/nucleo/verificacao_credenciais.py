"""
Verificação de credenciais profissionais.

Duas lógicas separadas:
- Enfermagem (enfermeiro, técnico, auxiliar): COREN completo + situação ativa
- Cuidador com certificado: OCR do documento, validade extraída do próprio documento

Regra de ouro: não inventamos prazo. Usamos o que o COREN define
(para enfermagem) ou o que o documento diz (para cuidador).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class CategoriaEnfermagem(str, Enum):
    ENFERMEIRO = "enfermeiro"
    TECNICO = "tecnico"
    AUXILIAR = "auxiliar"


class StatusCoren(str, Enum):
    ATIVO = "ativo"
    PENDENTE = "pendente"
    SUSPENSO = "suspenso"
    CANCELADO = "cancelado"
    INVALIDO = "invalido"


@dataclass
class ResultadoCoren:
    """Resultado da consulta ao COREN."""
    status: StatusCoren
    categoria: Optional[CategoriaEnfermagem]
    nome: Optional[str]
    coren_numero: Optional[str]
    proxima_verificacao_em: Optional[int]  # timestamp
    motivo: Optional[str] = None


@dataclass
class CertificadoCuidador:
    """Dados extraídos do certificado do cuidador via OCR."""
    nome: str
    cpf: str
    instituicao: str
    curso: str
    carga_horaria: int
    data_emissao: int
    data_validade: Optional[int]  # None = documento não define validade
    codigo_autenticidade: Optional[str]
    cobre_pressao: bool = False
    cobre_oximetria: bool = False
    cobre_glicemia: bool = False


def parse_coren(coren: str) -> Optional[dict]:
    """
    Valida o formato do COREN completo.

    Formato oficial: COREN-UF-NUMERO-CATEGORIA
    Exemplo: COREN-MG-238295-ENF

    Categorias válidas: ENF, TE, AE
    Retorna dict com uf, numero, categoria ou None se inválido.
    """
    if not coren:
        return None

    partes = coren.strip().upper().split("-")
    if len(partes) != 4:
        return None

    prefixo, uf, numero, categoria = partes

    if prefixo != "COREN":
        return None

    if len(uf) != 2 or not uf.isalpha():
        return None

    if not numero.isdigit():
        return None

    mapa_categoria = {
        "ENF": CategoriaEnfermagem.ENFERMEIRO,
        "TE": CategoriaEnfermagem.TECNICO,
        "AE": CategoriaEnfermagem.AUXILIAR,
    }

    if categoria not in mapa_categoria:
        return None

    return {
        "uf": uf,
        "numero": numero,
        "categoria": mapa_categoria[categoria],
        "coren_completo": f"COREN-{uf}-{numero}-{categoria}",
    }


def verificar_coren(
    coren: str,
    consulta_fn=None,
) -> ResultadoCoren:
    """
    Verifica o COREN.

    `consulta_fn` é uma função injetável que consulta a base oficial.
    No piloto, pode ser None (verificação manual). Na fase 2, é a
    consulta ao SIGEN/Cofen por CPF.

    Regras:
    - Formato inválido → INVALIDO
    - Categoria não reconhecida → INVALIDO
    - Consulta indisponível → PENDENTE (cai para cuidadora)
    - Status não ativo → mantém o status retornado
    - Ativo → ATIVO com categoria
    """
    parsed = parse_coren(coren)
    if parsed is None:
        return ResultadoCoren(
            status=StatusCoren.INVALIDO,
            categoria=None,
            nome=None,
            coren_numero=None,
            proxima_verificacao_em=None,
            motivo="Formato do COREN inválido",
        )

    # Verificação manual (piloto): assume pendente até alguém confirmar
    if consulta_fn is None:
        return ResultadoCoren(
            status=StatusCoren.PENDENTE,
            categoria=parsed["categoria"],
            nome=None,
            coren_numero=parsed["coren_completo"],
            proxima_verificacao_em=None,
            motivo="Verificação manual pendente",
        )

    # Consulta automática (fase 2)
    try:
        retorno = consulta_fn(coren)
    except Exception as e:
        return ResultadoCoren(
            status=StatusCoren.PENDENTE,
            categoria=parsed["categoria"],
            nome=None,
            coren_numero=parsed["coren_completo"],
            proxima_verificacao_em=None,
            motivo=f"Consulta indisponível: {e}",
        )

    return ResultadoCoren(
        status=StatusCoren(retorno["status"]),
        categoria=parsed["categoria"],
        nome=retorno.get("nome"),
        coren_numero=parsed["coren_completo"],
        proxima_verificacao_em=retorno.get("proxima_verificacao_em"),
        motivo=retorno.get("motivo"),
    )


def certificado_valido(
    cert: CertificadoCuidador,
    agora: int,
) -> bool:
    """
    Verifica se o certificado do cuidador é válido.

    - Se o documento tem data de validade, usa ela.
    - Se não tem, o certificado é válido até ser substituído/revogado
      (decisão: não inventar prazo).
    """
    if cert.data_validade is None:
        return True
    return cert.data_validade > agora


def permissoes_do_certificado(cert: CertificadoCuidador, agora: int) -> dict:
    """
    Retorna o que o certificado libera.

    Granular: só libera o que o documento cobre.
    Dextro NUNCA é liberado por certificado de cuidador.
    """
    if not certificado_valido(cert, agora):
        return {"pressao": False, "oximetria": False, "glicemia": False}

    return {
        "pressao": cert.cobre_pressao,
        "oximetria": cert.cobre_oximetria,
        "glicemia": cert.cobre_glicemia,
        "dextro": False,  # sempre False — privativo de enfermagem
    }
