"""
Aceite eletrônico e evidências de consentimento.

Fluxo obrigatório: rolar até o final + marcar checkbox + foto do rosto.
O pacote de evidências é a prova jurídica (LGPD art. 8º, §1º).
"""

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TipoTermo(str, Enum):
    USO = "uso"
    PRIVACIDADE = "privacidade"
    CAMERA = "camera"


@dataclass
class EvidenciaAceite:
    """Pacote de evidências do aceite."""
    usuario_id: str
    tipo_termo: TipoTermo
    versao_termo: str
    hash_documento: str      # SHA-256 do texto exato que o usuário viu
    ts: int
    foto_bytes: bytes        # foto do rosto no momento
    hash_foto: str           # SHA-256 da foto
    scroll_completo: bool
    device_id: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None


class ErroAceite(Exception):
    """Levantado quando o aceite é inválido."""
    pass


def calcular_hash(texto: str) -> str:
    """SHA-256 do texto do termo."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def validar_evidencia(ev: EvidenciaAceite) -> None:
    """
    Valida se o aceite é legítimo.

    Regras obrigatórias:
    - Scroll completo: usuário rolou até o final
    - Foto presente e com hash
    - Versão do termo preenchida
    - Hash do documento preenchido
    """
    if not ev.scroll_completo:
        raise ErroAceite("O usuário não rolou o termo até o final")

    if not ev.foto_bytes:
        raise ErroAceite("Foto de aceite ausente")

    if not ev.hash_foto:
        raise ErroAceite("Hash da foto ausente")

    if not ev.versao_termo:
        raise ErroAceite("Versão do termo ausente")

    if not ev.hash_documento:
        raise ErroAceite("Hash do documento ausente")

    # Verifica que o hash da foto bate com o conteúdo
    hash_calculado = hashlib.sha256(ev.foto_bytes).hexdigest()
    if hash_calculado != ev.hash_foto:
        raise ErroAceite("Hash da foto não confere")


def aceite_vigente(
    tipo_termo: TipoTermo,
    versao_atual: str,
    aceites_do_usuario: list,
) -> bool:
    """
    Verifica se o usuário aceitou a versão vigente do termo.

    `aceites_do_usuario` é uma lista de EvidenciaAceite (ou dicts
    com tipo_termo e versao_termo).
    """
    for a in aceites_do_usuario:
        tipo = a.tipo_termo if isinstance(a, EvidenciaAceite) else a.get("tipo_termo")
        versao = a.versao_termo if isinstance(a, EvidenciaAceite) else a.get("versao_termo")
        if tipo == tipo_termo and versao == versao_atual:
            return True
    return False
