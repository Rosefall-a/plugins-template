"""Check static JS and run declared plugin frontend checks/builds before packaging."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

try:
    from .distribution import ROOT, discover_plugins
except ImportError:
    from distribution import ROOT, discover_plugins


def build(root: Path, install: bool = False) -> None:
    node = shutil.which("node")
    npm = shutil.which("npm") or shutil.which("npm.cmd")
    for source, _ in discover_plugins(root):
        projects = sorted(source.rglob("package.json"))
        projects = [p for p in projects if "node_modules" not in p.parts]
        for project in projects:
            if not npm:
                raise ValueError("Node.js/npm are required for frontend projects")
            scripts = json.loads(project.read_text()).get("scripts", {})
            if not {"build", "test"} <= scripts.keys():
                raise ValueError(f"{project}: frontend projects must declare build and test scripts")
            if install:
                if not project.with_name("package-lock.json").is_file():
                    raise ValueError(f"{project}: commit package-lock.json for npm ci")
                subprocess.run([npm, "ci"], cwd=project.parent, check=True)
            for name in ("lint", "typecheck", "test", "build"):
                if name in scripts:
                    subprocess.run([npm, "run", name], cwd=project.parent, check=True)
        for folder in ("frontend", "native"):
            for script in sorted((source / folder).rglob("*.js")):
                if "node_modules" not in script.parts:
                    if not node:
                        raise ValueError("Node.js is required to check frontend JavaScript")
                    subprocess.run([node, "--check", str(script)], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="install locked npm dependencies")
    args = parser.parse_args()
    build(ROOT, args.install)
