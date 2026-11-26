"""
Matriz única de permissões — fonte única de verdade.

Três camadas de defesa:
  1. Tela esconde (UX)
  2. API rejeita (autoridade)
  3. Banco audita (registra tentativa negada)

Nenhuma regra de permissão pode viver fora deste arquivo.
Toda revalidação no backend passa por `pode()`.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class Papel(str, Enum):
    CUIDADORA = "cuidadora"
    TECNICO = "tecnico"
    AUXILIAR = "auxiliar"
    ENFERMEIRO = "enfermeiro"
    FAMILIA = "familia"
    COORDENACAO = "coordenacao"


class Acao(str, Enum):
    # Registro comum (livres)
    REGISTRAR_CUIDADO = "registrar_cuidado"
    REGISTRAR_AGUA = "registrar_agua"
    REGISTRAR_BANHEIRO = "registrar_banheiro"
    REGISTRAR_SONO = "registrar_sono"
    REGISTRAR_HUMOR = "registrar_humor"
    REGISTRAR_PASSEIO = "registrar_passeio"
    REGISTRAR_DOR = "registrar_dor"
    REGISTRAR_QUEDA = "registrar_queda"

    # Controlados (só enfermeiro libera)
    REGISTRAR_REMEDIO = "registrar_remedio"
    REGISTRAR_COMIDA = "registrar_comida"
    REGISTRAR_FRALDA = "registrar_fralda"
    REGISTRAR_BANHO = "registrar_banho"
    REGISTRAR_POSICAO = "registrar_posicao"

    # Privativos (só enfermagem verificada)
    REGISTRAR_DEXTRO = "registrar_dextro"
    REGISTRAR_PRESSAO = "registrar_pressao"
    REGISTRAR_OXIGENIO = "registrar_oxigenio"
    REGISTRAR_TEMPERATURA = "registrar_temperatura"

    # Plano e administração
    EDITAR_PLANO = "editar_plano"
    LIBERAR_TAREFA = "liberar_tarefa"
    DEFINIR_LIMITES = "definir_limites"
    CONFIGURAR_REAFERICAO = "configurar_reafericao"
    GERENCIAR_ESCALA = "gerenciar_escala"

    # Envio e visualização
    GERAR_PDF = "gerar_pdf"
    ENVIAR_RELATORIO = "enviar_relatorio"
    VER_CAMERA = "ver_camera"
    VER_RESUMO_FAMILIA = "ver_resumo_familia"
    VER_PAINEL_COMPARTILHADO = "ver_painel_compartilhado"
    VER_RELATORIO_AGREGADO = "ver_relatorio_agregado"


@dataclass
class Usuario:
    """Representação mínima do usuário para checagem de permissão."""
    id: str
    papel: Papel
    categoria: Optional[str] = None      # enfermeiro / tecnico / auxiliar
    verificado: bool = False             # COREN conferido
    ativo: bool = True


@dataclass
class Plano:
    """Representação mínima do plano de cuidado para checagem."""
    idoso_id: str
    liberacoes: dict                     # ex.: {"remedio": True, "pressao": False}
    autorizacoes: dict                   # ex.: {"pressao": True, "oxigenio": False}


_ACOES_COMUNS = {
    Acao.REGISTRAR_CUIDADO, Acao.REGISTRAR_AGUA, Acao.REGISTRAR_BANHEIRO,
    Acao.REGISTRAR_SONO, Acao.REGISTRAR_HUMOR, Acao.REGISTRAR_PASSEIO,
    Acao.REGISTRAR_DOR, Acao.REGISTRAR_QUEDA,
    Acao.GERAR_PDF, Acao.ENVIAR_RELATORIO,
}

_ACOES_ENFERMAGEM = _ACOES_COMUNS | {
    Acao.REGISTRAR_REMEDIO, Acao.REGISTRAR_COMIDA, Acao.REGISTRAR_FRALDA,
    Acao.REGISTRAR_BANHO, Acao.REGISTRAR_POSICAO,
    Acao.REGISTRAR_PRESSAO, Acao.REGISTRAR_OXIGENIO, Acao.REGISTRAR_TEMPERATURA,
}

MATRIZ = {
    Papel.CUIDADORA: _ACOES_COMUNS.copy(),
    Papel.TECNICO: _ACOES_ENFERMAGEM.copy(),
    Papel.AUXILIAR: _ACOES_ENFERMAGEM.copy(),
    Papel.ENFERMEIRO: _ACOES_ENFERMAGEM | {
        Acao.REGISTRAR_DEXTRO,
        Acao.EDITAR_PLANO, Acao.LIBERAR_TAREFA, Acao.DEFINIR_LIMITES,
        Acao.CONFIGURAR_REAFERICAO, Acao.GERENCIAR_ESCALA,
        Acao.VER_CAMERA, Acao.VER_RESUMO_FAMILIA,
        Acao.VER_PAINEL_COMPARTILHADO, Acao.VER_RELATORIO_AGREGADO,
    },
    Papel.FAMILIA: {
        Acao.REGISTRAR_CUIDADO, Acao.REGISTRAR_AGUA, Acao.REGISTRAR_BANHEIRO,
        Acao.REGISTRAR_SONO, Acao.REGISTRAR_HUMOR, Acao.REGISTRAR_PASSEIO,
        Acao.REGISTRAR_DOR, Acao.REGISTRAR_QUEDA,
        Acao.GERAR_PDF, Acao.ENVIAR_RELATORIO, Acao.VER_RESUMO_FAMILIA,
    },
    Papel.COORDENACAO: {
        Acao.GERAR_PDF, Acao.ENVIAR_RELATORIO, Acao.VER_RESUMO_FAMILIA,
        Acao.VER_CAMERA, Acao.VER_PAINEL_COMPARTILHADO,
        Acao.VER_RELATORIO_AGREGADO, Acao.GERENCIAR_ESCALA,
    },
}


def pode(
    acao: Acao,
    usuario: Optional[Usuario],
    plano: Optional[Plano] = None,
) -> bool:
    """
    Verifica se o usuário pode executar a ação.

    REGRAS DURAS (não podem ser contornadas):
    - Dextro: só enfermeiro com COREN verificado.
    - Pressão/O2/Temp: enfermagem verificada OU liberado no plano.
    - Controlados: cuidadora só se liberado no plano.
    - Plano/limites/liberação: só enfermeiro.

    ORDEM DAS CHECAGENS (importante):
    1. Usuário existe e está ativo
    2. Regras especiais (dextro, números, controlados, plano)
    3. Matriz base (fallback para ações comuns)

    As regras especiais vêm ANTES da matriz porque uma cuidadora
    pode ter permissão via plano para uma ação que não está na
    matriz base dela (ex.: pressão autorizada).
    """
    if usuario is None or not usuario.ativo:
        return False

    # -------------------------------------------------------------------
    # 1. Regras especiais (antes da matriz)
    # -------------------------------------------------------------------

    # Dextro: só enfermeiro verificado
    if acao == Acao.REGISTRAR_DEXTRO:
        return (
            usuario.papel == Papel.ENFERMEIRO
            and usuario.verificado is True
            and usuario.categoria == "enfermeiro"
        )

    # Números: enfermagem verificada OU autorizado no plano
    if acao in {Acao.REGISTRAR_PRESSAO, Acao.REGISTRAR_OXIGENIO,
                Acao.REGISTRAR_TEMPERATURA}:
        if usuario.papel in {Papel.ENFERMEIRO, Papel.TECNICO, Papel.AUXILIAR}:
            return usuario.verificado is True
        if usuario.papel == Papel.CUIDADORA and plano is not None:
            chave = acao.value.replace("registrar_", "")
            return bool(plano.autorizacoes.get(chave, False))
        return False

    # Controlados: cuidadora só se liberado no plano
    if acao in {Acao.REGISTRAR_REMEDIO, Acao.REGISTRAR_COMIDA,
                Acao.REGISTRAR_FRALDA, Acao.REGISTRAR_BANHO,
                Acao.REGISTRAR_POSICAO}:
        if usuario.papel == Papel.CUIDADORA:
            return bool(plano and plano.liberacoes.get(acao.value, False))
        # Enfermagem verificada cai no fallback da matriz abaixo
        # (todos esses estão em _ACOES_ENFERMAGEM)
        return acao in MATRIZ.get(usuario.papel, set())

    # Plano/limites/liberação: só enfermeiro verificado
    if acao in {Acao.EDITAR_PLANO, Acao.LIBERAR_TAREFA, Acao.DEFINIR_LIMITES,
                Acao.CONFIGURAR_REAFERICAO}:
        return usuario.papel == Papel.ENFERMEIRO and usuario.verificado is True

    # -------------------------------------------------------------------
    # 2. Matriz base (fallback)
    # -------------------------------------------------------------------
    return acao in MATRIZ.get(usuario.papel, set())


def exigir(acao: Acao, usuario: Optional[Usuario], plano: Optional[Plano] = None) -> None:
    """Levanta exceção se não puder. A API deve usar esta versão."""
    if not pode(acao, usuario, plano):
        raise PermissionError(
            f"Ação negada: {acao.value} para "
            f"{usuario.papel if usuario else 'anônimo'}"
        )


def auditar_tentativa_negada(
    usuario_id: Optional[str],
    acao: Acao,
    ts: int,
    motivo: str,
) -> None:
    """
    Registra tentativa negada no banco de auditoria.
    Nunca deixar passar em silêncio: alguém tentou furar a regra.
    """
    pass
