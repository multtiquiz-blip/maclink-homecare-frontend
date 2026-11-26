"""
Politica de autenticacao em duas etapas - regra pura, sem UI e sem HTTP.

Decisao do proprietario (25/11/2026):
  * Toda cuidadora mostra o rosto em TODO login.
  * Nao existe "entrar sem foto", pular etapa ou identificacao alternativa.
  * Se a camera falhar, o login normal fica BLOQUEADO.
  * Emergencia e independente: nao cria sessao, nao libera dados do paciente,
    nao atribui atividade a pessoa nao identificada.

Captura de imagem NAO e reconhecimento biometrico. Este modulo NAO compara
rostos. A identidade e confirmada pelo PIN; a foto e evidencia de auditoria.

Este arquivo nao importa banco, nao importa FastAPI e nao toca em rede.
Pode ser testado isoladamente.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EtapaLogin(str, Enum):
    """Desfecho possivel de uma tentativa de login."""

    NEGADO = "negado"                      # PIN invalido ou usuario inativo
    FOTO_OBRIGATORIA = "foto_obrigatoria"  # PIN ok, falta o rosto
    AUTENTICADO = "autenticado"            # sessao pode ser emitida


@dataclass(frozen=True)
class ResultadoLogin:
    etapa: EtapaLogin
    motivo: str
    libera_dados: bool

    @property
    def emite_sessao(self) -> bool:
        return self.etapa is EtapaLogin.AUTENTICADO


def decidir_login(
    *,
    pin_ok: bool,
    exigir_foto: bool,
    foto_confirmada: bool = False,
) -> ResultadoLogin:
    """
    Decide o desfecho de uma tentativa de login.

    Ordem das checagens (nao inverter):
      1. PIN errado -> NEGADO. Nunca revela se o usuario existe.
      2. Politica de foto ativa e sem rosto -> FOTO_OBRIGATORIA (bloqueado).
      3. Caso contrario -> AUTENTICADO.

    `exigir_foto=False` existe apenas para preservar o comportamento dos
    testes legados. Producao deve sempre passar True.
    """
    if not pin_ok:
        return ResultadoLogin(EtapaLogin.NEGADO, "Usuario ou PIN invalido", False)

    if exigir_foto and not foto_confirmada:
        return ResultadoLogin(
            EtapaLogin.FOTO_OBRIGATORIA,
            "Mostre o rosto para concluir o acesso. Sem a foto o login nao e liberado.",
            False,
        )

    return ResultadoLogin(EtapaLogin.AUTENTICADO, "", True)


_FALHAS_CAMERA = {
    "NotAllowedError": ("negada", "Permissao de camera negada no navegador."),
    "PermissionDeniedError": ("negada", "Permissao de camera negada no navegador."),
    "NotFoundError": ("indisponivel", "Nenhuma camera encontrada neste aparelho."),
    "DevicesNotFoundError": ("indisponivel", "Nenhuma camera encontrada neste aparelho."),
    "NotReadableError": ("indisponivel", "A camera esta em uso por outro aplicativo."),
    "TrackStartError": ("indisponivel", "A camera esta em uso por outro aplicativo."),
    "OverconstrainedError": ("indisponivel", "A camera nao atende a configuracao pedida."),
    "SecurityError": ("indisponivel", "A camera exige HTTPS ou localhost."),
    "AbortError": ("indisponivel", "A abertura da camera foi interrompida."),
}


def classificar_falha_camera(nome_erro: Optional[str]) -> dict:
    """
    Traduz o erro da camera em orientacao operacional.

    Nunca devolve caminho alternativo de identificacao: a saida e sempre
    'login bloqueado' + o que fazer. A emergencia continua disponivel.
    """
    estado, motivo = _FALHAS_CAMERA.get(
        nome_erro or "", ("indisponivel", "Falha ao abrir a camera.")
    )
    return {
        "estado": estado,
        "motivo": motivo,
        "login_liberado": False,
        "orientacao": [
            "Libere a camera no cadeado da barra de endereco e tente de novo.",
            "Feche outros aplicativos que estejam usando a camera.",
            "Se nao resolver, use o botao de Emergencia: ele avisa a coordenacao.",
            "Emergencia nao libera o sistema nem registra cuidado em seu nome.",
        ],
    }


def foto_evidencia_valida(foto_hash: Optional[str]) -> bool:
    """
    Aceita apenas hash SHA-256 em hex (64 caracteres) da imagem capturada.

    Recusa string vazia, None, 'pulado', 'sem_foto' e qualquer marcador de
    bypass. Nao existe valor que substitua a captura real.
    """
    if not foto_hash or not isinstance(foto_hash, str):
        return False
    h = foto_hash.strip().lower()
    if len(h) != 64:
        return False
    return all(c in "0123456789abcdef" for c in h)


def acesso_emergencia() -> dict:
    """
    O que a emergencia concede. Explicito para nao haver ambiguidade
    nem na API, nem na tela, nem no contrato.
    """
    return {
        "cria_sessao": False,
        "libera_dados_paciente": False,
        "atribui_atividade": False,
        "identifica_cuidadora": False,
        "telefone_samu": "192",
    }
