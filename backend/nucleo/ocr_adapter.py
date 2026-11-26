"""
Adapter de OCR para captura de afericoes.

Separa duas responsabilidades que nao podem se misturar:
  1. Extrair tokens (texto + posicao + confianca) da imagem do visor.
  2. Normalizar esses tokens antes de entrega-los ao interprete.

Regras do proprietario (25/11/2026):
  * A leitura automatica e sempre conferida pelo cuidador.
  * Nao inventar valores. Nao alterar unidades silenciosamente.
  * Reflexos, inclinacao e baixa iluminacao sao condicao real:
    o adapter marca baixa confianca em vez de adivinhar.

Este modulo nao toca em camera nem em rede. O OCR real (Tesseract)
e plugado como um adapter; aqui esta o contrato e um adapter de teste.
"""def normalizar_tokens(tokens: List[Token]) -> List[Token]:
    """Aplica a normalizacao preservando posicao e confianca."""
    resultado = []
    for t in tokens:
        novo_texto = normalizar_token(t.texto)
        resultado.append(Token(
            texto=novo_texto, x=t.x, y=t.y, w=t.w, h=t.h, conf=t.conf,
        ))
    return resultado


def estimar_qualidade(tokens: List[Token]) -> str:
    """
    Heuristica simples de qualidade: poucos tokens ou confianca baixa
    indicam imagem dificil (reflexo, borrado, inclinada).
    Nao diagnostica causa - so sinaliza para a tela pedir nova captura.
    """
    if not tokens:
        return "baixa"
    confs = [t.conf for t in tokens if t.conf is not None]
    if confs:
        media = sum(confs) / len(confs)
        if media < 0.5:
            return "baixa"
    if len([t for t in tokens if t.texto.strip()]) < 2:
        return "baixa"
    return "boa"


class OcrMockAdapter:
    """
    Adapter deterministico para TESTES. Recebe tokens prontos e devolve
    normalizados. Nao faz OCR de verdade; valida o contrato e o fluxo.
    """

    def __init__(self, tokens: List[Token]):
        self._tokens = tokens

    def extrair(self, imagem: bytes = b"") -> ResultadoOCR:
        normalizados = normalizar_tokens(self._tokens)
        qualidade = estimar_qualidade(normalizados)
        confs = [t.conf for t in normalizados if t.conf is not None]
        media = (sum(confs) / len(confs)) if confs else 0.0
        avisos = []
        if qualidade == "baixa":
            avisos.append("Imagem dificil. Se possivel, capture de novo com mais luz e enquadre o visor.")
        return ResultadoOCR(
            tokens=normalizados,
            confianca_media=media,
            qualidade_imagem=qualidade,
            avisos=avisos,
        )


class OcrTesseractAdapter:
    """OCR opcional via Tesseract; extrai tokens, sem interpretar/confirmar aferições."""
    def __init__(self):
        self._pytesseract = None
        self._disponivel = False
        try:
            import pytesseract
            from PIL import Image  # noqa: F401
            self._pytesseract = pytesseract
            self._disponivel = True
        except Exception:
            self._disponivel = False

    @property
    def disponivel(self) -> bool:
        return self._disponivel

    def extrair(self, imagem: bytes) -> ResultadoOCR:
        if not self._disponivel:
            return ResultadoOCR(tokens=[], confianca_media=0.0,
                qualidade_imagem="desconhecida",
                avisos=["OCR indisponível neste ambiente. Digite os valores manualmente."])
        if not imagem:
            return ResultadoOCR(tokens=[], confianca_media=0.0,
                qualidade_imagem="baixa", avisos=["Imagem vazia. Capture o visor novamente."])
        try:
            from io import BytesIO
            from PIL import Image
            img = Image.open(BytesIO(imagem)).convert("RGB")
            dados = self._pytesseract.image_to_data(img, output_type=self._pytesseract.Output.DICT)
            tokens = []
            for i, texto in enumerate(dados.get("text", [])):
                texto = (texto or "").strip()
                if not texto:
                    continue
                try:
                    c = float(dados.get("conf", [])[i])
                except (TypeError, ValueError, IndexError):
                    c = -1.0
                conf = c / 100.0 if c >= 0 else None
                tokens.append(Token(texto=texto, x=int(dados.get("left", [0])[i]),
                    y=int(dados.get("top", [0])[i]), w=int(dados.get("width", [0])[i]),
                    h=int(dados.get("height", [0])[i]), conf=conf))
            tokens = normalizar_tokens(tokens)
            confs = [t.conf for t in tokens if t.conf is not None]
            media = sum(confs) / len(confs) if confs else 0.0
            qualidade = estimar_qualidade(tokens)
            avisos = []
            if qualidade == "baixa":
                avisos.append("Imagem difícil. Confira os valores ou capture novamente.")
            if not tokens:
                avisos.append("Nenhum texto reconhecido. Digite os valores manualmente.")
            return ResultadoOCR(tokens=tokens, confianca_media=media,
                qualidade_imagem=qualidade, avisos=avisos)
        except Exception:
            return ResultadoOCR(tokens=[], confianca_media=0.0,
                qualidade_imagem="desconhecida",
                avisos=["Não foi possível processar a imagem. Digite os valores manualmente."])

from dataclasses import dataclass, field
from typing import List, Optional, Protocol

