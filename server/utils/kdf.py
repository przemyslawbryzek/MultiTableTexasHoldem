import hashlib
import hmac
import random
import base64
import math

rng = random.SystemRandom()
n = 16384
ln = int(math.log2(n))
r = 8
p = 1
maxmem = 128 * n * r * p
saltlen = 32
hashlen = 32


def checksum(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode(),
        salt=salt,
        n=n,
        r=r,
        p=p,
        maxmem=maxmem,
        dklen=hashlen,
    )


def hash(password: str) -> str:
    salt = rng.randbytes(saltlen)
    h = checksum(password, salt)
    salt_b64 = base64.b64encode(salt).decode()
    h_b64 = base64.b64encode(h).decode()
    return f"$scrypt$ln={ln},r={r},p={p}${salt_b64}${h_b64}"


def verify(password: str, hash: str):
    items = hash.split("$")
    salt = base64.b64decode(items[3].encode())
    a = base64.b64decode(items[4].encode())
    b = checksum(password, salt)
    return hmac.compare_digest(a, b)
