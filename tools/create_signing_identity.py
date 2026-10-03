"""Generate a developer-owned Ed25519 identity; never print its private seed."""
import argparse
import base64
import hashlib
import json
import os
import re
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).resolve().parents[1]


def create(directory: Path, key_id: str, publisher: str, prefix: str) -> None:
    directory = directory.resolve()
    if directory.is_relative_to(ROOT):
        raise ValueError("private-key directory must be outside the checkout")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", key_id):
        raise ValueError("invalid signing key ID")
    if not publisher.strip() or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*\.", prefix):
        raise ValueError("publisher and an owned namespace ending in '.' are required")
    registry_path = ROOT / "publishers/registry.json"
    registry = json.loads(registry_path.read_text())
    if any(item["key_id"] == key_id for item in registry["publishers"]):
        raise ValueError("key ID already registered; rotation needs a new ID")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    private_path = directory / f"{key_id}.private-seed.b64"
    public_path = ROOT / "publishers" / f"{key_id}.public-key.b64"
    if private_path.exists() or public_path.exists():
        raise ValueError("refusing to overwrite a key")
    key = Ed25519PrivateKey.generate()
    descriptor = os.open(private_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="ascii") as stream:
        stream.write(base64.b64encode(key.private_bytes_raw()).decode())
    public = key.public_key().public_bytes_raw()
    encoded = base64.b64encode(public).decode()
    public_path.write_text(encoded + "\n", encoding="ascii")
    registry["publishers"].append({"key_id": key_id, "publisher": publisher,
        "public_key_file": public_path.name, "public_key_b64": encoded,
        "public_key_sha256": hashlib.sha256(public).hexdigest(), "status": "active",
        "plugin_id_prefixes": [prefix], "channel": "community"})
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    print(f"Created public registry entry {key_id}; private seed saved outside Git.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-directory", required=True, type=Path)
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--publisher", required=True)
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()
    create(args.key_directory, args.key_id, args.publisher, args.prefix)