# Reusa o Token do interprete para manter um unico formato de contrato.
from backend.nucleo.afericoes import Token


# Rotulos que NUNCA devem sofrer correcao de caractere confundido.
ROTULOS_PROTEGIDOS = {
    "sys", "syst", "dia", "diast", "pul", "pr", "hr", "bpm",
    "spo2", "spo", "sat", "glu", "hi", "lo", "err",
    "mmhg", "mmol", "mg",
}

_CARACTERES_CONFUNDIDOS = {
    "O": "0", "o": "0",
    "Q": "0", "D": "0",
    "l": "1", "I": "1", "|": "1",
    "S": "5", "s": "5",
    "B": "8", "Z": "2", "z": "2",
    "G": "6", "g": "9",
    ",": ".",
}


@dataclass
class ResultadoOCR:
    """Saida padronizada de qualquer adapter de OCR."""
    tokens: List[Token] = field(default_factory=list)
    confianca_media: float = 0.0
    qualidade_imagem: str = "desconhecida"   # boa | baixa | desconhecida
    avisos: List[str] = field(default_factory=list)

    @property
    def legivel(self) -> bool:
        return any(t.texto.strip() for t in self.tokens)


class OcrAdapter(Protocol):
    """Contrato que todo adapter de OCR deve cumprir."""

    def extrair(self, imagem: bytes) -> ResultadoOCR:
        """Recebe os bytes da imagem e devolve tokens ja normalizados."""
        ...


def _e_predominantemente_numerico(texto: str) -> bool:
    """
    Diz se um token e um numero (pode ter 1-2 letras confundidas)
    e nao um rotulo. Criterio conservador: pelo menos metade digitos.
    """
    if not texto:
        return False
    s = texto.strip()
    if s.lower() in ROTULOS_PROTEGIDOS:
        return False
    digitos = sum(1 for c in s if c.isdigit())
    return digitos >= max(1, len(s) / 2)


def normalizar_token(texto: str) -> str:
    """
    Corrige caracteres confundidos pelo OCR apenas em tokens numericos.

    Rotulos ficam intactos (evita "O2" virar "02").
    Numeros ganham correcao (evita "1O0" nao ser lido como 100).
    """
    s = (texto or "").strip()
    if not s:
        return s
    if not _e_predominantemente_numerico(s):
        return s
    saida = []
    for c in s:
        if c.isdigit() or c == ".":
            saida.append(c)
        else:
            saida.append(_CARACTERES_CONFUNDIDOS.get(c, c))
    return "".join(saida)


def normalizar_tokens(tokens: List[Token]) -> List[Token]:
    """Aplica a normalizacao preservando posicao e confianca."""
    resultado = []
    for t in tokens:
        novo_texto = normalizar_token(t.texto)
        resultado.append(Token(
            texto=novo_texto, x=t.x, y=t.y, w=t.w, h=t.h, conf=t.conf,
        ))
    return resultado


def estimar_qualidade(tokens: List[Token]) -> str:
    """
    Heuristica simples de qualidade: poucos tokens ou confianca baixa
    indicam imagem dificil (reflexo, borrado, inclinada).
    Nao diagnostica causa - so sinaliza para a tela pedir nova captura.
    """
    if not tokens:
        return "baixa"
    confs = [t.conf for t in tokens if t.conf is not None]
    if confs:
        media = sum(confs) / len(confs)
        if media < 0.5:
            return "baixa"
    if len([t for t in tokens if t.texto.strip()]) < 2:
        return "baixa"
    return "boa"


class OcrMockAdapter:
    """
    Adapter deterministico para TESTES. Recebe tokens prontos e devolve
    normalizados. Nao faz OCR de verdade; valida o contrato e o fluxo.
    """

    def __init__(self, tokens: List[Token]):
        self._tokens = tokens

    def extrair(self, imagem: bytes = b"") -> ResultadoOCR:
        normalizados = normalizar_tokens(self._tokens)
        qualidade = estimar_qualidade(normalizados)
        confs = [t.conf for t in normalizados if t.conf is not None]
        media = (sum(confs) / len(confs)) if confs else 0.0
        avisos = []
        if qualidade == "baixa":
            avisos.append("Imagem dificil. Se possivel, capture de novo com mais luz e enquadre o visor.")
        return ResultadoOCR(
            tokens=normalizados,
            confianca_media=media,
            qualidade_imagem=qualidade,
            avisos=avisos,
        )


class OcrTesseractAdapter:
    """
    Adapter para Tesseract (backend Python). Marcado como NAO IMPLEMENTADO
    ate a dependencia estar disponivel no ambiente de destino. Nao fingimos
    OCR real sem o pacote instalado.
    """

    def __init__(self):
        self._disponivel = False
        try:
            import pytesseract  # noqa: F401
            self._disponivel = True
        except Exception:
            self._disponivel = False

    @property
    def disponivel(self) -> bool:
        return self._disponivel

    def extrair(self, imagem: bytes) -> ResultadoOCR:
        if not self._disponivel:
            return ResultadoOCR(
                tokens=[],
                confianca_media=0.0,
                qualidade_imagem="desconhecida",
                avisos=["OCR indisponível neste ambiente. Digite os valores manualmente."],
            )
        raise NotImplementedError("Integração Tesseract ainda não implementada.")
