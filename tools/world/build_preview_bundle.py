from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil

from tools.build_inplace_bundle import match_ops
from tools.build_release_bundle import flatten_steps
from tools.bundle_limits import check_bundle
from tools.recipe_chain import fit_chain

NATIONAL_CONFIG = "conf_ligas_nacionais/BRA.cfg"
IMAGE_FOLDERS = ("escudos", "escudosMini", "camisas", "camisas2")
MAX_ORIGINS = 64


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def legacy_variants(inherit: Path, entry: dict, relative: str, published_sha: str, bridge: dict | None,
                    known: set[str]) -> list[dict]:
    if not entry or bridge is None:
        return []
    source = inherit / "patches" / (entry.get("recipe") or Path(relative).name + ".json")
    if not source.is_file():
        return []
    recipe = json.loads(source.read_text(encoding="utf8"))
    chained = []
    for legacy in recipe.get("variants", [recipe]):
        origin = legacy.get("originalSha256")
        if origin in known or legacy.get("targetSha256") != published_sha or len(known) >= MAX_ORIGINS:
            continue
        chained.append({"schemaVersion": 3, "path": relative, "originalSha256": origin,
                        "targetSha256": bridge["targetSha256"], "originalSize": legacy["originalSize"],
                        "targetSize": bridge["targetSize"], "steps": fit_chain(flatten_steps(legacy) + flatten_steps(bridge))})
        known.add(origin)
    return chained


def build(inherit: Path, compiled: Path, original: Path, base: Path, output: Path, version: str,
          release: bool = False) -> dict:
    if output.exists():
        raise SystemExit(f"saída já existe: {output}")
    shutil.copytree(inherit, output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf8"))
    entries = {f["path"]: f for f in manifest["files"]}
    sources = [("teams/" + p.name, p) for p in sorted((compiled / "teams").glob("*.ban"))]
    sources += [("conf_ligas_nacionais/" + p.name, p) for p in sorted((compiled / "conf_ligas_nacionais").glob("*.cfg"))]
    for folder in IMAGE_FOLDERS:
        sources += [(f"teams/{folder}/" + p.name, p) for p in sorted((compiled / "teams" / folder).glob("*.png"))]
    counts = {"replaced": 0, "added": 0, "unchanged": 0, "bridged": 0}
    for relative, source in sources:
        target = source.read_bytes()
        inputs = {}
        vanilla = original / relative
        published = base / relative
        for path in (vanilla, published):
            if path.is_file():
                body = path.read_bytes()
                inputs[sha(body)] = body
        if not vanilla.exists():
            inputs[sha(b"")] = b""
        if (sha(target) in inputs and len(inputs) == 1) or (published.is_file() and sha(published.read_bytes()) == sha(target)
                                                              and relative in entries):
            counts["unchanged"] += 1
            continue
        inputs.pop(sha(target), None)
        variants = []
        for digest, body in inputs.items():
            operations, _ = match_ops(body, target)
            variants.append({"schemaVersion": 1, "path": relative, "originalSha256": digest,
                             "targetSha256": sha(target), "originalSize": len(body), "targetSize": len(target),
                             "operations": operations})
        if published.is_file():
            published_sha = sha(published.read_bytes())
            bridge = next((v for v in variants if v["originalSha256"] == published_sha), None)
            chained = legacy_variants(inherit, entries.get(relative, {}), relative, published_sha, bridge,
                                      {v["originalSha256"] for v in variants} | {sha(target)})
            variants += chained
            counts["bridged"] += len(chained)
        image = relative.split("/")[1] in IMAGE_FOLDERS
        recipe = ("crest-" + sha(relative.encode())[:20] + ".json") if image else source.name + ".json"
        (output / "patches" / recipe).write_text(
            json.dumps({"schemaVersion": 2, "path": relative, "variants": variants}, ensure_ascii=False,
                       separators=(",", ":")), encoding="utf-8")
        accepted = [v["originalSha256"] for v in variants if v["originalSha256"] != sha(b"")]
        entry = copy.deepcopy(entries.get(relative, {}))
        for stale in ("recipe", "via", "allowMissing"):
            entry.pop(stale, None)
        if image:
            entry["recipe"] = recipe
            entry["component"] = "crests"
        replace = vanilla.exists() or published.exists()
        entry.update({"operation": "replace" if replace else "add", "path": relative, "size": len(target),
                      "sha256": sha(target), "acceptedOriginalSha256": accepted if replace else []})
        entry.setdefault("component", "season" if relative == NATIONAL_CONFIG else "rosters")
        if vanilla.exists():
            entry["vanillaSha256"] = sha(vanilla.read_bytes())
            entry["vanillaSize"] = vanilla.stat().st_size
            entry.pop("vanillaMissing", None)
            counts["replaced"] += 1
        else:
            entry.pop("vanillaSha256", None)
            entry.pop("vanillaSize", None)
            entry["vanillaMissing"] = True
            if replace:
                if not relative.endswith(".ban"):
                    raise SystemExit(f"arquivo ausente no original só pode ser equipe: {relative}")
                entry["allowMissing"] = True
                counts["replaced"] += 1
            else:
                counts["added"] += 1
        entries[relative] = entry
    manifest["files"] = sorted(entries.values(), key=lambda f: f["path"])
    manifest.update({"kind": "BRASFOOT_RELEASE_PATCH" if release else "BRASFOOT_HOMOLOGATION_PATCH",
                     "version": version, "publicationAllowed": release, "compatibilityTestedInGame": False,
                     "channel": "stable" if release else "local-preview", "tests": "not-run-at-owner-request"})
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    check_bundle(output)
    return {"bundle": str(output), "files": len(manifest["files"]), **counts}


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m tools.world.build_preview_bundle",
                                     description="Pacote de prévia do Super Update sobre o pacote publicado")
    parser.add_argument("--inherit", type=Path, required=True)
    parser.add_argument("--compiled", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.inherit, args.compiled, args.original, args.base, args.output, args.version,
                           args.release), ensure_ascii=False))


if __name__ == "__main__":
    main()
