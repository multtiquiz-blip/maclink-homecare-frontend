"""
Testes do repositorio de auditoria, contra o esquema.sql real.
Prova que o evento chega ao banco e que nada se apaga.
"""

import pytest

from backend.dados.conexao import em_memoria
from backend.dados.repositorios import auditoria


def test_registrar_devolve_id():
    conn = em_memoria()
    novo = auditoria.registrar(conn, acao="login", detalhe="ok")
    assert novo and novo.startswith("au_")


def test_colunas_casam_com_esquema_real():
    conn = em_memoria()
    auditoria.registrar(
        conn, acao="registrar_dextro", detalhe="sem COREN",
        usuario_id="u1", usuario_nome="Joana", negado=True, ts=1700000000,
    )
    item = auditoria.listar(conn)[0]
    assert item["acao"] == "registrar_dextro"
    assert item["detalhe"] == "sem COREN"
    assert item["usuario_id"] == "u1"
    assert item["usuario_nome"] == "Joana"
    assert item["negado"] is True
    assert item["ts"] == 1700000000


def test_negado_padrao_e_false():
    conn = em_memoria()
    auditoria.registrar(conn, acao="login_com_foto")
    assert auditoria.listar(conn)[0]["negado"] is False


def test_usuario_none_e_permitido():
    """Emergencia e tentativa anonima tambem ficam registradas."""
    conn = em_memoria()
    auditoria.registrar(conn, acao="emergencia_acionada", usuario_id=None)
    item = auditoria.listar(conn)[0]
    assert item["usuario_id"] is None
    assert item["acao"] == "emergencia_acionada"


def test_apenas_negados_filtra():
    conn = em_memoria()
    auditoria.registrar(conn, acao="login", negado=False, ts=1)
    auditoria.registrar(conn, acao="dextro", negado=True, ts=2)
    auditoria.registrar(conn, acao="plano", negado=True, ts=3)
    negados = auditoria.listar(conn, apenas_negados=True)
    assert len(negados) == 2
    assert all(x["negado"] for x in negados)


def test_ordem_do_mais_recente():
    conn = em_memoria()
    auditoria.registrar(conn, acao="antigo", ts=100)
    auditoria.registrar(conn, acao="novo", ts=200)
    assert auditoria.listar(conn)[0]["acao"] == "novo"


def test_mesmo_ts_nao_inverte_ordem_de_insercao():
    conn = em_memoria()
    auditoria.registrar(conn, acao="primeiro", ts=500)
    auditoria.registrar(conn, acao="segundo", ts=500)
    assert auditoria.listar(conn)[0]["acao"] == "segundo"


def test_limite_respeitado():
    conn = em_memoria()
    for i in range(10):
        auditoria.registrar(conn, acao=f"a{i}", ts=i)
    assert len(auditoria.listar(conn, limite=3)) == 3


def test_acumula_e_nao_apaga():
    conn = em_memoria()
    for i in range(50):
        auditoria.registrar(conn, acao="tentativa", ts=i)
    assert len(auditoria.listar(conn, limite=1000)) == 50


def test_ids_unicos():
    conn = em_memoria()
    ids = [auditoria.registrar(conn, acao="x", ts=i) for i in range(30)]
    assert len(set(ids)) == 30


def test_acao_vazia_recusada():
    conn = em_memoria()
    with pytest.raises(ValueError):
        auditoria.registrar(conn, acao="")


def test_modulo_nao_tem_delete_nem_update():
    """Auditoria so recebe INSERT e SELECT. Nada se apaga."""
    assert not hasattr(auditoria, "apagar")
    assert not hasattr(auditoria, "deletar")
    assert not hasattr(auditoria, "limpar")
    assert not hasattr(auditoria, "atualizar")
