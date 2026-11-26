"""
Avaliação de números contra os limites do plano.

Cada medida pode ter múltiplos limites. Ex.:
- Pressão: sis (max), dia (max), pulso_min, pulso_max
- Oxigênio: spo (min), pulso_min, pulso_max
- Temperatura: temp_max (febre), temp_min (hipotermia)
- Dextro: dexMin (hipoglicemia), dexMax (hiperglicemia)

Regra dura: se o limite não foi definido pelo enfermeiro (None),
aquele campo NÃO é avaliado. O sistema nunca inventa número clínico.
"""


def avaliar_numeros(tipo: str, valor: dict, limites: dict) -> dict:
    """
    Avalia um valor numérico contra os limites.

    Retorna {"fora": bool, "motivos": list[str]}.
    Motivos são frases legíveis para o alerta.
    """
    motivos: list[str] = []

    if tipo == "pressao":
        _checar_max(motivos, valor, "sis", limites, "sis", "Pressão sistólica")
        _checar_max(motivos, valor, "dia", limites, "dia", "Pressão diastólica")
        _checar_pulso(motivos, valor, limites)

    elif tipo == "oxigenio":
        _checar_min(motivos, valor, "spo", limites, "spo", "Oxigênio", sufixo="%")
        _checar_pulso(motivos, valor, limites)

    elif tipo == "temperatura":
        _checar_max(
            motivos, valor, "temp", limites, "temp_max", "Temperatura",
            sufixo="°C", rotulo_limite="febre a partir de",
        )
        _checar_min(
            motivos, valor, "temp", limites, "temp_min", "Temperatura",
            sufixo="°C", rotulo_limite="hipotermia a partir de",
        )

    elif tipo == "dextro":
        _checar_min(motivos, valor, "dextro", limites, "dexMin", "Glicemia")
        _checar_max(motivos, valor, "dextro", limites, "dexMax", "Glicemia")

    return {"fora": len(motivos) > 0, "motivos": motivos}


def _checar_max(motivos, valor, campo, limites, chave_limite, rotulo,
                sufixo="", rotulo_limite="acima do limite"):
    v = valor.get(campo)
    lim = limites.get(chave_limite)
    if v is None or lim is None:
        return
    if v > lim:
        motivos.append(f"{rotulo} {v}{sufixo} {rotulo_limite} {lim}{sufixo}")


def _checar_min(motivos, valor, campo, limites, chave_limite, rotulo,
                sufixo="", rotulo_limite="abaixo do limite"):
    v = valor.get(campo)
    lim = limites.get(chave_limite)
    if v is None or lim is None:
        return
    if v < lim:
        motivos.append(f"{rotulo} {v}{sufixo} {rotulo_limite} {lim}{sufixo}")


def _checar_pulso(motivos, valor, limites):
    p = valor.get("pulso")
    if p is None:
        return
    if limites.get("pulso_max") is not None and p > limites["pulso_max"]:
        motivos.append(f"Pulso {p} bpm acima do limite {limites['pulso_max']} bpm")
    if limites.get("pulso_min") is not None and p < limites["pulso_min"]:
        motivos.append(f"Pulso {p} bpm abaixo do limite {limites['pulso_min']} bpm")
