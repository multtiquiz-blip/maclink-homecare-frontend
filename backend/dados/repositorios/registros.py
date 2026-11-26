"""
Repositório de registros.

Regra dura: registro NÃO se apaga. Se corrige com motivo.
"""

import sqlite3
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class RegistroDB:
    id: str
    idoso_id: str
    dia: str
    ts: int
    tipo: str
    texto: Optional[str]
    valor: Optional[str]
    autor_id: Optional[str]
    autor_nome: str
    autor_papel: str
    limite_vigente: Optional[str]  # snapshot JSON dos limites no momento
    corrigido: bool
    excluido: bool


def criar(
    conn: sqlite3.Connection,
    *,
    id: str,
    idoso_id: str,
    dia: str,
    tipo: str,
    autor_id: str,
    autor_nome: str,
    autor_papel: str,
    texto: Optional[str] = None,
    valor: Optional[str] = None,
    autor_coren: Optional[str] = None,
    limite_vigente: Optional[str] = None,
    vinculo_reafericao: Optional[str] = None,
) -> str:
    agora = int(time.time())
    conn.execute(
        """
        INSERT INTO registros (
            id, idoso_id, dia, ts, tipo, texto, valor,
            autor_id, autor_nome, autor_papel, autor_coren,
            limite_vigente, vinculo_reafericao, corrigido, excluido
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
        """,
        (
            id, idoso_id, dia, agora, tipo, texto, valor,
            autor_id, autor_nome, autor_papel, autor_coren,
            limite_vigente, vinculo_reafericao,
        ),
    )
    conn.commit()
    return id


def buscar(conn: sqlite3.Connection, registro_id: str) -> Optional[RegistroDB]:
    row = conn.execute(
        "SELECT * FROM registros WHERE id = ?", (registro_id,)
    ).fetchone()
    if row is None:
        return None
    return _linha_para_registro(row)


def listar_por_dia(
    conn: sqlite3.Connection, idoso_id: str, dia: str
) -> list:
    rows = conn.execute(
        """
        SELECT * FROM registros
        WHERE idoso_id = ? AND dia = ? AND excluido = 0
        ORDER BY ts ASC
        """,
        (idoso_id, dia),
    ).fetchall()
    return [_linha_para_registro(r) for r in rows]


def corrigir(
    conn: sqlite3.Connection,
    *,
    registro_id: str,
    motivo: str,
    autor_id: str,
    autor_nome: str,
    novo_texto: Optional[str] = None,
    novo_valor: Optional[str] = None,
) -> None:
    if not motivo or not motivo.strip():
        raise ValueError("Motivo da correção é obrigatório")
    original = conn.execute(
        "SELECT texto, valor FROM registros WHERE id = ?", (registro_id,)
    ).fetchone()
    if original is None:
        raise ValueError(f"Registro {registro_id} não encontrado")
    agora = int(time.time())
    conn.execute(
        """
        INSERT INTO registros_historico (
            id, registro_id, ts, autor_id, autor_nome, motivo,
            antes_texto, antes_valor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"h_{registro_id}_{agora}",
            registro_id, agora, autor_id, autor_nome, motivo,
            original["texto"], original["valor"],
        ),
    )
    campos = []
    params = []
    if novo_texto is not None:
        campos.append("texto = ?")
        params.append(novo_texto)
    if novo_valor is not None:
        campos.append("valor = ?")
        params.append(novo_valor)
    campos.append("corrigido = 1")
    params.append(registro_id)
    conn.execute(
        f"UPDATE registros SET {', '.join(campos)} WHERE id = ?", params
    )
    conn.commit()


def excluir_nunca(conn: sqlite3.Connection, registro_id: str) -> None:
    raise NotImplementedError(
        "Registros não se apagam. Use corrigir() com motivo."
    )


def _linha_para_registro(row: sqlite3.Row) -> RegistroDB:
    return RegistroDB(
        id=row["id"],
        idoso_id=row["idoso_id"],
        dia=row["dia"],
        ts=row["ts"],
        tipo=row["tipo"],
        texto=row["texto"],
        valor=row["valor"],
        autor_id=row["autor_id"],
        autor_nome=row["autor_nome"],
        autor_papel=row["autor_papel"],
        limite_vigente=row["limite_vigente"],
        corrigido=bool(row["corrigido"]),
        excluido=bool(row["excluido"]),
    )
