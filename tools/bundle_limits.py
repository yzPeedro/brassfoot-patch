from __future__ import annotations

import json
from pathlib import Path
import re

MAX_FILES = 2048
MAX_ORIGINS = 64
MAX_SIZE = 25 * 1024 * 1024
HASH = re.compile(r"[0-9a-f]{64}")


def hub_limit_errors(manifest: dict) -> list[str]:
    errors = []
    files = manifest.get("files", [])
    if not 1 <= len(files) <= MAX_FILES:
        errors.append(f"o pacote tem {len(files)} arquivos; o hub aceita de 1 a {MAX_FILES}")
    executable = None
    for entry in files:
        path = entry.get("path", "")
        mode = entry.get("operation") or "replace"
        accepted = entry.get("acceptedOriginalSha256") or []
        if path == "bf22-23.exe":
            executable = entry
        if not 4 <= int(entry.get("size", 0)) <= MAX_SIZE or not HASH.fullmatch(entry.get("sha256", "")):
            errors.append(f"{path}: tamanho ou hash fora do que o hub aceita")
        if mode == "replace" and not 1 <= len(accepted) <= MAX_ORIGINS:
            errors.append(f"{path}: {len(accepted)} origens aceitas; o hub aceita de 1 a {MAX_ORIGINS}")
        if any(not HASH.fullmatch(value) for value in accepted):
            errors.append(f"{path}: hash de origem inválido")
        if entry.get("sha256") in accepted:
            errors.append(f"{path}: origem idêntica ao resultado")
    components = manifest.get("components") or {}
    full_accepted = (executable or {}).get("acceptedOriginalSha256") or []
    for key, target in (components.get("executables") or {}).items():
        if key == "patch+live":
            continue
        union = {value for value in (target.get("acceptedOriginalSha256") or []) + full_accepted
                 if value != target.get("sha256")}
        if len(union) > MAX_ORIGINS:
            errors.append(f"componente {key}: {len(union)} origens somadas; o hub usa só as primeiras {MAX_ORIGINS}")
    return errors


def check_bundle(bundle: Path) -> None:
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8-sig"))
    errors = hub_limit_errors(manifest)
    if errors:
        raise ValueError("pacote recusado pelas regras do hub:\n- " + "\n- ".join(errors))
