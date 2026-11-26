"""
Cálculo do dia de cuidado e situação de tarefas.

Regra do projeto: o dia de cuidado vai de 06:00 a 06:00.
Isso evita que plantões noturnos sejam partidos ao meio-dia.
"""

from datetime import datetime, timedelta


def dia_de_cuidado(ts: int, inicio_hora: int = 6) -> str:
    """
    Retorna a data (YYYY-MM-DD) do dia de cuidado de um timestamp.

    Se a hora for antes das 06:00, pertence ao dia anterior.
    """
    dt = datetime.fromtimestamp(ts)
    if dt.hour < inicio_hora:
        dt = dt - timedelta(days=1)
    return dt.strftime("%Y-%m-%d")


def rotulo_dia(ts: int, inicio_hora: int = 6) -> str:
    """Rótulo legível do dia de cuidado."""
    dia = dia_de_cuidado(ts, inicio_hora)
    return f"Dia de cuidado {dia} · {inicio_hora:02d}:00 → {inicio_hora:02d}:00"


def inicio_do_dia(ts: int, inicio_hora: int = 6) -> int:
    """
    Timestamp do início do dia de cuidado (06:00 daquele dia).

    Útil para filtrar registros do dia.
    """
    dt = datetime.fromtimestamp(ts)
    if dt.hour < inicio_hora:
        dt = dt - timedelta(days=1)
    inicio = dt.replace(hour=inicio_hora, minute=0, second=0, microsecond=0)
    return int(inicio.timestamp())
