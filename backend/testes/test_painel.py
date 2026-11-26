"""Testes do cálculo do painel."""

from backend.nucleo.painel import (
    EstadoPaciente,
    RegistroResumo,
    TarefaResumo,
    calcular_resumo,
)


def _reg(**kwargs):
    base = dict(ts=100, tipo="agua", texto="Bebeu água", valor=None, fora_do_limite=False)
    base.update(kwargs)
    return RegistroResumo(**base)


def _tar(**kwargs):
    base = dict(id="t1", nome="Água", hora_alvo=200, feita=False, atrasada=False, minutos_para_vencer=10)
    base.update(kwargs)
    return TarefaResumo(**base)


def test_sem_registros_sem_tarefas_em_dia():
    r = calcular_resumo("e1", [], [], agora=100)
    assert r.estado == EstadoPaciente.EM_DIA


def test_registro_fora_do_limite_vira_alerta():
    r = calcular_resumo(
        "e1",
        [_reg(fora_do_limite=True, texto="Pressão", valor="180/110")],
        [],
        agora=100,
    )
    assert r.estado == EstadoPaciente.ALERTA
    assert r.tem_alerta_critico is True
    assert "180/110" in r.frase_curta


def test_tarefa_atrasada_vira_atrasado():
    r = calcular_resumo(
        "e1",
        [],
        [_tar(atrasada=True, minutos_para_vencer=-30)],
        agora=100,
    )
    assert r.estado == EstadoPaciente.ATRASADO


def test_tarefa_proxima_vira_atencao():
    r = calcular_resumo(
        "e1",
        [],
        [_tar(minutos_para_vencer=10)],
        agora=100,
    )
    assert r.estado == EstadoPaciente.ATENCAO


def test_alerta_tem_precedencia_sobre_atrasado():
    r = calcular_resumo(
        "e1",
        [_reg(fora_do_limite=True, texto="SpO2", valor="85%")],
        [_tar(atrasada=True)],
        agora=100,
    )
    assert r.estado == EstadoPaciente.ALERTA


def test_ultima_acao_e_a_mais_recente():
    r = calcular_resumo(
        "e1",
        [_reg(ts=100, texto="A"), _reg(ts=300, texto="B"), _reg(ts=200, texto="C")],
        [],
        agora=400,
    )
    assert r.ultima_acao_texto == "B"
    assert r.ultima_acao_ts == 300
