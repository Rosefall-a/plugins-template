"""Verify packages with the real host; optionally exercise its Linux workers."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from uuid import uuid4


def check(host: Path, distribution: Path, lifecycle: bool = False) -> None:
    sys.path.insert(0, str(host / "src/backend"))
    sys.path.insert(0, str(host / "src/plugin-runtime"))
    from runtime import PluginRegistry, PluginSupervisor, RuntimePolicyError
    from src.plugin_api.contracts import PluginManifest, PluginUiDocument
    from src.plugin_api.updates import PluginPackageVerifier, TrustedPublisher
    try:
        from .distribution import ROOT
        from .publisher_registry import load_registry
    except ImportError:
        from distribution import ROOT
        from publisher_registry import load_registry
    registry_data = json.loads((ROOT / "publishers/registry.json").read_text())
    records = load_registry() if registry_data["publishers"] else {}
    publishers = {key: TrustedPublisher(key_id=key, public_key=record.public_key,
        publisher=record.publisher, status=record.status, plugin_id_prefixes=record.plugin_id_prefixes,
        channel=record.channel, require_manifest_binding=True) for key, record in records.items()}
    if lifecycle and os.name != "posix":
        raise ValueError("real worker lifecycle requires Linux; run the blocking CI job")
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        supervisor = PluginSupervisor(work / "workers", work / "storage")
        registry = PluginRegistry(work / "installed", supervisor)
        if lifecycle:
            supervisor.probe_isolation()
        try:
            for package in sorted((distribution / "dist").glob("*.utp")):
                inspection = PluginPackageVerifier(publishers, require_signature=False).inspect(package)
                manifest = inspection.manifest
                PluginManifest.model_validate(manifest.model_dump())
                plugin_id = manifest.plugin_id
                identity = str(uuid4())
                operation = str(uuid4())
                registry.install_package(package.read_bytes(), package.name,
                    installation_id=identity, operation_id=operation)
                PluginUiDocument.model_validate(registry.ui(plugin_id))
                assert not next(p for p in registry.list() if p["plugin_id"] == plugin_id)["enabled"]
                if lifecycle and plugin_id == "yourname.hello-world":
                    try:
                        registry.start(plugin_id)
                    except RuntimePolicyError as exc:
                        assert "permission commit" in str(exc)
                    else:
                        raise AssertionError("uncommitted installation started")
                    registry.finish_installation(plugin_id, operation, commit=True)
                    registry.start(plugin_id)
                    deadline = time.monotonic() + 10
                    while not registry.health(plugin_id) and time.monotonic() < deadline:
                        time.sleep(0.05)
                    assert registry.health(plugin_id), registry.diagnostics(plugin_id)
                    registry.finish_activation(plugin_id, operation, commit=True)
                    assert registry.action(plugin_id, "greet", {"name": "Developer"}) == {"message": "Hello, Developer!"}
                    registry.storage_put(plugin_id, "sentinel", "preserved")
                    registry.stop(plugin_id)
                    registry.start(plugin_id)
                    assert registry.health(plugin_id)
                    # Build a new version and changed feature with the actual builder.
                    update_root = work / "update-source"
                    for directory in ("tools", "sdk"):
                        shutil.copytree(ROOT / directory, update_root / directory,
                            ignore=shutil.ignore_patterns("__pycache__"))
                    (update_root / "publishers").mkdir()
                    (update_root / "publishers/registry.json").write_text(json.dumps({"schema_version": 1, "publishers": []}))
                    source = update_root / "plugins/hello-world"
                    source.mkdir(parents=True)
                    with zipfile.ZipFile(package) as archive:
                        for name in archive.namelist():
                            if not name.startswith("payload/") or name.endswith("/"):
                                continue
                            relative = name.removeprefix("payload/")
                            if relative.startswith("sdk/") or relative in {"distribution.json", "package-signature-v2.json"}:
                                continue
                            target = source / relative
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_bytes(archive.read(name))
                    updated = manifest.model_dump(mode="json")
                    major, minor, patch = map(int, manifest.version.split("."))
                    updated["version"] = f"{major}.{minor}.{patch + 1}"
                    updated["integrity"] = {"sha256": "0" * 64, "signature": None, "key_id": None}
                    (source / "manifest.json").write_text(json.dumps(updated))
                    feature = source / "plugin.py"
                    feature.write_text(feature.read_text().replace('Hello, {name}!', 'Welcome, {name}!'))
                    environment = {key: value for key, value in os.environ.items() if not key.startswith("PLUGIN_SIGNING")}
                    subprocess.run([sys.executable, str(update_root / "tools/build_packages.py")], env=environment, check=True)
                    candidate = next((update_root / ".validation/dist").glob("*.utp"))
                    PluginPackageVerifier({}, require_signature=False).inspect(candidate)
                    operation = str(uuid4())
                    registry.install_package(candidate.read_bytes(), candidate.name, installation_id=identity,
                        operation_id=operation, replace=True, expected_version=manifest.version)
                    registry.finish_installation(plugin_id, operation, commit=True)
                    registry.start(plugin_id)
                    assert registry.health(plugin_id)
                    registry.finish_activation(plugin_id, operation, commit=True)
                    assert registry.package(plugin_id)[1]["version"] == updated["version"]
                    assert registry.action(plugin_id, "greet", {"name": "Developer"}) == {"message": "Welcome, Developer!"}
                    assert supervisor._storage(plugin_id).get("sentinel") == b"preserved"
                    registry.stop(plugin_id)
                    print(f"{plugin_id}: Linux worker ready/action/disable/re-enable/new-version update passed")
                registry.delete(plugin_id)
                assert not registry.list()
                print(f"{package.name}: real host manifest/UI/verifier/install/uninstall passed")
        finally:
            supervisor.stop_all()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-root", required=True, type=Path)
    parser.add_argument("--distribution-root", type=Path, default=Path(__file__).resolve().parents[1] / ".validation")
    parser.add_argument("--lifecycle", action="store_true")
    args = parser.parse_args()
    check(args.host_root.resolve(), args.distribution_root.resolve(), args.lifecycle)
