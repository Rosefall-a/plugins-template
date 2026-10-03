"""Exercise the current generated packages without replacing published artifacts."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def built_distribution(tmp_path_factory):
    output = tmp_path_factory.mktemp("distribution")
    subprocess.run([sys.executable, str(ROOT / "tools/build_packages.py"), "--output-root", str(output)], check=True)
    return output


@pytest.fixture(scope="session")
def current_packages(built_distribution):
    entries = json.loads((built_distribution / "list.json").read_text(encoding="utf-8"))["plugins"]
    return {e["plugin_id"]: built_distribution / "dist" / e["package"]["filename"] for e in entries}
