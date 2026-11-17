"""Encrypt render inputs and outputs for the public GitHub Actions repository."""
import base64
import hashlib
import zlib

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


def encrypt_compressed_text(value, secret):
    """Compress JSON/text before encryption to fit GitHub workflow input limits."""
    compressed = zlib.compress(value.encode("utf-8"), level=9)
    return encrypt_bytes(compressed, secret).decode("ascii")


def decrypt_compressed_text(value, secret):
    """Decrypt and decompress a manifest produced by encrypt_compressed_text."""
    try:
        payload = decrypt_bytes(value.encode("ascii"), secret)
        return zlib.decompress(payload).decode("utf-8")
    except (zlib.error, UnicodeDecodeError) as exc:
        raise ValueError("Compressed render manifest is invalid or corrupted.") from exc
