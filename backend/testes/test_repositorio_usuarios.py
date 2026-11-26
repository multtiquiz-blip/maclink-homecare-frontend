"""Testes do repositório de usuários (banco em memória)."""

import pytest
from backend.dados.conexao import em_memoria
from backend.dados.repositorios import usuarios


@pytest.fixture
def conn():
    c = em_memoria()
    yield c
    c.close()


def test_criar_e_buscar_usuario(conn):
    usuarios.criar(
        conn,
        id="u1", nome="Joana", papel="cuidadora", pin="1234",
    )
    u = usuarios.buscar(conn, "u1")
    assert u is not None
    assert u.nome == "Joana"
    assert u.papel == "cuidadora"
    assert u.ativo is True


def test_pin_nao_e_guardado_em_texto_puro(conn):
    usuarios.criar(conn, id="u1", nome="Joana", papel="cuidadora", pin="1234")
    row = conn.execute("SELECT pin_hash, pin_salt FROM usuarios WHERE id = 'u1'").fetchone()
    assert row["pin_hash"] != "1234"
    assert "1234" not in row["pin_hash"]
    assert row["pin_salt"] != "1234"


def test_pin_invalido_levanta_erro(conn):
    with pytest.raises(ValueError):
        usuarios.criar(conn, id="u1", nome="X", papel="cuidadora", pin="123")


def test_autenticar_com_pin_correto(conn):
    usuarios.criar(conn, id="u1", nome="Joana", papel="cuidadora", pin="1234")
    assert usuarios.autenticar(conn, "u1", "1234")


def test_autenticar_com_pin_errado(conn):
    usuarios.criar(conn, id="u1", nome="Joana", papel="cuidadora", pin="1234")
    assert not usuarios.autenticar(conn, "u1", "9999")


def test_autenticar_usuario_inexistente(conn):
    assert not usuarios.autenticar(conn, "u_inexistente", "1234")


def test_buscar_usuario_inexistente_retorna_none(conn):
    assert usuarios.buscar(conn, "u_inexistente") is None


def test_criar_enfermeiro_com_coren(conn):
    usuarios.criar(
        conn,
        id="u5", nome="Carla", papel="enfermeiro", pin="4567",
        categoria="enfermeiro", coren="COREN-MG-238295-ENF", verificado=True,
    )
    u = usuarios.buscar(conn, "u5")
    assert u.coren == "COREN-MG-238295-ENF"
    assert u.verificado is True
