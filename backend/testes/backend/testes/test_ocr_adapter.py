"""
Testes do adapter de OCR. Protegem a normalizacao de caracteres
confundidos e o contrato de qualidade de imagem.
"""

import pytest

from backend.nucleo.afericoes import Token
from backend.nucleo.ocr_adapter import (
    OcrMockAdapter,
    OcrTesseractAdapter,
    estimar_qualidade,
    normalizar_token,
    normalizar_tokens,
)


def test_numero_com_o_confundido_vira_zero():
    assert normalizar_token("1O0") == "100"


def test_numero_com_l_confundido_vira_um():
    assert normalizar_token("8l") == "81"


def test_rotulo_nao_e_alterado():
    assert normalizar_token("SYS") == "SYS"
    assert normalizar_token("SpO2") == "SpO2"
    assert normalizar_token("HI") == "HI"


def test_o2_como_rotulo_nao_vira_02():
    assert normalizar_token("O2") == "O2"


def test_token_vazio_seguro():
    assert normalizar_token("") == ""
    assert normalizar_token(None) == ""


def test_normalizar_preserva_posicao_e_confianca():
    tokens = [Token("1O0", x=1, y=2, w=30, h=10, conf=0.9)]
    saida = normalizar_tokens(tokens)
    assert saida[0].texto == "100"
    assert saida[0].x == 1
    assert saida[0].conf == 0.9


def test_qualidade_baixa_com_poucos_tokens():
    assert estimar_qualidade([]) == "baixa"


def test_qualidade_baixa_com_confianca_baixa():
    tokens = [Token("1", conf=0.1), Token("2", conf=0.2)]
    assert estimar_qualidade(tokens) == "baixa"


def test_qualidade_boa_com_tokens_legiveis():
    tokens = [Token("120", conf=0.9), Token("80", conf=0.9), Token("75", conf=0.85)]
    assert estimar_qualidade(tokens) == "boa"


def test_mock_adapter_devolve_resultado_completo():
    tokens = [Token("12O"), Token("8O"), Token("75")]
    r = OcrMockAdapter(tokens).extrair(b"")
    assert r.legivel
    assert r.tokens[0].texto == "120"
    assert r.tokens[1].texto == "80"
    assert r.qualidade_imagem == "boa"


def test_mock_adapter_avisa_imagem_dificil():
    tokens = [Token("?", conf=0.1)]
    r = OcrMockAdapter(tokens).extrair(b"")
    assert r.qualidade_imagem == "baixa"
    assert r.avisos


def test_tesseract_adapter_nao_quebra_sem_pacote():
    a = OcrTesseractAdapter()
    r = a.extrair(b"")
    assert isinstance(r.avisos, list)
    if not a.disponivel:
        assert r.tokens == []
