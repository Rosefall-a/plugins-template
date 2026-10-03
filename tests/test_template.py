"""Developer acceptance and rejection tests against real generated packages."""
import base64
import json
import os
import shutil
import subprocess
import sys
import zipfile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.distribution import ROOT, catalogue_base


def run(root, *args, env=None, ok=True):
    result = subprocess.run([sys.executable, *args], cwd=root, env=env, text=True, capture_output=True)
    if ok:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode != 0, result.stdout + result.stderr
    return result


def commit(root, message):
    for args in (("add", "."), ("commit", "-m", message)):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def independent(tmp_path):
    root = tmp_path / "fork"
    shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", ".validation", "__pycache__", ".pytest_cache", ".ruff_cache", "dist", "releases", "list.json", "plugins", "*.b64"))
    (root / "publishers/registry.json").write_text(json.dumps({"schema_version": 1, "publishers": []}))
    run(root, "tools/new_plugin.py", "hello-world", "--id", "yourname.hello-world", "--name", "Hello World", "--publisher", "Your Name")
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    for name, value in (("user.name", "Developer"), ("user.email", "developer@example.invalid")):
        subprocess.run(["git", "-C", str(root), "config", name, value], check=True)
    env = {k: v for k, v in os.environ.items() if not k.startswith("PLUGIN_SIGNING")}
    return root, env


def package(root, plugin_id="yourname.hello-world"):
    entries = json.loads((root / "list.json").read_text())["plugins"]
    entry = next(e for e in entries if e["plugin_id"] == plugin_id)
    return root / "dist" / entry["package"]["filename"]


def test_unsigned_empty_registry_build(independent):
    from tools.validate_packages import validate_package
    from tools.verify_packages import verify_package
    root, env = independent
    run(root, "tools/build_packages.py", env=env)
    for path in (root / ".validation/dist").glob("*.utp"):
        validate_package(path, full=True)
        verify_package(path)
        with pytest.raises(ValueError, match="requires a publisher signature"):
            verify_package(path, require_signature=True)


def test_current_source_packages_validate(current_packages):
    from tools.validate_packages import validate_package
    from tools.verify_packages import verify_package
    for path in current_packages.values():
        validate_package(path, full=True)
        verify_package(path)


def test_greeting_uses_public_protocol(independent):
    import importlib.util
    spec = importlib.util.spec_from_file_location("hello", independent[0] / "plugins/hello-world/plugin.py")
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)
    assert plugin.greet({}) == {"message": "Hello, world!"}
    assert plugin.greet({"name": "Developer"}) == {"message": "Hello, Developer!"}
    assert plugin.greet({"name": " "}) == {"message": "Hello, world!"}


def test_fresh_developer_signed_releases_and_immutable_history(independent, tmp_path):
    root, env = independent
    run(root, "tools/new_plugin.py", "my-plugin", "--id", "yourname.my-plugin", "--name", "My Plugin", "--publisher", "Your Name")
    feature = root / "plugins/my-plugin/plugin.py"
    feature.write_text(feature.read_text().replace('Hello, {name}!', 'Welcome, {name}!'))
    run(root, "tools/check_source_layout.py")
    run(root, "tools/build_packages.py", env=env)
    run(root, "tools/create_signing_identity.py", "--key-directory", str(tmp_path / "keys"),
        "--key-id", "developer-1", "--publisher", "Your Name", "--prefix", "yourname.")
    env.update(PLUGIN_SIGNING_KEY_ID="developer-1", PLUGIN_SIGNING_KEY_B64=(tmp_path / "keys/developer-1.private-seed.b64").read_text())
    commit(root, "feat: create my first plugin")
    run(root, "tools/build_packages.py", "--publish", env=env)
    first = package(root, "yourname.my-plugin")
    original = first.read_bytes()
    run(root, "tools/verify_packages.py", str(first), env=env)
    run(root, "tools/distribution.py", "--check-source", env=env)
    commit(root, "chore: publish initial packages")
    baseline = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    manifest_path = root / "plugins/my-plugin/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["version"] = "0.2.0"
    manifest_path.write_text(json.dumps(manifest))
    feature.write_text(feature.read_text().replace('Welcome, {name}!', 'Welcome back, {name}!'))
    commit(root, "feat: improve my greeting")
    run(root, "tools/build_packages.py", "--publish", env=env)
    assert package(root, "yourname.my-plugin").name == "yourname.my-plugin-0.2.0.utp"
    assert first.read_bytes() == original
    run(root, "tools/distribution.py", "--baseline-ref", baseline, env=env)
    commit(root, "chore: publish second release")
    run(root, "tools/build_packages.py", "--publish", "--reuse-published", env=env)
    assert first.read_bytes() == original
    # Conventional Commit version policy remains the upstream policy.
    feature.write_text(feature.read_text() + "\n# A backwards-compatible fix.\n")
    commit(root, "fix: clarify greeting")
    run(root, "tools/build_packages.py", "--publish", env=env)
    assert package(root, "yourname.my-plugin").name == "yourname.my-plugin-0.2.1.utp"


