"""
Testes da API: login, sessão, permissões.

Usa TestClient do FastAPI (httpx por baixo) para fazer requisições
reais contra a app em memória. Prova que a matriz de permissões
funciona na prática, não só no teste unitário.
"""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.dados.conexao import em_memoria
from backend.dados.repositorios import usuarios as repo_usuarios


def _criar_app_com_usuario(
    papel="cuidadora",
    verificado=False,
    categoria=None,
):
    """Cria app + usuário com PIN 1234."""
    conn = em_memoria()
    repo_usuarios.criar(
        conn,
        id="u1",
        nome="Joana",
        papel=papel,
        pin="1234",
        categoria=categoria,
        verificado=verificado,
    )
    app = create_app(conn)
    return app, conn


def _login(client, usuario_id="u1", pin="1234"):
    r = client.post(
        "/auth/login",
        json={"usuario_id": usuario_id, "pin": pin},
    )
    return r


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_sucesso():
    app, _ = _criar_app_com_usuario()
    client = TestClient(app)
    r = _login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["token"]
    assert body["usuario_id"] == "u1"
    assert body["nome"] == "Joana"
    assert body["papel"] == "cuidadora"


def test_login_pin_errado():
    app, _ = _criar_app_com_usuario()
    client = TestClient(app)
    r = _login(client, pin="9999")
    assert r.status_code == 401


def test_login_usuario_inexistente():
    app, _ = _criar_app_com_usuario()
    client = TestClient(app)
    r = _login(client, usuario_id="u_inexistente")
    assert r.status_code == 401


def test_login_pin_com_formato_invalido_falha():
    """PIN com 3 dígitos nunca chega a ser criado (usuarios.criar valida)."""
    conn = em_memoria()
    with pytest.raises(ValueError):
        repo_usuarios.criar(
            conn, id="u1", nome="Joana", papel="cuidadora", pin="123",
        )


# ---------------------------------------------------------------------------
# Sessão e /me
# ---------------------------------------------------------------------------

def test_me_sem_token_retorna_401():
    app, _ = _criar_app_com_usuario()
    client = TestClient(app)
    r = client.get("/me")
    assert r.status_code == 401


def test_me_com_token_retorna_usuario():
    app, _ = _criar_app_com_usuario()
    client = TestClient(app)
    token = _login(client).json()["token"]
    r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "u1"
    assert body["papel"] == "cuidadora"
    assert body["verificado"] is False


def test_logout_invalida_token():
    app, _ = _criar_app_com_usuario()
    client = TestClient(app)
    token = _login(client).json()["token"]
    r = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    # Agora /me deve falhar
    r2 = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 401


# ---------------------------------------------------------------------------
# Permissões na prática
# ---------------------------------------------------------------------------

def test_agua_permitida_para_cuidadora():
    app, _ = _criar_app_com_usuario(papel="cuidadora")
    client = TestClient(app)
    token = _login(client).json()["token"]
    r = client.post("/registrar/agua", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_dextro_negado_para_cuidadora():
    app, _ = _criar_app_com_usuario(papel="cuidadora")
    client = TestClient(app)
    token = _login(client).json()["token"]
    r = client.post("/registrar/dextro", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_dextro_negado_para_tecnico_verificado():
    app, _ = _criar_app_com_usuario(
        papel="tecnico", verificado=True, categoria="tecnico",
    )
    client = TestClient(app)
    token = _login(client).json()["token"]
    r = client.post("/registrar/dextro", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_dextro_permitido_para_enfermeiro_verificado():
    app, _ = _criar_app_com_usuario(
        papel="enfermeiro", verificado=True, categoria="enfermeiro",
    )
    client = TestClient(app)
    token = _login(client).json()["token"]
    r = client.post("/registrar/dextro", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_dextro_negado_para_enfermeiro_nao_verificado():
    app, _ = _criar_app_com_usuario(
        papel="enfermeiro", verificado=False, categoria="enfermeiro",
    )
    client = TestClient(app)
    token = _login(client).json()["token"]
    r = client.post("/registrar/dextro", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_editar_plano_negado_para_cuidadora():
    app, _ = _criar_app_com_usuario(papel="cuidadora")
    client = TestClient(app)
    token = _login(client).json()["token"]
    r = client.post("/editar/plano", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_editar_plano_permitido_para_enfermeiro_verificado():
    app, _ = _criar_app_com_usuario(
        papel="enfermeiro", verificado=True, categoria="enfermeiro",
    )
    client = TestClient(app)
    token = _login(client).json()["token"]
    r = client.post("/editar/plano", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
