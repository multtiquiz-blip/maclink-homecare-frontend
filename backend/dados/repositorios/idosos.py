"""
Repositório de idosos (pacientes).
"""

import sqlite3
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class IdosoDB:
    id: str
    nome: str
    idade: Optional[int]
    quarto: Optional[str]
    alergia: Optional[str]
    dieta: Optional[str]
    obs: Optional[str]


def criar(
    conn: sqlite3.Connection,
    *,
    id: str,
    nome: str,
    idade: Optional[int] = None,
    quarto: Optional[str] = None,
    alergia: Optional[str] = None,
    dieta: Optional[str] = None,
    obs: Optional[str] = None,
) -> str:
    """Cria um paciente. Retorna o id."""
    agora = int(time.time())
    conn.execute(
        """
        INSERT INTO idosos (id, nome, idade, quarto, alergia, dieta, obs, criado_em)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (id, nome, idade, quarto, alergia, dieta, obs, agora),
    )
    conn.commit()
    return id


def buscar(conn: sqlite3.Connection, idoso_id: str) -> Optional[IdosoDB]:
    row = conn.execute(
        "SELECT * FROM idosos WHERE id = ?", (idoso_id,)
    ).fetchone()
    if row is None:
        return None
    return _linha(row)


def listar_por_ids(conn: sqlite3.Connection, ids: list) -> list:
    """Lista pacientes a partir de uma lista de ids, na ordem dada."""
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT * FROM idosos WHERE id IN ({placeholders})", ids
    ).fetchall()
    por_id = {r["id"]: _linha(r) for r in rows}
    return [por_id[i] for i in ids if i in por_id]


def _linha(row: sqlite3.Row) -> IdosoDB:
    return IdosoDB(
        id=row["id"],
        nome=row["nome"],
        idade=row["idade"],
        quarto=row["quarto"],
        alergia=row["alergia"],
        dieta=row["dieta"],
        obs=row["obs"],
    )
