"""Testes do aceite eletrônico."""

import hashlib
import pytest
from backend.nucleo.aceites import (
    ErroAceite,
    EvidenciaAceite,
    TipoTermo,
    aceite_vigente,
    validar_evidencia,
)


def _ev(**kwargs):
    foto = b"foto_bytes"
    base = dict(
        usuario_id="u1",
        tipo_termo=TipoTermo.USO,
        versao_termo="v1.0",
        hash_documento="abc123",
        ts=100,
        foto_bytes=foto,
        hash_foto=hashlib.sha256(foto).hexdigest(),
        scroll_completo=True,
    )
    base.update(kwargs)
    return EvidenciaAceite(**base)


def test_aceite_valido_passa():
    validar_evidencia(_ev())  # não levanta


def test_aceite_sem_scroll_falha():
    with pytest.raises(ErroAceite, match="rolou"):
        validar_evidencia(_ev(scroll_completo=False))


def test_aceite_sem_foto_falha():
    with pytest.raises(ErroAceite, match="Foto"):
        validar_evidencia(_ev(foto_bytes=b""))


def test_aceite_hash_errado_falha():
    with pytest.raises(ErroAceite, match="Hash"):
        validar_evidencia(_ev(hash_foto="errado"))


def test_aceite_sem_versao_falha():
    with pytest.raises(ErroAceite, match="Versão"):
        validar_evidencia(_ev(versao_termo=""))


def test_aceite_sem_hash_documento_falha():
    with pytest.raises(ErroAceite, match="Hash do documento"):
        validar_evidencia(_ev(hash_documento=""))


def test_aceite_vigente_quando_versao_bate():
    aceites = [{"tipo_termo": TipoTermo.USO, "versao_termo": "v1.0"}]
    assert aceite_vigente(TipoTermo.USO, "v1.0", aceites)


def test_aceite_nao_vigente_quando_versao_diferente():
    aceites = [{"tipo_termo": TipoTermo.USO, "versao_termo": "v0.9"}]
    assert not aceite_vigente(TipoTermo.USO, "v1.0", aceites)
