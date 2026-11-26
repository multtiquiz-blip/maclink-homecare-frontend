"""Testes do endpoint do painel."""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.dados.conexao import em_memoria
from backend.dados.repositorios import idosos, usuarios, vinculos


@pytest.fixture
def setup():
    conn = em_memoria()
    usuarios.criar(conn, id="u_cui", nome="Joana", papel="cuidadora", pin="1234")
    usuarios.criar(conn, id="u_out", nome="Outro", papel="cuidadora", pin="9999")
    idosos.criar(conn, id="e1", nome="Dona Maria")
    idosos.criar(conn, id="e2", nome="Seu Valdo")
    vinculos.criar(conn, id="v1", usuario_id="u_cui", paciente_id="e1",
                   papel="cuidadora", vinculado_por="u_cui")
    vinculos.criar(conn, id="v2", usuario_id="u_cui", paciente_id="e2",
                   papel="cuidadora", vinculado_por="u_cui")
    # u_out não tem vínculo com ninguém
    app = create_app(conn)
    client = TestClient(app)
    return client, conn


def _login(client, uid, pin):
    return client.post(
        "/auth/login", json={"usuario_id": uid, "pin": pin}
    ).json()["token"]


def test_painel_vazio_para_usuario_sem_vinculo(setup):
    client, _ = setup
    token = _login(client, "u_out", "9999")
    r = client.get("/painel", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_painel_lista_pacientes_do_usuario(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.get("/painel", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    nomes = {p["nome"] for p in body["pacientes"]}
    assert nomes == {"Dona Maria", "Seu Valdo"}


def test_paciente_sem_registro_aparece_em_dia(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.get("/painel", headers={"Authorization": f"Bearer {token}"})
    for p in r.json()["pacientes"]:
        assert p["estado"] == "em_dia"


def test_paciente_com_registro_mostra_ultima_acao(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    client.post(
        "/registros/agua",
        json={"idoso_id": "e1", "texto": "Bebeu água"},
        headers={"Authorization": f"Bearer {token}"},
    )
    r = client.get("/painel", headers={"Authorization": f"Bearer {token}"})
    body = r.json()
    dona = next(p for p in body["pacientes"] if p["idoso_id"] == "e1")
    assert dona["ultima_acao_texto"] == "Bebeu água"


def test_painel_sem_token_da_401(setup):
    client, _ = setup
    r = client.get("/painel")
    assert r.status_code == 401
