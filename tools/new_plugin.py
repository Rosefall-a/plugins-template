"""Create another real plugin by adapting a local plugin's public contract."""
import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def create(slug: str, plugin_id: str, name: str, publisher: str, source: Path | None = None) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,47}", slug):
        raise ValueError("directory name must be a lowercase slug")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", plugin_id):
        raise ValueError("plugin ID must be lowercase and at most 64 characters")
    for path in (ROOT / "plugins").glob("*/manifest.json"):
        if json.loads(path.read_text())["plugin_id"] == plugin_id:
            raise ValueError("plugin ID already exists")
    destination = ROOT / "plugins" / slug
    if destination.exists():
        raise ValueError("destination already exists")
    if source is not None and not (source / "manifest.json").is_file():
        raise ValueError("--from must point to a complete local plugin")
    if source is not None:
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("node_modules", "__pycache__", ".*"))
    else:
        destination.mkdir(parents=True)
        recipe = {
            "manifest.json": {"manifest_version": 1, "plugin_id": plugin_id, "name": name,
                "version": "0.1.0", "description": "A greeting from your independent plugin.",
                "entrypoint": "plugin:main", "sdk_version_range": "^1.0.0", "application_version_range": "*",
                "capabilities": [], "permissions": [], "dependencies": [], "storage": {"quota_mb": 1},
                "ui": {"pages": ["hello"], "actions": ["greet"], "settings": [], "menus": []},
                "integrity": {"sha256": "0" * 64, "signature": None, "key_id": None}},
            "ui.json": {"schema_version": "v1", "plugin_id": plugin_id, "title": name,
                "actions": [{"id": "greet", "label": "Say hello", "handler": "plugin:greet"}],
                "pages": [{"id": "hello", "title": name, "actions": ["greet"]}]},
            "release.json": {"schema_version": 1, "publisher": publisher, "tags": ["personal"],
                "icon": None, "automatic_update": False, "release_notes": "Initial release."},
        }
        for filename, document in recipe.items():
            (destination / filename).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
        (destination / "plugin.py").write_text('''"""An independent Plugin API v1 greeting."""
import time
from sdk.plugin_protocol import request


def greet(values: dict) -> dict:
    name = str(values.get("name", "world")).strip()[:80] or "world"
    return {"message": f"Hello, {name}!"}


def main() -> None:
    request("lifecycle.ready", "lifecycle.ready", {})
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
''', encoding="utf-8")
    for filename in ("manifest.json", "ui.json", "release.json"):
        path = destination / filename
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        if filename == "manifest.json":
            data.update(plugin_id=plugin_id, name=name, version="0.1.0",
                        integrity={"sha256": "0" * 64, "signature": None, "key_id": None})
        elif filename == "ui.json":
            data.update(plugin_id=plugin_id, title=name)
        else:
            data.update(publisher=publisher, release_notes="Initial release.")
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (destination / "README.md").write_text(f"# {name}\n\nDescribe your plugin, permissions and configuration here.\n", encoding="utf-8")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument("--id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--publisher", required=True)
    parser.add_argument("--from", dest="source", type=Path, help="optionally adapt an existing local plugin")
    args = parser.parse_args()
    print(create(args.slug, args.id, args.name, args.publisher, args.source))
