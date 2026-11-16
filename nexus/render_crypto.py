"""Encrypt render inputs and outputs for the public GitHub Actions repository."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken


def _cipher(secret):
    if not secret:
        raise ValueError("CLOUDFLARE_API_TOKEN is required for render encryption.")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_text(value, secret):
    return _cipher(secret).encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_text(value, secret):
    try:
        return _cipher(secret).decrypt(value.encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Encrypted render manifest could not be decrypted.") from exc


def encrypt_bytes(value, secret):
    return _cipher(secret).encrypt(value)


def decrypt_bytes(value, secret):
    try:
        return _cipher(secret).decrypt(value)
    except InvalidToken as exc:
        raise ValueError("Encrypted render artifact could not be decrypted.") from exc
