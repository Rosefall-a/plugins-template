"""Check local guide links and actual tool commands without a wiki system."""
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def check() -> None:
    pages = [ROOT / "README.md", ROOT / "DEVELOPMENT.md", *sorted((ROOT / "docs").glob("*.md"))]
    for page in pages:
        source = page.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", source):
            parsed = urlsplit(target)
            if not parsed.scheme and parsed.path:
                path = (page.parent / unquote(parsed.path)).resolve()
                if not path.is_relative_to(ROOT) or not path.exists():
                    raise ValueError(f"{page.name}: missing local documentation link {target}")
        for command in re.findall(r"\bpython\s+(tools/[\w/-]+\.py)", source):
            if not (ROOT / command).is_file():
                raise ValueError(f"{page.name}: nonexistent command {command}")
    print("Guide links and tool commands verified")


if __name__ == "__main__":
    check()