def test_signing_rejects_invalid_key_scope_and_publisher(independent, tmp_path):
    root, env = independent
    run(root, "tools/create_signing_identity.py", "--key-directory", str(tmp_path / "keys"),
        "--key-id", "developer-1", "--publisher", "Your Name", "--prefix", "different.")
    env.update(PLUGIN_SIGNING_KEY_ID="developer-1", PLUGIN_SIGNING_KEY_B64=(tmp_path / "keys/developer-1.private-seed.b64").read_text())
    commit(root, "feat: configure signing")
    assert "outside the plugin scope" in run(root, "tools/build_packages.py", env=env, ok=False).stderr
    registry = root / "publishers/registry.json"
    data = json.loads(registry.read_text())
    data["publishers"][0]["plugin_id_prefixes"] = ["yourname."]
    data["publishers"][0]["publisher"] = "Different publisher"
    registry.write_text(json.dumps(data))
    assert "publisher does not match" in run(root, "tools/build_packages.py", env=env, ok=False).stderr
    env["PLUGIN_SIGNING_KEY_B64"] = base64.b64encode(Ed25519PrivateKey.generate().private_bytes_raw()).decode()
    assert "signing key is not registered" in run(root, "tools/build_packages.py", env=env, ok=False).stderr


@pytest.mark.parametrize("field,value", [("plugin_id", "BAD ID"), ("version", "01.2.3"), ("entrypoint", "missing:main"), ("sdk_version_range", "banana")])
def test_invalid_source_fails(independent, field, value):
    root, env = independent
    path = root / "plugins/hello-world/manifest.json"
    data = json.loads(path.read_text())
    data[field] = value
    path.write_text(json.dumps(data))
    run(root, "tools/check_source_layout.py", env=env, ok=False)
    run(root, "tools/build_packages.py", env=env, ok=False)


def test_duplicate_ids_and_incomplete_plugins_fail(independent):
    root, env = independent
    shutil.copytree(root / "plugins/hello-world", root / "plugins/duplicate")
    assert "duplicate plugin_id" in run(root, "tools/build_packages.py", env=env, ok=False).stderr
    shutil.rmtree(root / "plugins/duplicate")
    (root / "plugins/incomplete").mkdir()
    assert "manifest.json is missing" in run(root, "tools/build_packages.py", env=env, ok=False).stderr


def test_signature_binds_payload_and_manifest(independent, tmp_path):
    root, env = independent
    run(root, "tools/create_signing_identity.py", "--key-directory", str(tmp_path / "keys"),
        "--key-id", "developer-1", "--publisher", "Your Name", "--prefix", "yourname.")
    env.update(PLUGIN_SIGNING_KEY_ID="developer-1", PLUGIN_SIGNING_KEY_B64=(tmp_path / "keys/developer-1.private-seed.b64").read_text())
    run(root, "tools/build_packages.py", env=env)
    signed = next((root / ".validation/dist").glob("*.utp"))
    with zipfile.ZipFile(signed) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    for name in ("manifest.json", "payload/plugin.py"):
        modified = dict(entries)
        if name == "manifest.json":
            manifest = json.loads(modified[name])
            manifest["name"] = "Forged identity"
            modified[name] = json.dumps(manifest).encode()
        else:
            modified[name] += b"\n# changed bytes\n"
        corrupt = tmp_path / "corrupt.utp"
        with zipfile.ZipFile(corrupt, "w") as archive:
            for key, value in modified.items():
                archive.writestr(key, value)
        run(root, "tools/verify_packages.py", str(corrupt), env=env, ok=False)
    # Altering a signature itself must also fail cryptographic verification.
    manifest = json.loads(entries["manifest.json"])
    manifest["integrity"]["signature"] = "v2:" + base64.b64encode(bytes(64)).decode()
    entries["manifest.json"] = json.dumps(manifest).encode()
    with zipfile.ZipFile(tmp_path / "bad-signature.utp", "w") as archive:
        for key, value in entries.items():
            archive.writestr(key, value)
    run(root, "tools/verify_packages.py", str(tmp_path / "bad-signature.utp"), env=env, ok=False)


def test_catalogue_uses_own_fork(independent, monkeypatch):
    root, _ = independent
    monkeypatch.setenv("GITHUB_REPOSITORY", "developer/personal-plugins")
    monkeypatch.setenv("PLUGIN_CATALOGUE_BRANCH", "stable")
    assert catalogue_base(root, {"base_url": "auto"}) == "https://raw.githubusercontent.com/developer/personal-plugins/stable"
    assert catalogue_base(root, {"base_url": "https://plugins.example.org/"}) == "https://plugins.example.org"


def test_template_has_no_official_assets():
    assert not any((ROOT / name).exists() for name in ("wiki", "examples", "official"))
    assert all(p.get("channel", "community") == "community" for p in json.loads((ROOT / "publishers/registry.json").read_text())["publishers"])
