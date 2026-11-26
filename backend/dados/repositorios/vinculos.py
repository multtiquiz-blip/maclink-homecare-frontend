"""
Repositório de vínculos pessoa ↔ paciente.

Um vínculo diz que o usuário tem acesso ao paciente naquele papel.
Origem: 'codigo' (compartilhamento), 'convite', 'criacao'.
"""

import sqlite3
import time


def criar(
    conn: sqlite3.Connection,
    *,
    id: str,
    usuario_id: str,
    paciente_id: str,
    papel: str,
    vinculado_por: str,
    origem: str = "codigo",
) -> str:
    agora = int(time.time())
    conn.execute(
        """
        INSERT INTO vinculos_paciente (
            id, usuario_id, paciente_id, papel, vinculado_por, origem,
            ativo, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (id, usuario_id, paciente_id, papel, vinculado_por, origem, agora),
    )
    conn.commit()
    return id


def tem_vinculo(
    conn: sqlite3.Connection, usuario_id: str, paciente_id: str
) -> bool:
    row = conn.execute(
        """
        SELECT 1 FROM vinculos_paciente
        WHERE usuario_id = ? AND paciente_id = ? AND ativo = 1
        LIMIT 1
        """,
        (usuario_id, paciente_id),
    ).fetchone()
    return row is not None


def listar_pacientes_do_usuario(
    conn: sqlite3.Connection, usuario_id: str
) -> list:
    """Retorna lista de ids de pacientes vinculados ao usuário."""
    rows = conn.execute(
        """
        SELECT paciente_id FROM vinculos_paciente
        WHERE usuario_id = ? AND ativo = 1
        ORDER BY criado_em ASC
        """,
        (usuario_id,),
    ).fetchall()
    return [r["paciente_id"] for r in rows]
