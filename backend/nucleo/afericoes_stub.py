"""Contrato neutro de dados de tokens de OCR."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Token:
    """Fragmento de texto extraído, com caixa e confiança (0..1)."""
    texto: str
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    conf: Optional[float] = None
