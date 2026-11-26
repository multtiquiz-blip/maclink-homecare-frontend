"""Testes das rotas de medidas numéricas."""

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
    # Plano com limites definidos
    planos.criar_ou_atualizar(
        conn,
        idoso_id="e1", perfil="acamada", periodo="24h", pecas=["agua"],
        limites={"sis": 150, "dia": 90, "pulso_max": 100,
                 "spo": 90, "temp_max": 37.5, "temp_min": 35.0,
                 "dexMin": 70, "dexMax": 180},
        autorizacoes={"pressao": True, "oxigenio": True, "temperatura": True},
        liberacoes={}, escada=["u_enf"], espera_min=3,
        definido_por="u_enf",
    )
    app = create_app(conn)
    return TestClient(app), conn


def _login(client, uid, pin):
    return client.post(
        "/auth/login", json={"usuario_id": uid, "pin": pin}
    ).json()["token"]


# ---------------------------------------------------------------------------
# Pressão com pulso (o ponto do Rubemar)
# ---------------------------------------------------------------------------

def test_pressao_normal(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/pressao",
        json={"idoso_id": "e1", "valor": {"sis": 130, "dia": 85, "pulso": 78}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["fora_do_limite"] is False
    assert body["motivos"] == []


def test_pressao_alta_retorna_motivo(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/pressao",
        json={"idoso_id": "e1", "valor": {"sis": 170, "dia": 100, "pulso": 88}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["fora_do_limite"] is True
    assert len(body["motivos"]) == 2
    assert any("170" in m for m in body["motivos"])
    assert any("100" in m for m in body["motivos"])


def test_pulso_alto_retorna_motivo(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/pressao",
        json={"idoso_id": "e1", "valor": {"sis": 130, "dia": 85, "pulso": 120}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["fora_do_limite"] is True
    assert any("Pulso 120" in m for m in body["motivos"])


# ---------------------------------------------------------------------------
# Temperatura com hipotermia
# ---------------------------------------------------------------------------

def test_temperatura_febre(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/temperatura",
        json={"idoso_id": "e1", "valor": {"temp": 38.5}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["fora_do_limite"] is True
    assert any("febre" in m for m in body["motivos"])


def test_temperatura_hipotermia(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/temperatura",
        json={"idoso_id": "e1", "valor": {"temp": 34.2}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["fora_do_limite"] is True
    assert any("hipotermia" in m for m in body["motivos"])


# ---------------------------------------------------------------------------
# Oxigênio
# ---------------------------------------------------------------------------

def test_oxigenio_baixo(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/oxigenio",
        json={"idoso_id": "e1", "valor": {"spo": 87, "pulso": 78}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["fora_do_limite"] is True


# ---------------------------------------------------------------------------
# Dextro — regra dura
# ---------------------------------------------------------------------------

def test_cuidadora_nao_pode_dextro(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/dextro",
        json={"idoso_id": "e1", "valor": {"dextro": 110}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


def test_enfermeiro_verificado_pode_dextro(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.post(
        "/registros/dextro",
        json={"idoso_id": "e1", "valor": {"dextro": 110}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["fora_do_limite"] is False


def test_dextro_hipoglicemia(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.post(
        "/registros/dextro",
        json={"idoso_id": "e1", "valor": {"dextro": 55}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["fora_do_limite"] is True


# ---------------------------------------------------------------------------
# Cuidadora sem autorização no plano
# ---------------------------------------------------------------------------

def test_cuidadora_sem_autorizacao_nao_pode_pressao(setup):
    client, conn = setup
    # Remove autorização
    planos.criar_ou_atualizar(
        conn, idoso_id="e1", perfil="acamada", periodo="24h", pecas=["agua"],
        limites={"sis": 150}, autorizacoes={}, liberacoes={},
        escada=["u_enf"], espera_min=3, definido_por="u_enf",
    )
    token = _login(client, "u_cui", "1234")
    r = client.post(
        "/registros/pressao",
        json={"idoso_id": "e1", "valor": {"sis": 130, "dia": 85}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
