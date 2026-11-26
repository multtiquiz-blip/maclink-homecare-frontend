"""Testes das rotas de registro (gravam de verdade no SQLite)."""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.dados.conexao import em_memoria
from backend.dados.repositorios import idosos, usuarios, vinculos
from backend.nucleo.tarefas import dia_de_cuidado
import time


@pytest.fixture
def setup():
    """App + idoso + vínculos cuidadora e enfermeiro."""
    conn = em_memoria()
    usuarios.criar(conn, id="u_cui", nome="Joana", papel="cuidadora", pin="1234")
    usuarios.criar(
        conn, id="u_enf", nome="Carla", papel="enfermeiro", pin="4567",
        categoria="enfermeiro", coren="COREN-MG-238295-ENF", verificado=True,
    )
    idosos.criar(conn, id="e1", nome="Dona Maria")
    vinculos.criar(conn, id="v1", usuario_id="u_cui", paciente_id="e1",
                   papel="cuidadora", vinculado_por="u_cui")
    vinculos.criar(conn, id="v2", usuario_id="u_enf", paciente_id="e1",
                   papel="enfermeiro", vinculado_por="u_enf")
    app = create_app(conn)
    client = TestClient(app)
    return client, conn


def _login(client, uid, pin):
    r = client.post("/auth/login", json={"usuario_id": uid, "pin": pin})
    return r.json()["token"]


def test_registrar_agua_grava_no_banco(setup):
    client, conn = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/agua",
        json={"idoso_id": "e1", "texto": "Bebeu água"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["tipo"] == "agua"
    assert body["dia"] == dia_de_cuidado(int(time.time()))

    # Confirma que gravou no banco
    row = conn.execute("SELECT * FROM registros WHERE id = ?", (body["id"],)).fetchone()
    assert row is not None
    assert row["texto"] == "Bebeu água"
    assert row["autor_nome"] == "Joana"
    assert row["autor_papel"] == "cuidadora"


def test_registrar_dor_grava_valor(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/dor",
        json={"idoso_id": "e1", "texto": "Dor no joelho", "valor": "7"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["tipo"] == "dor"


def test_registrar_queda(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/queda",
        json={"idoso_id": "e1", "texto": "Escorregou no banheiro"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["tipo"] == "queda"


def test_registrar_sem_vinculo_da_403(setup):
    client, conn = setup
    idosos.criar(conn, id="e2", nome="Outro idoso")  # sem vínculo
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/agua",
        json={"idoso_id": "e2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


def test_registrar_sem_token_da_401(setup):
    client, _ = setup
    r = client.post("/registros/agua", json={"idoso_id": "e1"})
    assert r.status_code == 401


def test_cuidadora_nao_pode_dextro(setup):
    """A rota /registrar/dextro (em main.py) exige permissão dura."""
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registrar/dextro",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


def test_enfermeiro_verificado_pode_dextro(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.post(
        "/registrar/dextro",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200


def test_listar_registros_do_dia(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    # Grava dois
    client.post("/registros/agua", json={"idoso_id": "e1", "texto": "A"},
                headers={"Authorization": f"Bearer {token}"})
    client.post("/registros/dor", json={"idoso_id": "e1", "texto": "B"},
                headers={"Authorization": f"Bearer {token}"})
    # Lista
    r = client.get("/registros/e1/dia", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert len(r.json()["registros"]) == 2
