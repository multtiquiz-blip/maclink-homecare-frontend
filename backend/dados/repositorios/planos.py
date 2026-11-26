"""
Repositório de planos de cuidado.

O plano é único por paciente (versão mais recente).
Atualizar = incrementar versão e gravar, mantendo o id.

Regra dura: limites começam SEMPRE vazios ({}), nunca com número
clínico hardcoded. Quem define é o enfermeiro.
"""

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class PlanoDB:
    id: str
    idoso_id: str
    perfil: Optional[str]
    periodo: Optional[str]
    pecas: list
    limites: dict
    autorizacoes: dict
    liberacoes: dict
    escada: list
    espera_min: int
    definido_por: Optional[str]
    definido_em: Optional[int]
    versao: int


def criar_ou_atualizar(
    conn: sqlite3.Connection,
    *,
    idoso_id: str,
    perfil: str,
    periodo: str,
    pecas: list,
    limites: dict,
    autorizacoes: dict,
    liberacoes: dict,
    escada: list,
    espera_min: int,
    definido_por: str,
) -> str:
    """
    Cria ou atualiza o plano do paciente.

    Se já existe plano: atualiza e incrementa versão.
    Se não existe: cria versão 1.
    Retorna o id do plano.
    """
    agora = int(time.time())
    existente = buscar_por_idoso(conn, idoso_id)

    if existente:
        conn.execute(
            """
            UPDATE planos SET
                perfil = ?, periodo = ?, pecas = ?, limites = ?,
                autorizacoes = ?, liberacoes = ?, escada = ?,
                espera_min = ?, definido_por = ?, definido_em = ?,
                versao = ?
            WHERE id = ?
            """,
            (
                perfil, periodo, json.dumps(pecas), json.dumps(limites),
                json.dumps(autorizacoes), json.dumps(liberacoes),
                json.dumps(escada), espera_min, definido_por, agora,
                existente.versao + 1, existente.id,
            ),
        )
        conn.commit()
        return existente.id

    novo_id = f"pl_{uuid.uuid4().hex[:12]}"
    conn.execute(
        """
        INSERT INTO planos (
            id, idoso_id, perfil, periodo, pecas, limites,
            autorizacoes, liberacoes, escada, espera_min,
            definido_por, definido_em, versao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            novo_id, idoso_id, perfil, periodo, json.dumps(pecas),
            json.dumps(limites), json.dumps(autorizacoes),
            json.dumps(liberacoes), json.dumps(escada),
            espera_min, definido_por, agora,
        ),
    )
    conn.commit()
    return novo_id


def buscar_por_idoso(
    conn: sqlite3.Connection, idoso_id: str
) -> Optional[PlanoDB]:
    row = conn.execute(
        "SELECT * FROM planos WHERE idoso_id = ? ORDER BY versao DESC LIMIT 1",
        (idoso_id,),
    ).fetchone()
    if row is None:
        return None
    return _linha(row)


def _linha(row: sqlite3.Row) -> PlanoDB:
    return PlanoDB(
        id=row["id"],
        idoso_id=row["idoso_id"],
        perfil=row["perfil"],
        periodo=row["periodo"],
        pecas=json.loads(row["pecas"]),
        limites=json.loads(row["limites"]),
        autorizacoes=json.loads(row["autorizacoes"]),
        liberacoes=json.loads(row["liberacoes"]),
        escada=json.loads(row["escada"]),
        espera_min=row["espera_min"],
        definido_por=row["definido_por"],
        definido_em=row["definido_em"],
        versao=row["versao"],
    )
