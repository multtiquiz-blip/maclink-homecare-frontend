"""Testes do cálculo do dia de cuidado."""

from datetime import datetime

from backend.nucleo.tarefas import dia_de_cuidado, inicio_do_dia, rotulo_dia


def _ts(ano, mes, dia, hora, minuto=0):
    return int(datetime(ano, mes, dia, hora, minuto).timestamp())


def test_meio_dia_pertence_ao_dia_atual():
    assert dia_de_cuidado(_ts(2026, 11, 21, 12, 0)) == "2026-11-21"


def test_madrugada_pertence_ao_dia_anterior():
    assert dia_de_cuidado(_ts(2026, 11, 21, 3, 0)) == "2026-11-20"


def test_0600_pertence_ao_dia_novo():
    assert dia_de_cuidado(_ts(2026, 11, 21, 6, 0)) == "2026-11-21"


def test_0559_pertence_ao_dia_anterior():
    assert dia_de_cuidado(_ts(2026, 11, 21, 5, 59)) == "2026-11-20"


def test_virada_de_mes():
    # 1º de dezembro às 03:00 pertence a 30 de novembro
    assert dia_de_cuidado(_ts(2026, 12, 1, 3, 0)) == "2026-11-30"


def test_virada_de_ano():
    # 1º de janeiro às 02:00 pertence a 31 de dezembro
    assert dia_de_cuidado(_ts(2027, 1, 1, 2, 0)) == "2026-12-31"


def test_rotulo_do_dia():
    r = rotulo_dia(_ts(2026, 11, 21, 12, 0))
    assert "2026-11-21" in r
    assert "06:00" in r


def test_inicio_do_dia_retorna_0600():
    ts = _ts(2026, 11, 21, 15, 0)
    inicio = inicio_do_dia(ts)
    dt = datetime.fromtimestamp(inicio)
    assert dt.hour == 6
    assert dt.minute == 0
    assert dt.strftime("%Y-%m-%d") == "2026-11-21"


def test_inicio_do_dia_madrugada_volta_um_dia():
    ts = _ts(2026, 11, 21, 3, 0)
    inicio = inicio_do_dia(ts)
    dt = datetime.fromtimestamp(inicio)
    assert dt.hour == 6
    assert dt.strftime("%Y-%m-%d") == "2026-11-20"
