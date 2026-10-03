"""Select independently scoped signers; never silently downgrade a configured key."""
from __future__ import annotations

import base64
import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
try:
    from .publisher_registry import PublisherRegistryError, release_signer
except ImportError:
    from publisher_registry import PublisherRegistryError, release_signer


def select_signer(root: Path, source: Path, plugin_id: str, *, required: bool):
    folder = source.relative_to(root).parts[0]
    prefix = "PLUGIN_SIGNING"
    fallback = os.getenv("PLUGIN_SIGNING_FALLBACK", "generic").strip()
    if fallback not in {"generic", "unsigned", "error"}:
        raise ValueError("PLUGIN_SIGNING_FALLBACK must be generic, unsigned or error")
    key_id = os.getenv(prefix + "_KEY_ID", "").strip()
    encoded = os.getenv(prefix + "_KEY_B64", "").strip()
    if bool(key_id) != bool(encoded):
        raise ValueError(f"{prefix}: both KEY_ID and KEY_B64 are required")
    if not encoded:
        if required or fallback == "error":
            raise ValueError(f"{folder}/{source.name}: a registered signing key is required for publication")
        return None, None
    try:
        key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(encoded, validate=True))
    except ValueError as exc:
        raise ValueError(f"{prefix}: invalid Ed25519 seed") from exc
    try:
        record = release_signer(key_id, (plugin_id,), key.public_key().public_bytes_raw())
    except PublisherRegistryError as exc:
        raise PublisherRegistryError(
            f"{source.relative_to(root).as_posix()}: {prefix} identity rejected: {exc}. "
            "Register the matching public key, channel and plugin scope in "
            "publishers/registry.json and the host trusted_publishers.json; "
            "adding Actions secrets alone does not register a publisher. "
            "Configured invalid identities are not silently replaced."
        ) from exc
    if record.channel != "community":
        raise ValueError("independent sources require a community signing identity")
    return key, key_id
