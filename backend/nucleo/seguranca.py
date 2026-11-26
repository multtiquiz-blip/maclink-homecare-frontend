"""
Segurança do PIN e das credenciais locais.

Regra dura: PIN NUNCA é guardado em texto puro.
Sempre SHA-256(salt + pin), com salt aleatório por usuário.

Não usamos bcrypt/argon2 porque o SQLite roda no tablet e
queremos zero dependências nativas no piloto. SHA-256 com salt
é adequado para PIN de 4 dígitos (o espaço de busca é pequeno,
mas o salt impede rainbow table e o bloqueio por tentativas
impede força bruta online).
"""

import hashlib
import secrets


def gerar_salt(tamanho_bytes: int = 16) -> str:
    """Gera um salt aleatório em hex."""
    return secrets.token_hex(tamanho_bytes)


def hash_pin(pin: str, salt: str) -> str:
    """
    Gera o hash do PIN.

    Formato: SHA-256(salt + pin), em hex.
    O salt vem antes para evitar que PINs iguais gerem hashes iguais.
    """
    if not pin or not salt:
        raise ValueError("PIN e salt são obrigatórios")
    dados = (salt + pin).encode("utf-8")
    return hashlib.sha256(dados).hexdigest()


def verificar_pin(pin: str, salt: str, hash_armazenado: str) -> bool:
    """
    Verifica o PIN contra o hash armazenado.

    Comparação em tempo constante para evitar timing attack.
    """
    if not pin or not salt or not hash_armazenado:
        return False
    calculado = hash_pin(pin, salt)
    return secrets.compare_digest(calculado, hash_armazenado)


def pin_valido(pin: str) -> bool:
    """
    Valida o formato do PIN.

    Regras: exatamente 4 dígitos numéricos.
    """
    if not pin:
        return False
    return len(pin) == 4 and pin.isdigit()
