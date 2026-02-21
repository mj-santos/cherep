#!/usr/bin/env python3
"""Lightweight manifest validation without external dependencies."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STORE_FILE = ROOT / "umbrel-app-store.yml"
APP_FILE = ROOT / "cherep-wallos" / "umbrel-app.yml"
COMPOSE_FILE = ROOT / "cherep-wallos" / "docker-compose.yml"

KEY_VALUE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$")
ID_RE = re.compile(r"^[a-z-]+$")


def parse_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith(" ") or line.startswith("\t"):
            continue
        m = KEY_VALUE_RE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        value = value.split("#", 1)[0].strip().strip('"').strip("'")
        data[key] = value
    return data


def validate() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for path in (STORE_FILE, APP_FILE, COMPOSE_FILE):
        if not path.exists():
            errors.append(f"Missing file: {path.relative_to(ROOT)}")

    if errors:
        return report(errors, warnings)

    store = parse_simple_yaml(STORE_FILE)
    app = parse_simple_yaml(APP_FILE)
    compose_text = COMPOSE_FILE.read_text(encoding="utf-8")

    for required in ("id", "name"):
        if required not in store or not store[required]:
            errors.append(f"umbrel-app-store.yml missing required key: {required}")

    for required in ("id", "name", "version", "port", "icon", "repo"):
        if required not in app or not app[required]:
            errors.append(f"cherep-wallos/umbrel-app.yml missing required key: {required}")

    store_id = store.get("id", "")
    app_id = app.get("id", "")
    if store_id and not ID_RE.fullmatch(store_id):
        errors.append("Store id must match ^[a-z-]+$")
    if app_id and not ID_RE.fullmatch(app_id):
        errors.append("App id must match ^[a-z-]+$")
    if store_id and app_id and not app_id.startswith(f"{store_id}-"):
        errors.append(f"App id '{app_id}' must start with '{store_id}-'")

    if app.get("version", "").lower() == "latest":
        warnings.append("App version is 'latest'; pinning explicit versions improves reproducibility")

    if re.search(r"image\s*:\s*[^\n]*:latest\b", compose_text):
        warnings.append("docker-compose.yml uses ':latest' image tag; pin a version or digest")

    if not re.search(r"\$\{APP_DATA_DIR\}", compose_text):
        warnings.append("docker-compose.yml has no APP_DATA_DIR usage; verify persistent data mounts")

    return report(errors, warnings)


def report(errors: list[str], warnings: list[str]) -> int:
    if errors:
        print("ERRORS:")
        for err in errors:
            print(f"  - {err}")
    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")

    if not errors and not warnings:
        print("Validation passed with no warnings.")
    elif not errors:
        print("Validation passed with warnings.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(validate())
