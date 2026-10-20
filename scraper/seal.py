"""Password encryption for site/data.js (AES-256-GCM, key from PBKDF2-SHA256).

The browser decrypts with WebCrypto using the same parameters (see site/index.html).
Passwords live in secrets.env next to the project root, which is never committed.
"""
import base64
import json
import os
import secrets

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 310_000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS = os.path.join(ROOT, "secrets.env")


def load_passwords():
    """Return (catalog_password, admin_password); create secrets.env with random ones on first run."""
    if not os.path.exists(SECRETS):
        with open(SECRETS, "w") as f:
            f.write("# Passwords for the catalog. Change them here, then run scripts/update.sh.\n")
            f.write(f"CATALOG_PASSWORD={secrets.token_urlsafe(9)}\n")
            f.write(f"ADMIN_PASSWORD={secrets.token_urlsafe(12)}\n")
        os.chmod(SECRETS, 0o600)
        print(f"Created {SECRETS} with new passwords.")
    values = {}
    with open(SECRETS) as f:
        for line in f:
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    catalog, admin = values.get("CATALOG_PASSWORD"), values.get("ADMIN_PASSWORD")
    if not catalog or not admin:
        raise SystemExit("secrets.env must define CATALOG_PASSWORD and ADMIN_PASSWORD")
    if catalog == admin:
        raise SystemExit("CATALOG_PASSWORD and ADMIN_PASSWORD must be different")
    return catalog, admin


def encrypt(obj, password):
    b64 = lambda b: base64.b64encode(b).decode()  # noqa: E731
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS).derive(password.encode())
    ct = AESGCM(key).encrypt(iv, json.dumps(obj, ensure_ascii=False).encode(), None)
    return {"v": 1, "iter": ITERATIONS, "salt": b64(salt), "iv": b64(iv), "ct": b64(ct)}
