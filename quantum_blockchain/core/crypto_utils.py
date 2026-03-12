from __future__ import annotations

from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def generate_keys() -> tuple[str, str]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


def load_private_key(private_pem: str) -> Any:
    return serialization.load_pem_private_key(
        private_pem.encode("utf-8"),
        password=None,
    )


def load_public_key(public_pem: str) -> Any:
    return serialization.load_pem_public_key(public_pem.encode("utf-8"))


def sign_transaction(private_pem: str, transaction: Any) -> str:
    private_key = load_private_key(private_pem)
    payload = transaction.signing_payload().encode("utf-8")
    signature = private_key.sign(payload, ec.ECDSA(hashes.SHA256()))
    transaction.signature = signature.hex()
    transaction.public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return transaction.signature


def verify_transaction(transaction: Any) -> bool:
    if not transaction.signature or not transaction.public_key:
        return False

    try:
        public_key = load_public_key(transaction.public_key)
        public_key.verify(
            bytes.fromhex(transaction.signature),
            transaction.signing_payload().encode("utf-8"),
            ec.ECDSA(hashes.SHA256()),
        )
        return True
    except (ValueError, InvalidSignature, TypeError):
        return False
