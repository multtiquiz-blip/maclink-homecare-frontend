"""
Testes da politica de login com rosto obrigatorio.
Cada teste protege uma decisao do proprietario. Se um falhar, o build quebra.
"""

import hashlib

import pytest

from backend.nucleo.autenticacao import (
    EtapaLogin,
    acesso_emergencia,
    classificar_falha_camera,
    decidir_login,
    foto_evidencia_valida,
)

FOTO = hashlib.sha256(b"imagem-ficticia-de-teste").hexdigest()


# --- PIN -------------------------------------------------------------------

def test_pin_errado_nunca_autentica_mesmo_com_foto():
    r = decidir_login(pin_ok=False, exigir_foto=True, foto_confirmada=True)
    assert r.etapa is EtapaLogin.NEGADO
    assert r.emite_sessao is False
    assert r.libera_dados is False


def test_pin_errado_nao_revela_se_usuario_existe():
    r = decidir_login(pin_ok=False, exigir_foto=True)
    assert "usuario" not in r.motivo.lower() or "ou" in r.motivo.lower()
    assert r.motivo == "Usuario ou PIN invalido"


# --- foto obrigatoria ------------------------------------------------------

def test_politica_ativa_sem_foto_bloqueia():
    r = decidir_login(pin_ok=True, exigir_foto=True, foto_confirmada=False)
    assert r.etapa is EtapaLogin.FOTO_OBRIGATORIA
    assert r.emite_sessao is False
    assert r.libera_dados is False
    assert r.motivo


def test_politica_ativa_com_foto_autentica():
    r = decidir_login(pin_ok=True, exigir_foto=True, foto_confirmada=True)
    assert r.etapa is EtapaLogin.AUTENTICADO
    assert r.emite_sessao is True
    assert r.libera_dados is True


def test_foto_nao_compra_autenticacao_sem_pin():
    assert decidir_login(pin_ok=False, exigir_foto=True, foto_confirmada=True).libera_dados is False


def test_politica_desligada_preserva_legado():
    r = decidir_login(pin_ok=True, exigir_foto=False, foto_confirmada=False)
    assert r.etapa is EtapaLogin.AUTENTICADO


def test_resultado_e_imutavel():
    r = decidir_login(pin_ok=True, exigir_foto=True, foto_confirmada=True)
    with pytest.raises(Exception):
        r.etapa = EtapaLogin.NEGADO


# --- evidencia de foto -----------------------------------------------------

@pytest.mark.parametrize("valor", [
    "", None, "pulado", "sem_foto", "sem foto", "null", "0",
    "0" * 63, "0" * 65, "z" * 64, "g" * 64, "1234", "true", " ",
])
def test_evidencia_invalida_recusada(valor):
    assert foto_evidencia_valida(valor) is False


def test_evidencia_valida_aceita_sha256():
    assert foto_evidencia_valida(FOTO) is True


def test_evidencia_aceita_maiuscula_e_espaco():
    assert foto_evidencia_valida("  " + FOTO.upper() + "  ") is True


def test_evidencia_recusa_numero():
    assert foto_evidencia_valida(123456) is False


# --- falha de camera -------------------------------------------------------

@pytest.mark.parametrize("erro", [
    "NotAllowedError", "PermissionDeniedError", "NotFoundError",
    "DevicesNotFoundError", "NotReadableError", "TrackStartError",
    "OverconstrainedError", "SecurityError", "AbortError",
    "ErroDesconhecido", None, "",
])
def test_falha_de_camera_nunca_libera_login(erro):
    d = classificar_falha_camera(erro)
    assert d["login_liberado"] is False
    assert d["motivo"]
    assert len(d["orientacao"]) >= 3


def test_camera_negada_e_distinta_de_indisponivel():
    assert classificar_falha_camera("NotAllowedError")["estado"] == "negada"
    assert classificar_falha_camera("NotFoundError")["estado"] == "indisponivel"


def test_orientacao_aponta_emergencia_sem_liberar_sistema():
    d = classificar_falha_camera("NotAllowedError")
    texto = " ".join(d["orientacao"]).lower()
    assert "emergencia" in texto
    assert "nao libera" in texto


# --- emergencia ------------------------------------------------------------

def test_emergencia_nao_concede_nada():
    a = acesso_emergencia()
    assert a["cria_sessao"] is False
    assert a["libera_dados_paciente"] is False
    assert a["atribui_atividade"] is False
    assert a["identifica_cuidadora"] is False
    assert a["telefone_samu"] == "192"


def test_emergencia_devolve_copia_e_nao_estado_compartilhado():
    a = acesso_emergencia()
    a["cria_sessao"] = True
    assert acesso_emergencia()["cria_sessao"] is False
