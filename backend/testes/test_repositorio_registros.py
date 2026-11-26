"""Testes do repositório de registros."""

import pytest
from backend.dados.conexao import em_memoria
from backend.dados.repositorios import registros, usuarios


@pytest.fixture
def conn():
    c = em_memoria()
    # cria o idoso mínimo
    c.execute(
        "INSERT INTO idosos (id, nome, criado_em) VALUES (?, ?, ?)",
        ("e1", "Dona Maria", 0),
    )
    # cria usuário autor
    usuarios.criar(c, id="u1", nome="Joana", papel="cuidadora", pin="1234")
    c.commit()
    yield c
    c.close()


def test_criar_registro(conn):
    r = registros.criar(
        conn, id="r1", idoso_id="e1", dia="2026-11-21", tipo="agua",
        autor_id="u1", autor_nome="Joana", autor_papel="cuidadora",
        texto="Bebeu água",
    )
    assert r == "r1"
    buscado = registros.buscar(conn, "r1")
    assert buscado.texto == "Bebeu água"
    assert buscado.corrigido is False


def test_listar_por_dia(conn):
    for i in range(3):
        registros.criar(
            conn, id=f"r{i}", idoso_id="e1", dia="2026-11-21", tipo="agua",
            autor_id="u1", autor_nome="Joana", autor_papel="cuidadora",
            texto=f"Reg {i}",
        )
    registros.criar(
        conn, id="r_outro", idoso_id="e1", dia="2026-11-22", tipo="agua",
        autor_id="u1", autor_nome="Joana", autor_papel="cuidadora",
        texto="Outro dia",
    )

    lista = registros.listar_por_dia(conn, "e1", "2026-11-21")
    assert len(lista) == 3
    assert all(r.dia == "2026-11-21" for r in lista)


def test_corrigir_registro_guarda_historico(conn):
    registros.criar(
        conn, id="r1", idoso_id="e1", dia="2026-11-21", tipo="pressao",
        autor_id="u1", autor_nome="Joana", autor_papel="cuidadora",
        texto="Pressão", valor="120/80",
    )

    registros.corrigir(
        conn,
        registro_id="r1",
        motivo="Valor digitado errado; aferido novamente",
        autor_id="u1",
        autor_nome="Joana",
        novo_valor="130/85",
    )

    r = registros.buscar(conn, "r1")
    assert r.corrigido is True
    assert r.valor == "130/85"

    hist = conn.execute(
        "SELECT * FROM registros_historico WHERE registro_id = 'r1'"
    ).fetchall()
    assert len(hist) == 1
    assert hist[0]["antes_valor"] == "120/80"
    assert hist[0]["motivo"].startswith("Valor digitado")


def test_corrigir_sem_motivo_levanta_erro(conn):
    registros.criar(
        conn, id="r1", idoso_id="e1", dia="2026-11-21", tipo="agua",
        autor_id="u1", autor_nome="Joana", autor_papel="cuidadora",
    )
    with pytest.raises(ValueError, match="Motivo"):
        registros.corrigir(
            conn, registro_id="r1", motivo="", autor_id="u1", autor_nome="Joana",
        )


def test_corrigir_registro_inexistente_levanta_erro(conn):
    with pytest.raises(ValueError, match="não encontrado"):
        registros.corrigir(
            conn, registro_id="r_inexistente", motivo="teste",
            autor_id="u1", autor_nome="Joana",
        )


def test_excluir_nunca_nao_permite_exclusao(conn):
    """A função existe só para provar que exclusão não é possível."""
    with pytest.raises(NotImplementedError, match="não se apagam"):
        registros.excluir_nunca(conn, "r1")
