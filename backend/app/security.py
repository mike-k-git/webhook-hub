import hmac
from hashlib import sha256


def sign(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, sha256).hexdigest()


def verify(secret: str, body: bytes, provided: str | None) -> bool:
    if not provided:
        return False
    return hmac.compare_digest(sign(secret, body), provided)
