"""Testes do repositório de planos."""

import pytest

from backend.dados.conexao import em_memoria
from backend.dados.repositorios import idosos, planos, usuarios


@pytest.fixture
def conn():
    c = em_memoria()
    idosos.criar(c, id="e1", nome="Dona Maria")
    usuarios.criar(
        c, id="u_enf", nome="Carla", papel="enfermeiro", pin="4567",
        categoria="enfermeiro", coren="COREN-MG-238295-ENF", verificado=True,
    )
    yield c
    c.close()


def _criar_plano(conn, **over):
    kwargs = dict(
        idoso_id="e1",
        perfil="acamada",
        periodo="24h",
        pecas=["agua", "comida", "fralda"],
        limites={},
        autorizacoes={},
        liberacoes={},
        escada=["u_enf"],
        espera_min=3,
        definido_por="u_enf",
    )
    kwargs.update(over)
    return planos.criar_ou_atualizar(conn, **kwargs)


def test_criar_plano_v1(conn):
    plano_id = _criar_plano(conn)
    assert plano_id.startswith("pl_")
    p = planos.buscar_por_idoso(conn, "e1")
    assert p is not None
    assert p.versao == 1
    assert p.perfil == "acamada"
    assert p.pecas == ["agua", "comida", "fralda"]


def test_atualizar_incrementa_versao(conn):
    _criar_plano(conn)
    _criar_plano(conn, perfil="demencia")
    p = planos.buscar_por_idoso(conn, "e1")
    assert p.versao == 2
    assert p.perfil == "demencia"


def test_plano_comeca_sem_numeros_clinicos(conn):
    """Regra dura: nenhum número clínico no código."""
    _criar_plano(conn, limites={})
    p = planos.buscar_por_idoso(conn, "e1")
    assert p.limites == {}


def test_plano_com_limites_do_enfermeiro(conn):
    """Se o enfermeiro definiu, o sistema guarda como veio."""
    _criar_plano(conn, limites={"sis": 150, "dia": 90})
    p = planos.buscar_por_idoso(conn, "e1")
    assert p.limites["sis"] == 150
    assert p.limites["dia"] == 90


def test_buscar_plano_inexistente_retorna_none(conn):
    assert planos.buscar_por_idoso(conn, "e_sem_plano") is None


def test_autorizacoes_e_liberacoes_persistem(conn):
    _criar_plano(
        conn,
        autorizacoes={"pressao": True, "oxigenio": False},
        liberacoes={"registrar_remedio": True},
    )
    p = planos.buscar_por_idoso(conn, "e1")
    assert p.autorizacoes["pressao"] is True
    assert p.autorizacoes["oxigenio"] is False
    assert p.liberacoes["registrar_remedio"] is True
