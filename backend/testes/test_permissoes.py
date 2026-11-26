"""
Testes da matriz de permissões.
Estes testes são a garantia de que dextro só passa com enfermeiro verificado.
Se um deles falhar, o build quebra.
"""

import pytest
from backend.nucleo.permissoes import Acao, Papel, Plano, Usuario, pode


def _plano(**kwargs):
    """Plano com liberações e autorizações vazias por padrão."""
    liberacoes = kwargs.pop("liberacoes", {})
    autorizacoes = kwargs.pop("autorizacoes", {})
    return Plano(idoso_id="e1", liberacoes=liberacoes, autorizacoes=autorizacoes)


# ---------------------------------------------------------------------------
# DEXTRO — regra dura: só enfermeiro verificado
# ---------------------------------------------------------------------------

def test_dextro_negado_para_cuidadora():
    u = Usuario(id="u1", papel=Papel.CUIDADORA)
    assert not pode(Acao.REGISTRAR_DEXTRO, u, _plano())


def test_dextro_negado_para_tecnico_verificado():
    u = Usuario(id="u2", papel=Papel.TECNICO, categoria="tecnico", verificado=True)
    assert not pode(Acao.REGISTRAR_DEXTRO, u, _plano())


def test_dextro_negado_para_auxiliar_verificado():
    u = Usuario(id="u3", papel=Papel.AUXILIAR, categoria="auxiliar", verificado=True)
    assert not pode(Acao.REGISTRAR_DEXTRO, u, _plano())


def test_dextro_negado_para_enfermeiro_nao_verificado():
    u = Usuario(id="u4", papel=Papel.ENFERMEIRO, categoria="enfermeiro", verificado=False)
    assert not pode(Acao.REGISTRAR_DEXTRO, u, _plano())


def test_dextro_permitido_somente_enfermeiro_verificado():
    u = Usuario(id="u5", papel=Papel.ENFERMEIRO, categoria="enfermeiro", verificado=True)
    assert pode(Acao.REGISTRAR_DEXTRO, u, _plano())


# ---------------------------------------------------------------------------
# PRESSÃO / OXIGÊNIO / TEMPERATURA
# ---------------------------------------------------------------------------

def test_pressao_negada_para_cuidadora_sem_autorizacao():
    u = Usuario(id="u1", papel=Papel.CUIDADORA)
    assert not pode(Acao.REGISTRAR_PRESSAO, u, _plano())


def test_pressao_permitida_para_cuidadora_com_autorizacao_no_plano():
    u = Usuario(id="u1", papel=Papel.CUIDADORA)
    p = _plano(autorizacoes={"pressao": True})
    assert pode(Acao.REGISTRAR_PRESSAO, u, p)


def test_pressao_negada_para_tecnico_nao_verificado():
    u = Usuario(id="u2", papel=Papel.TECNICO, categoria="tecnico", verificado=False)
    assert not pode(Acao.REGISTRAR_PRESSAO, u, _plano())


def test_pressao_permitida_para_tecnico_verificado():
    u = Usuario(id="u2", papel=Papel.TECNICO, categoria="tecnico", verificado=True)
    assert pode(Acao.REGISTRAR_PRESSAO, u, _plano())


# ---------------------------------------------------------------------------
# CONTROLADOS — cuidadora só com liberação no plano
# ---------------------------------------------------------------------------

def test_remedio_negado_para_cuidadora_sem_liberacao():
    u = Usuario(id="u1", papel=Papel.CUIDADORA)
    assert not pode(Acao.REGISTRAR_REMEDIO, u, _plano())


def test_remedio_permitido_para_cuidadora_com_liberacao():
    u = Usuario(id="u1", papel=Papel.CUIDADORA)
    p = _plano(liberacoes={"registrar_remedio": True})
    assert pode(Acao.REGISTRAR_REMEDIO, u, p)


def test_remedio_permitido_para_enfermeiro_verificado():
    u = Usuario(id="u5", papel=Papel.ENFERMEIRO, categoria="enfermeiro", verificado=True)
    assert pode(Acao.REGISTRAR_REMEDIO, u, _plano())


# ---------------------------------------------------------------------------
# PLANO / LIMITES — só enfermeiro verificado
# ---------------------------------------------------------------------------

def test_editar_plano_negado_para_cuidadora():
    u = Usuario(id="u1", papel=Papel.CUIDADORA)
    assert not pode(Acao.EDITAR_PLANO, u, _plano())


def test_editar_plano_negado_para_enfermeiro_nao_verificado():
    u = Usuario(id="u4", papel=Papel.ENFERMEIRO, categoria="enfermeiro", verificado=False)
    assert not pode(Acao.EDITAR_PLANO, u, _plano())


def test_editar_plano_permitido_para_enfermeiro_verificado():
    u = Usuario(id="u5", papel=Papel.ENFERMEIRO, categoria="enfermeiro", verificado=True)
    assert pode(Acao.EDITAR_PLANO, u, _plano())


# ---------------------------------------------------------------------------
# REGISTRO COMUM — todos podem
# ---------------------------------------------------------------------------

def test_agua_permitida_para_cuidadora():
    u = Usuario(id="u1", papel=Papel.CUIDADORA)
    assert pode(Acao.REGISTRAR_AGUA, u, _plano())


def test_dor_permitida_para_familia():
    u = Usuario(id="u6", papel=Papel.FAMILIA)
    assert pode(Acao.REGISTRAR_DOR, u, _plano())


# ---------------------------------------------------------------------------
# SEM IDENTIFICAÇÃO — usuário None nunca passa por aqui
# ---------------------------------------------------------------------------

def test_usuario_none_negado_em_qualquer_acao():
    assert not pode(Acao.REGISTRAR_AGUA, None, _plano())
    assert not pode(Acao.REGISTRAR_DEXTRO, None, _plano())
