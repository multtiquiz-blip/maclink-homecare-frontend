"""Testes da avaliação de números contra limites."""

from backend.nucleo.limites import avaliar_numeros


# ---------------------------------------------------------------------------
# Pressão
# ---------------------------------------------------------------------------

def test_pressao_dentro_do_limite():
    aval = avaliar_numeros(
        "pressao",
        {"sis": 120, "dia": 80},
        {"sis": 150, "dia": 90},
    )
    assert aval["fora"] is False
    assert aval["motivos"] == []


def test_pressao_sistolica_acima():
    aval = avaliar_numeros(
        "pressao", {"sis": 160, "dia": 80}, {"sis": 150, "dia": 90},
    )
    assert aval["fora"] is True
    assert "160" in aval["motivos"][0]
    assert "150" in aval["motivos"][0]


def test_pressao_diastolica_acima():
    aval = avaliar_numeros(
        "pressao", {"sis": 140, "dia": 100}, {"sis": 150, "dia": 90},
    )
    assert aval["fora"] is True
    assert "diastólica" in aval["motivos"][0]


def test_pressao_sem_limite_definido_nao_avalia():
    """Limite None = enfermeiro não definiu, não pode acusar."""
    aval = avaliar_numeros(
        "pressao", {"sis": 200, "dia": 120}, {"sis": None, "dia": None},
    )
    assert aval["fora"] is False


# ---------------------------------------------------------------------------
# Pulso (com pressão ou oxigênio)
# ---------------------------------------------------------------------------

def test_pulso_acima_do_limite():
    aval = avaliar_numeros(
        "pressao",
        {"sis": 120, "dia": 80, "pulso": 120},
        {"sis": 150, "dia": 90, "pulso_max": 100},
    )
    assert aval["fora"] is True
    assert "Pulso 120" in aval["motivos"][0]


def test_pulso_abaixo_do_limite():
    aval = avaliar_numeros(
        "oxigenio",
        {"spo": 96, "pulso": 45},
        {"spo": 90, "pulso_min": 60},
    )
    assert aval["fora"] is True
    assert "Pulso 45" in aval["motivos"][0]


# ---------------------------------------------------------------------------
# Oxigênio
# ---------------------------------------------------------------------------

def test_oxigenio_abaixo():
    aval = avaliar_numeros("oxigenio", {"spo": 88}, {"spo": 90})
    assert aval["fora"] is True
    assert "88" in aval["motivos"][0]


def test_oxigenio_normal():
    aval = avaliar_numeros("oxigenio", {"spo": 96}, {"spo": 90})
    assert aval["fora"] is False


# ---------------------------------------------------------------------------
# Temperatura (febre e hipotermia)
# ---------------------------------------------------------------------------

def test_temperatura_normal():
    aval = avaliar_numeros(
        "temperatura", {"temp": 36.5}, {"temp_max": 37.5, "temp_min": 35.0},
    )
    assert aval["fora"] is False


def test_temperatura_febre():
    aval = avaliar_numeros(
        "temperatura", {"temp": 38.2}, {"temp_max": 37.5, "temp_min": 35.0},
    )
    assert aval["fora"] is True
    assert "febre" in aval["motivos"][0]


def test_temperatura_hipotermia():
    """O ponto que você lembrou: temperatura ABAIXO do limite."""
    aval = avaliar_numeros(
        "temperatura", {"temp": 34.5}, {"temp_max": 37.5, "temp_min": 35.0},
    )
    assert aval["fora"] is True
    assert "hipotermia" in aval["motivos"][0]


def test_temperatura_apenas_limite_max_definido():
    """Se enfermeiro só definiu febre, hipotermia não acusa."""
    aval = avaliar_numeros(
        "temperatura", {"temp": 34.0}, {"temp_max": 37.5},
    )
    assert aval["fora"] is False


# ---------------------------------------------------------------------------
# Dextro
# ---------------------------------------------------------------------------

def test_dextro_hipoglicemia():
    aval = avaliar_numeros("dextro", {"dextro": 60}, {"dexMin": 70, "dexMax": 180})
    assert aval["fora"] is True
    assert "60" in aval["motivos"][0]


def test_dextro_hiperglicemia():
    aval = avaliar_numeros("dextro", {"dextro": 210}, {"dexMin": 70, "dexMax": 180})
    assert aval["fora"] is True
    assert "210" in aval["motivos"][0]


def test_dextro_normal():
    aval = avaliar_numeros("dextro", {"dextro": 110}, {"dexMin": 70, "dexMax": 180})
    assert aval["fora"] is False


# ---------------------------------------------------------------------------
# Múltiplos motivos
# ---------------------------------------------------------------------------

def test_pressao_e_pulso_alterados_dois_motivos():
    aval = avaliar_numeros(
        "pressao",
        {"sis": 180, "dia": 110, "pulso": 130},
        {"sis": 150, "dia": 90, "pulso_max": 100},
    )
    assert aval["fora"] is True
    assert len(aval["motivos"]) == 3
