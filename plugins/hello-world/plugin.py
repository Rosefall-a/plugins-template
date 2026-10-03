"""A deletable starter using the real JSON-line Plugin API v1."""
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
