"""Reviewed publisher-key registry shared by package build and verification tools."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).parents[1]
REGISTRY_PATH = ROOT / "publishers" / "registry.json"
_KEY_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_STATUSES = {"active", "retiring", "revoked"}


class PublisherRegistryError(ValueError):
    """Raised when reviewed publisher metadata is malformed or unsafe."""


@dataclass(frozen=True)
class PublisherRecord:
    key_id: str
    publisher: str
    public_key: bytes
    status: str
    plugin_id_prefixes: tuple[str, ...]
    channel: str = "community"
    legacy_manifest_hashes: dict[str, list[str]] = field(default_factory=dict)

    def allows_plugin(self, plugin_id: str, *, release: bool = False) -> bool:
        allowed_statuses = {"active"} if release else {"active", "retiring"}
        return self.status in allowed_statuses and any(
            plugin_id.startswith(prefix) for prefix in self.plugin_id_prefixes
        )


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, PublisherRecord]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublisherRegistryError("publisher registry cannot be read") from exc
    if data.get("schema_version") != 1 or not isinstance(data.get("publishers"), list):
        raise PublisherRegistryError("publisher registry has an unsupported schema")

    records: dict[str, PublisherRecord] = {}
    for entry in data["publishers"]:
        if not isinstance(entry, dict):
            raise PublisherRegistryError("publisher registry contains an invalid record")
        key_id = entry.get("key_id")
        key_file = entry.get("public_key_file")
        encoded_key = entry.get("public_key_b64")
        digest = entry.get("public_key_sha256")
        status = entry.get("status")
        scopes = entry.get("plugin_id_prefixes")
        if (
            not isinstance(key_id, str)
            or not _KEY_ID.fullmatch(key_id)
            or not isinstance(key_file, str)
            or Path(key_file).name != key_file
            or not isinstance(encoded_key, str)
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or status not in _STATUSES
            or not isinstance(scopes, list)
            or not scopes
            or not all(isinstance(scope, str) and scope for scope in scopes)
        ):
            raise PublisherRegistryError("publisher registry contains invalid publisher metadata")
        if key_id in records:
            raise PublisherRegistryError("publisher registry contains duplicate key identifiers")
        try:
            public_key = base64.b64decode(encoded_key, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise PublisherRegistryError(
                "publisher registry contains invalid public-key encoding"
            ) from exc
        if len(public_key) != 32 or hashlib.sha256(public_key).hexdigest() != digest:
            raise PublisherRegistryError("publisher registry public-key digest does not match")
        try:
            file_key = base64.b64decode((path.parent / key_file).read_text().strip(), validate=True)
        except (OSError, ValueError, binascii.Error) as exc:
            raise PublisherRegistryError(
                "publisher registry public-key file cannot be read"
            ) from exc
        if file_key != public_key:
            raise PublisherRegistryError("publisher registry public-key file does not match")
        if entry.get("channel", "community") not in {"official", "demo", "community"}:
            raise PublisherRegistryError("invalid publisher channel")
        legacy = entry.get("legacy_manifest_hashes", {})
        if not isinstance(legacy, dict) or len(legacy) > 2048 or any(
            not re.fullmatch(r"[a-f0-9]{64}", key) or not isinstance(value, list) or not value or len(value) > 128
            or any(not isinstance(pin, str) or not re.fullmatch(r"[a-f0-9]{64}", pin) for pin in value) for key, value in legacy.items()
        ):
            raise PublisherRegistryError("invalid legacy manifest review pins")
        records[key_id] = PublisherRecord(
            key_id=key_id,
            publisher=str(entry.get("publisher", "")),
            public_key=public_key,
            status=status,
            plugin_id_prefixes=tuple(scopes),
            channel=entry.get("channel", "community"),
            legacy_manifest_hashes=legacy,
        )
    if not records:
        raise PublisherRegistryError("publisher registry must contain at least one key")
    return records


def release_signer(key_id: str, plugin_ids: tuple[str, ...], public_key: bytes) -> PublisherRecord:
    record = load_registry().get(key_id)
    if record is None or record.public_key != public_key:
        raise PublisherRegistryError("signing key is not registered")
    if not all(record.allows_plugin(plugin_id, release=True) for plugin_id in plugin_ids):
        raise PublisherRegistryError("signing key is inactive or outside the plugin scope")
    return record
