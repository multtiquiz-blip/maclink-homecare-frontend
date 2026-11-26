"""Testes da verificação de credenciais."""

import pytest
from backend.nucleo.verificacao_credenciais import (
    CategoriaEnfermagem,
    CertificadoCuidador,
    StatusCoren,
    certificado_valido,
    parse_coren,
    permissoes_do_certificado,
    verificar_coren,
)


# ---------------------------------------------------------------------------
# parse_coren — formato
# ---------------------------------------------------------------------------

def test_parse_coren_valido_enfermeiro():
    r = parse_coren("COREN-MG-238295-ENF")
    assert r is not None
    assert r["uf"] == "MG"
    assert r["numero"] == "238295"
    assert r["categoria"] == CategoriaEnfermagem.ENFERMEIRO


def test_parse_coren_valido_tecnico():
    r = parse_coren("COREN-SP-123456-TE")
    assert r["categoria"] == CategoriaEnfermagem.TECNICO


def test_parse_coren_valido_auxiliar():
    r = parse_coren("COREN-RJ-999999-AE")
    assert r["categoria"] == CategoriaEnfermagem.AUXILIAR


def test_parse_coren_invalido_sem_prefixo():
    assert parse_coren("MG-238295-ENF") is None


def test_parse_coren_invalido_categoria():
    assert parse_coren("COREN-MG-238295-XX") is None


def test_parse_coren_invalido_numero():
    assert parse_coren("COREN-MG-ABC123-ENF") is None


def test_parse_coren_vazio():
    assert parse_coren("") is None


# ---------------------------------------------------------------------------
# verificar_coren — fluxo
# ---------------------------------------------------------------------------

def test_verificar_coren_formato_invalido():
    r = verificar_coren("invalido")
    assert r.status == StatusCoren.INVALIDO


def test_verificar_coren_sem_consulta_retorna_pendente():
    """No piloto, sem consulta automática, o COREN fica pendente."""
    r = verificar_coren("COREN-MG-238295-ENF", consulta_fn=None)
    assert r.status == StatusCoren.PENDENTE
    assert r.categoria == CategoriaEnfermagem.ENFERMEIRO


def test_verificar_coren_com_consulta_ativa():
    def consulta(coren):
        return {"status": "ativo", "nome": "Carla Lima", "proxima_verificacao_em": 999}

    r = verificar_coren("COREN-MG-238295-ENF", consulta_fn=consulta)
    assert r.status == StatusCoren.ATIVO
    assert r.nome == "Carla Lima"


def test_verificar_coren_com_consulta_suspensa():
    def consulta(coren):
        return {"status": "suspenso", "nome": "Carla Lima"}

    r = verificar_coren("COREN-MG-238295-ENF", consulta_fn=consulta)
    assert r.status == StatusCoren.SUSPENSO


def test_verificar_coren_consulta_com_erro_cai_para_pendente():
    def consulta(coren):
        raise ConnectionError("sem internet")

    r = verificar_coren("COREN-MG-238295-ENF", consulta_fn=consulta)
    assert r.status == StatusCoren.PENDENTE


# ---------------------------------------------------------------------------
# Certificado do cuidador
# ---------------------------------------------------------------------------

def _cert(**kwargs):
    base = dict(
        nome="Joana", cpf="000", instituicao="X", curso="Aferição",
        carga_horaria=8, data_emissao=100, data_validade=200,
        codigo_autenticidade=None,
        cobre_pressao=True, cobre_oximetria=False, cobre_glicemia=False,
    )
    base.update(kwargs)
    return CertificadoCuidador(**base)


def test_certificado_valido_dentro_do_prazo():
    assert certificado_valido(_cert(data_validade=200), agora=150)


def test_certificado_vencido():
    assert not certificado_valido(_cert(data_validade=200), agora=250)


def test_certificado_sem_validade_e_valido_ate_ser_substituido():
    assert certificado_valido(_cert(data_validade=None), agora=999999)


def test_permissoes_do_certificado_so_libera_o_que_cobre():
    perms = permissoes_do_certificado(_cert(), agora=150)
    assert perms["pressao"] is True
    assert perms["oximetria"] is False
    assert perms["glicemia"] is False


def test_certificado_nunca_libera_dextro():
    perms = permissoes_do_certificado(_cert(), agora=150)
    assert perms["dextro"] is False


def test_certificado_vencido_nao_libera_nada():
    perms = permissoes_do_certificado(_cert(data_validade=200), agora=250)
    assert perms["pressao"] is False
    assert perms["oximetria"] is False
    assert perms["glicemia"] is False
