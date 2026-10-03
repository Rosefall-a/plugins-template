"""Shared Plugin Package v1 canonical payload format helpers."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable


def canonical_payload_digest(entries: Iterable[tuple[str, bytes]]) -> str:
    """Return the v1 digest over sorted payload paths and raw bytes."""
    digest = hashlib.sha256()
    for name, content in sorted(entries):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


SIGNATURE_ENVELOPE = "package-signature-v2.json"


def signature_message(digest: str, version: int = 2) -> bytes:
    return f"plugin-package-v{version}:{digest}".encode("ascii")


def signature_envelope(manifest: dict, key_id: str | None) -> dict:
    return {"schema_version": 2, "key_id": key_id,
            "manifest": {k: v for k, v in manifest.items() if k != "integrity"}}
