"""Testes do painel com alerta real (usa limites do plano)."""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.dados.conexao import em_memoria
from backend.dados.repositorios import idosos, planos, usuarios, vinculos


@pytest.fixture
def setup():
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
    planos.criar_ou_atualizar(
        conn, idoso_id="e1", perfil="acamada", periodo="24h", pecas=["agua"],
        limites={"sis": 150, "dia": 90, "spo": 90, "temp_max": 37.5,
                 "temp_min": 35.0, "pulso_max": 100},
        autorizacoes={"pressao": True, "oxigenio": True, "temperatura": True},
        liberacoes={}, escada=["u_enf"], espera_min=3,
        definido_por="u_enf",
    )
    app = create_app(conn)
    return TestClient(app)


def _login(client, uid, pin):
    return client.post(
        "/auth/login", json={"usuario_id": uid, "pin": pin}
    ).json()["token"]


def _paciente(client, token):
    r = client.get("/painel", headers={"Authorization": f"Bearer {token}"})
    return r.json()["pacientes"][0]


def test_paciente_sem_registro_em_dia(setup):
    client = setup
    token = _login(client, "u_cui", "1234")
    p = _paciente(client, token)
    assert p["estado"] == "em_dia"


def test_pressao_alta_vira_alerta_no_painel(setup):
    client = setup
    token = _login(client, "u_cui", "1234")
    client.post(
        "/registros/pressao",
        json={"idoso_id": "e1", "valor": {"sis": 170, "dia": 100}},
        headers={"Authorization": f"Bearer {token}"},
    )
    p = _paciente(client, token)
    assert p["estado"] == "alerta"
    assert p["tem_alerta_critico"] is True
    assert "170" in p["frase"]


def test_hipotermia_vira_alerta_no_painel(setup):
    client = setup
    token = _login(client, "u_cui", "1234")
    client.post(
        "/registros/temperatura",
        json={"idoso_id": "e1", "valor": {"temp": 34.5}},
        headers={"Authorization": f"Bearer {token}"},
    )
    p = _paciente(client, token)
    assert p["estado"] == "alerta"
    assert "hipotermia" in p["frase"].lower()


def test_oxigenio_baixo_vira_alerta(setup):
    client = setup
    token = _login(client, "u_cui", "1234")
    client.post(
        "/registros/oxigenio",
        json={"idoso_id": "e1", "valor": {"spo": 85}},
        headers={"Authorization": f"Bearer {token}"},
    )
    p = _paciente(client, token)
    assert p["estado"] == "alerta"


def test_pressao_normal_nao_vira_alerta(setup):
    client = setup
    token = _login(client, "u_cui", "1234")
    client.post(
        "/registros/pressao",
        json={"idoso_id": "e1", "valor": {"sis": 130, "dia": 85}},
        headers={"Authorization": f"Bearer {token}"},
    )
    p = _paciente(client, token)
    assert p["estado"] == "em_dia"
    assert p["tem_alerta_critico"] is False
