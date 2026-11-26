"""
Repositorio da tabela `auditoria`.

Existe para que tentativa negada nao passe em silencio.
Nada aqui se apaga: este modulo so faz INSERT e SELECT.
Nao existe funcao de delete nem de update.

Usa a tabela `auditoria` que ja existe em dados/esquema.sql:
    id, ts, usuario_id, usuario_nome, acao, detalhe, negado
"""

import sqlite3
import time
import uuid
from typing import Optional


def registrar(
    conn: sqlite3.Connection,
    *,
    acao: str,
    detalhe: str = "",
    usuario_id: Optional[str] = None,
    usuario_nome: Optional[str] = None,
    negado: bool = False,
    ts: Optional[int] = None,
) -> str:
    """
    Grava um evento de auditoria. Retorna o id criado.

    `usuario_id` pode ser None de proposito: emergencia e tentativa
    anonima tambem precisam ficar registradas.
    """
    if not acao:
        raise ValueError("acao e obrigatoria na auditoria")
    novo_id = f"au_{uuid.uuid4().hex[:12]}"
    conn.execute(
        """
        INSERT INTO auditoria (id, ts, usuario_id, usuario_nome, acao, detalhe, negado)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            novo_id,
            int(ts if ts is not None else time.time()),
            usuario_id,
            usuario_nome,
            acao,
            detalhe,
            1 if negado else 0,
        ),
    )
    conn.commit()
    return novo_id


def listar(
    conn: sqlite3.Connection,
    *,
    apenas_negados: bool = False,
    limite: int = 100,
) -> list:
    """Lista eventos do mais recente para o mais antigo."""
    sql = "SELECT * FROM auditoria"
    if apenas_negados:
        sql += " WHERE negado = 1"
    sql += " ORDER BY ts DESC, rowid DESC LIMIT ?"
    return [
        {
            "id": r["id"],
            "ts": r["ts"],
            "usuario_id": r["usuario_id"],
            "usuario_nome": r["usuario_nome"],
            "acao": r["acao"],
            "detalhe": r["detalhe"],
            "negado": bool(r["negado"]),
        }
        for r in conn.execute(sql, (limite,)).fetchall()
    ]
