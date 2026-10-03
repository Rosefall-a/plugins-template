"""Linux acceptance against a disposable migrated PostgreSQL host, with real HTTP grants.

Requires host backend dependencies and POSTGRES_* pointing to an empty disposable
database. Builds a fresh independent plugin, never an upstream example.
"""
import argparse
import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ID = "acceptance.greeting"


def port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def server(host: Path, work: Path, mode: str, listen: int) -> None:
    sys.path.insert(0, str(host / "src/backend"))
    sys.path.insert(0, str(host / "src/plugin-runtime"))
    if mode == "host":
        import uvicorn
        from src.main import app
        uvicorn.run(app, host="127.0.0.1", port=listen)
    else:
        from runtime import PluginRegistry, PluginSupervisor, RuntimeHandler, RuntimeServer
        supervisor = PluginSupervisor(work / "workers", work / "runtime/.storage")
        supervisor.probe_isolation()
        registry = PluginRegistry(work / "runtime", supervisor)
        service = RuntimeServer(("127.0.0.1", listen), RuntimeHandler)
        service.registry = registry
        try:
            service.serve_forever()
        finally:
            supervisor.stop_all()


def acceptance(host: Path, work: Path) -> None:
    import httpx
    if os.name != "posix":
        raise ValueError("authenticated real-worker acceptance requires Linux")
    source = work / "fresh-fork"
    for name in ("tools", "sdk"):
        shutil.copytree(ROOT / name, source / name, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copyfile(ROOT / ".gitignore", source / ".gitignore")
    (source / "publishers").mkdir()
    (source / "publishers/registry.json").write_text(json.dumps({"schema_version": 1, "publishers": []}))

    def python(*args, env=None):
        subprocess.run([sys.executable, *args], cwd=source, env=env, check=True)

    def commit(message):
        subprocess.run(["git", "-C", str(source), "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(source), "commit", "-m", message], check=True, capture_output=True)

    python("tools/new_plugin.py", "greeting", "--id", PLUGIN_ID, "--name", "My Greeting", "--publisher", "Developer Acceptance")
    clean_env = {key: value for key, value in os.environ.items() if not key.startswith("PLUGIN_SIGNING")}
    python("tools/build_packages.py", env=clean_env)
    unsigned = next((source / ".validation/dist").glob("*.utp"))
    python("tools/create_signing_identity.py", "--key-directory", str(work / "private-keys"),
        "--key-id", "acceptance-1", "--publisher", "Developer Acceptance", "--prefix", "acceptance.")
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    for name, value in (("user.name", "Developer Acceptance"), ("user.email", "acceptance@example.invalid")):
        subprocess.run(["git", "-C", str(source), "config", name, value], check=True)
    commit("feat: create first independent greeting")
    signing_env = {**clean_env, "PLUGIN_SIGNING_KEY_ID": "acceptance-1",
        "PLUGIN_SIGNING_KEY_B64": (work / "private-keys/acceptance-1.private-seed.b64").read_text()}
    python("tools/build_packages.py", "--publish", env=signing_env)
    signed = next((source / "dist").glob("*.utp"))
    commit("chore: publish first signed package")
    public_registry = source / "publishers/registry.json"
    shutil.copyfile(public_registry, work / "trusted.json")
    (work / "catalogues.json").write_text(json.dumps({"version": 1, "catalogues": [{"id": "official", "enabled": False}]}))
    backend_port, runtime_port = port(), port()
    password = "Disposable-test-password1!"
    env = {**clean_env, "PRIMARY_USER_USERNAME": "developer-" + uuid4().hex,
        "PRIMARY_USER_EMAIL": uuid4().hex + "@example.invalid", "PRIMARY_USER_PASSWORD": password,
        "PLUGIN_RUNTIME_URL": f"http://127.0.0.1:{runtime_port}", "PLUGIN_RUNTIME_TOKEN": uuid4().hex + uuid4().hex,
        "PLUGIN_GATEWAY_URL": f"http://127.0.0.1:{backend_port}", "NONBUBBLE_ENV": "true",
        "PLUGIN_MANAGER_STATE_PATH": str(work / "manager.json"),
        "PLUGIN_CATALOGUE_REGISTRY": str(work / "catalogues.json"),
        "PLUGIN_TRUSTED_PUBLISHER_REGISTRY": str(work / "trusted.json"), "STARTUP_MODE": "testing", "DEBUG": "false",
        "SECRET_KEY": base64.urlsafe_b64encode(os.urandom(32)).decode()}
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=host / "src/backend", env=env, check=True)
    processes, logs = [], []
    try:
        for mode, listen in (("runtime", runtime_port), ("host", backend_port)):
            log = (work / f"{mode}.log").open("w")
            logs.append(log)
            processes.append(subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--host-root", str(host),
                "--work-root", str(work), "--mode", mode, "--port", str(listen)], env=env,
                cwd=host / "src/backend", stdout=log, stderr=log))
        with httpx.Client(base_url=f"http://127.0.0.1:{backend_port}", timeout=60) as client:
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline:
                try:
                    login = client.post("/api/auth/login", json={"username_or_email": env["PRIMARY_USER_USERNAME"], "password": password})
                    if login.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(0.2)
            else:
                raise AssertionError("host login unavailable; inspect host.log/runtime.log")

            def request(method, path, expected=200, **kwargs):
                response = client.request(method, "/api/plugins" + path, **kwargs)
                assert response.status_code == expected, (path, response.status_code, response.text[:2000])
                return response.json() if response.content else None

            def upload(path):
                return {"file": (path.name, path.read_bytes(), "application/octet-stream")}

            def greet(expected=200):
                return request("POST", f"/{PLUGIN_ID}/actions/greet", expected, json={"values": {"name": "Developer"}})

            request("POST", "/install/preview", 400, files={"file": ("invalid.utp", b"not a ZIP")})
            assert request("POST", "/install/preview", files=upload(unsigned))["trust_status"] == "unsigned"
            request("POST", "/install", 409, files=upload(unsigned))
            request("POST", "/install", 201, files=upload(unsigned), params={"allow_untrusted": True})
            assert greet()["message"] == "Hello, Developer!"
            request("PUT", f"/{PLUGIN_ID}/secrets/api_key", 403, json={"value": "DisposablePluginToken"})
            request("DELETE", f"/{PLUGIN_ID}", 204)
            assert request("POST", "/install/preview", files=upload(signed))["trust_status"] == "trusted"
            request("POST", "/install", 201, files=upload(signed))
            assert greet()["message"] == "Hello, Developer!"
            request("POST", f"/{PLUGIN_ID}/disable")
            greet(409)
            request("POST", f"/{PLUGIN_ID}/enable")
            assert greet()["message"] == "Hello, Developer!"
            manifest_path = source / "plugins/greeting/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["version"] = "0.2.0"
            ref = {"name": "plugin.storage", "version": 1}
            manifest["capabilities"] = [ref]
            manifest["permissions"] = [{"capability": ref, "rationale": "Read the plugin-owned saved token status."}]
            manifest_path.write_text(json.dumps(manifest))
            feature = source / "plugins/greeting/plugin.py"
            feature.write_text(feature.read_text().replace('return {"message": f"Hello, {name}!"}',
                'token = request("storage.get", "plugin.storage", {"key": "secrets/api_key"}).get("value")\n    return {"message": f"Welcome, {name}!", "has_secret": bool(token)}'))
            commit("feat: add private credential status")
            python("tools/build_packages.py", "--publish", env=signing_env)
            candidate = source / "dist" / f"{PLUGIN_ID}-0.2.0.utp"
            preview = request("PUT", f"/{PLUGIN_ID}/update/preview", files=upload(candidate))
            assert any(p["capability"] == "plugin.storage" for p in preview["permissions"])
            pending = request("PUT", f"/{PLUGIN_ID}/update", files=upload(candidate))
            assert pending["status"] == "awaiting_permissions" and pending["version"] == "0.1.0"
            assert greet()["message"] == "Hello, Developer!"
            request("PUT", f"/{PLUGIN_ID}/update", files=upload(candidate), params={"approved_permissions": ["plugin.storage:v1"]})
            assert greet()["message"] == "Welcome, Developer!"
            request("PUT", f"/{PLUGIN_ID}/secrets/api_key", json={"value": "DisposablePluginToken"})
            result = greet()
            assert result["has_secret"] is True and "DisposablePluginToken" not in json.dumps(result)
            request("POST", f"/{PLUGIN_ID}/disable")
            request("POST", f"/{PLUGIN_ID}/enable")
            assert greet()["has_secret"] is True
            request("DELETE", f"/{PLUGIN_ID}", 204)
            assert not request("GET", "")
            assert not (work / "runtime/.storage" / PLUGIN_ID).exists()
            (work / "http-conformance.json").write_text(json.dumps({"status": "passed", "plugin_id": PLUGIN_ID,
                "unsigned_consent": True, "signed_publisher": "community", "real_gateway": True,
                "new_permission_denial_and_approval": True, "secret_not_returned": True,
                "enable_use_update_uninstall": True, "isolation": "NONBUBBLE_ENV process mode"}, indent=2) + "\n")
            print("Authenticated host: fresh plugin, unsigned consent, own signature, live grants, secret storage, update and uninstall passed.")
    finally:
        for process in reversed(processes):
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        for log in logs:
            log.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-root", type=Path, required=True)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--mode", choices=("acceptance", "host", "runtime"), default="acceptance")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    host = args.host_root.resolve()
    if args.mode != "acceptance":
        server(host, args.work_root.resolve(), args.mode, args.port)
    elif args.work_root:
        args.work_root.mkdir(parents=True, exist_ok=False)
        acceptance(host, args.work_root.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="plugin-template-http-") as temporary:
            acceptance(host, Path(temporary))
