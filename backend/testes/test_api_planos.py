"""Testes das rotas do plano de cuidado."""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.dados.conexao import em_memoria
from backend.dados.repositorios import idosos, usuarios, vinculos


@pytest.fixture
def setup():
    conn = em_memoria()
    usuarios.criar(conn, id="u_cui", nome="Joana", papel="cuidadora", pin="1234")
    usuarios.criar(
        conn, id="u_enf", nome="Carla", papel="enfermeiro", pin="4567",
        categoria="enfermeiro", coren="COREN-MG-238295-ENF", verificado=True,
    )
    usuarios.criar(
        conn, id="u_enf_nv", nome="Paulo", papel="enfermeiro", pin="8888",
        categoria="enfermeiro", coren="COREN-MG-999999-ENF", verificado=False,
    )
    idosos.criar(conn, id="e1", nome="Dona Maria")
    idosos.criar(conn, id="e2", nome="Outro paciente")
    vinculos.criar(conn, id="v1", usuario_id="u_cui", paciente_id="e1",
                   papel="cuidadora", vinculado_por="u_cui")
    vinculos.criar(conn, id="v2", usuario_id="u_enf", paciente_id="e1",
                   papel="enfermeiro", vinculado_por="u_enf")
    # u_enf_nv tem vínculo com e1 mas NÃO é verificado
    vinculos.criar(conn, id="v3", usuario_id="u_enf_nv", paciente_id="e1",
                   papel="enfermeiro", vinculado_por="u_enf_nv")
    # u_enf NÃO tem vínculo com e2
    app = create_app(conn)
    client = TestClient(app)
    return client, conn


def _login(client, uid, pin):
    return client.post(
        "/auth/login", json={"usuario_id": uid, "pin": pin}
    ).json()["token"]


def _plano_payload(idoso_id="e1", **over):
    base = {
        "idoso_id": idoso_id,
        "perfil": "acamada",
        "periodo": "24h",
        "pecas": ["agua", "comida", "fralda"],
        "limites": {},
        "autorizacoes": {},
        "liberacoes": {},
        "escada": ["u_cui"],
        "espera_min": 3,
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# Criar plano — permissões
# ---------------------------------------------------------------------------

def test_enfermeiro_verificado_cria_plano(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.post("/planos", json=_plano_payload(),
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_cuidadora_nao_cria_plano(setup):
    client, _ = setup
    token = _login(client, "u_cui", "1234")
    r = client.post("/planos", json=_plano_payload(),
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_enfermeiro_nao_verificado_nao_cria_plano(setup):
    client, _ = setup
    token = _login(client, "u_enf_nv", "8888")
    r = client.post("/planos", json=_plano_payload(),
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_enfermeiro_sem_vinculo_nao_cria_plano(setup):
    """u_enf não tem vínculo com e2."""
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.post("/planos", json=_plano_payload(idoso_id="e2"),
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Validações de conteúdo
# ---------------------------------------------------------------------------

def test_perfil_invalido(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.post("/planos", json=_plano_payload(perfil="xpto"),
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400


def test_periodo_invalido(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.post("/planos", json=_plano_payload(periodo="madrugada_inteira"),
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400


def test_peca_invalida(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.post("/planos", json=_plano_payload(pecas=["agua", "voar"]),
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 400


def test_espera_min_menor_que_1(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.post("/planos", json=_plano_payload(espera_min=0),
                    headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 422  # validação Pydantic


# ---------------------------------------------------------------------------
# Regra dura: sem número clínico
# ---------------------------------------------------------------------------

def test_plano_sem_limites_nao_gera_numero_clinico(setup):
    """Se o enfermeiro não definiu, o sistema não inventa."""
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    client.post("/planos", json=_plano_payload(limites={}),
                headers={"Authorization": f"Bearer {token}"})
    r = client.get("/planos/e1", headers={"Authorization": f"Bearer {token}"})
    assert r.json()["limites"] == {}


# ---------------------------------------------------------------------------
# GET e versão
# ---------------------------------------------------------------------------

def test_get_plano_apos_criar(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    client.post("/planos", json=_plano_payload(),
                headers={"Authorization": f"Bearer {token}"})
    r = client.get("/planos/e1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["perfil"] == "acamada"
    assert body["versao"] == 1


def test_get_plano_inexistente(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.get("/planos/e1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


def test_get_plano_sem_vinculo_403(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    r = client.get("/planos/e2", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_atualizar_plano_incrementa_versao(setup):
    client, _ = setup
    token = _login(client, "u_enf", "4567")
    client.post("/planos", json=_plano_payload(),
                headers={"Authorization": f"Bearer {token}"})
    client.post("/planos", json=_plano_payload(perfil="demencia"),
                headers={"Authorization": f"Bearer {token}"})
    r = client.get("/planos/e1", headers={"Authorization": f"Bearer {token}"})
    body = r.json()
    assert body["versao"] == 2
    assert body["perfil"] == "demencia"


# ---------------------------------------------------------------------------
# Sem token
# ---------------------------------------------------------------------------

def test_post_sem_token_401(setup):
    client, _ = setup
    r = client.post("/planos", json=_plano_payload())
    assert r.status_code == 401
