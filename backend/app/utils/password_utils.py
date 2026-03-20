import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def is_bcrypt_hash(hashed: str) -> bool:
    return isinstance(hashed, str) and hashed.startswith("$2")


def verify_password(password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False

    if is_bcrypt_hash(hashed_password):
        return pwd_context.verify(password, hashed_password)

    # Legacy SHA256 support
    if hashlib.sha256(password.encode()).hexdigest() == hashed_password:
        return True

    # Legacy MD5 support
    return hashlib.md5(password.encode()).hexdigest() == hashed_password


def needs_rehash(hashed_password: str) -> bool:
    return not is_bcrypt_hash(hashed_password)
