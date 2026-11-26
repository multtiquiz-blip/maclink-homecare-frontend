"""
Repositório de usuários.

Operações sobre a tabela `usuarios`. Toda senha/PIN passa por
`nucleo/seguranca.py` — nunca é guardada em texto puro.
"""

import sqlite3
import time
from dataclasses import dataclass
from typing import Optional

from backend.nucleo.seguranca import gerar_salt, hash_pin, pin_valido, verificar_pin


@dataclass
class UsuarioDB:
    id: str
    nome: str
    papel: str
    categoria: Optional[str]
    coren: Optional[str]
    verificado: bool
    telefone: Optional[str]
    email: Optional[str]
    ativo: bool
    criado_em: int


def criar(
    conn: sqlite3.Connection,
    *,
    id: str,
    nome: str,
    papel: str,
    pin: str,
    categoria: Optional[str] = None,
    coren: Optional[str] = None,
    verificado: bool = False,
    telefone: Optional[str] = None,
    email: Optional[str] = None,
) -> str:
    """
    Cria um usuário.

    Levanta ValueError se o PIN for inválido.
    Retorna o id criado.
    """
    if not pin_valido(pin):
        raise ValueError("PIN deve ter exatamente 4 dígitos numéricos")

    salt = gerar_salt()
    pin_hash = hash_pin(pin, salt)
    agora = int(time.time())

    conn.execute(
        """
        INSERT INTO usuarios (
            id, nome, papel, categoria, coren, verificado,
            pin_hash, pin_salt, telefone, email, ativo, criado_em
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            id, nome, papel, categoria, coren, 1 if verificado else 0,
            pin_hash, salt, telefone, email, agora,
        ),
    )
    conn.commit()
    return id


def buscar(conn: sqlite3.Connection, usuario_id: str) -> Optional[UsuarioDB]:
    """Busca um usuário por id."""
    row = conn.execute(
        "SELECT * FROM usuarios WHERE id = ? AND ativo = 1",
        (usuario_id,),
    ).fetchone()
    if row is None:
        return None
    return _linha_para_usuario(row)


def autenticar(conn: sqlite3.Connection, usuario_id: str, pin: str) -> bool:
    """
    Verifica o PIN do usuário.

    Retorna True só se o usuário existe, está ativo e o PIN confere.
    """
    row = conn.execute(
        "SELECT pin_hash, pin_salt FROM usuarios WHERE id = ? AND ativo = 1",
        (usuario_id,),
    ).fetchone()
    if row is None:
        return False
    return verificar_pin(pin, row["pin_salt"], row["pin_hash"])


def _linha_para_usuario(row: sqlite3.Row) -> UsuarioDB:
    return UsuarioDB(
        id=row["id"],
        nome=row["nome"],
        papel=row["papel"],
        categoria=row["categoria"],
        coren=row["coren"],
        verificado=bool(row["verificado"]),
        telefone=row["telefone"],
        email=row["email"],
        ativo=bool(row["ativo"]),
        criado_em=row["criado_em"],
    )
