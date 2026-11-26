"""Testes da segurança do PIN."""

import pytest
from backend.nucleo.seguranca import (
    gerar_salt,
    hash_pin,
    pin_valido,
    verificar_pin,
)


def test_pin_valido_com_4_digitos():
    assert pin_valido("1234")


def test_pin_invalido_com_3_digitos():
    assert not pin_valido("123")


def test_pin_invalido_com_5_digitos():
    assert not pin_valido("12345")


def test_pin_invalido_com_letras():
    assert not pin_valido("12a4")


def test_pin_vazio_invalido():
    assert not pin_valido("")


def test_salt_aleatorio_nao_repete():
    s1 = gerar_salt()
    s2 = gerar_salt()
    assert s1 != s2


def test_hash_pin_e_deterministico():
    h1 = hash_pin("1234", "salt_fixo")
    h2 = hash_pin("1234", "salt_fixo")
    assert h1 == h2


def test_hash_pin_com_salt_diferente_muda():
    h1 = hash_pin("1234", "salt_a")
    h2 = hash_pin("1234", "salt_b")
    assert h1 != h2


def test_hash_pin_nunca_e_o_pin():
    h = hash_pin("1234", "salt")
    assert h != "1234"
    assert "1234" not in h


def test_verificar_pin_correto():
    salt = gerar_salt()
    h = hash_pin("1234", salt)
    assert verificar_pin("1234", salt, h)


def test_verificar_pin_errado():
    salt = gerar_salt()
    h = hash_pin("1234", salt)
    assert not verificar_pin("9999", salt, h)


def test_verificar_pin_com_salt_errado():
    salt = gerar_salt()
    h = hash_pin("1234", salt)
    assert not verificar_pin("1234", "outro_salt", h)


def test_hash_pin_sem_salt_levanta_erro():
    with pytest.raises(ValueError):
        hash_pin("1234", "")
