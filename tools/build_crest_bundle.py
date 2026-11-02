#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import shutil

from PIL import Image

from tools.bundle_limits import check_bundle
from tools.crest_audit import Fetcher

ROOT = Path(__file__).resolve().parents[1]
SIZES = {"escudos": 60, "escudosMini": 18}
COMPONENT = "crests"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def approved_from_audit(audit: Path, statuses: list[str]) -> dict:
    data = json.loads(audit.read_text(encoding="utf8"))
    clubs = []
    for row in data["clubs"]:
        if row["status"] not in statuses:
            continue
        tm, sc = row["transfermarkt"], row["scores"]
        if row.get("transfermarktCrestUrl"):
            source, ident, url = "transfermarkt", tm["id"], row["transfermarktCrestUrl"]
        elif row.get("scoresCrestUrl"):
            source, ident, url = "365scores", sc["id"], row["scoresCrestUrl"]
        else:
            continue
        clubs.append({"teamFile": row["teamFile"], "stem": row["stem"], "name": row["name"],
                      "country": row["country"], "source": source, "sourceId": str(ident), "imageUrl": url,
                      "transfermarktId": tm.get("id"), "scoresId": sc.get("id"), "auditStatus": row["status"],
                      "distances": row["distances"]})
    return {"schemaVersion": 1, "season": 2026, "generatedAt": datetime.now(timezone.utc).isoformat(),
            "auditGeneratedAt": data["meta"]["generatedAt"], "statuses": statuses,
            "clubs": sorted(clubs, key=lambda c: c["teamFile"])}


def render(source: bytes, side: int) -> bytes:
    image = Image.open(io.BytesIO(source)).convert("RGBA")
    box = image.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if box:
        image = image.crop(box)
    scale = side / max(image.size)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    image = image.resize(size, Image.LANCZOS)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((side - size[0]) // 2, (side - size[1]) // 2))
    out = io.BytesIO()
    canvas.save(out, "PNG", optimize=True)
    return out.getvalue()


def recipe_name(path: str) -> str:
    return "crest-" + sha(path.encode())[:20] + ".json"


def crest_recipe(path: str, origins: dict[str, int], target: bytes) -> dict:
    variants = [{"schemaVersion": 1, "path": path, "originalSha256": origin, "targetSha256": sha(target),
                 "originalSize": size, "targetSize": len(target),
                 "operations": [{"add": base64.b64encode(target).decode()}]} for origin, size in origins.items()]
    return variants[0] if len(variants) == 1 else {"schemaVersion": 2, "path": path, "variants": variants}


def build(args: argparse.Namespace) -> dict:
    approved = json.loads(args.approved.read_text(encoding="utf8"))
    fetcher = Fetcher(args.cache, args.delay, args.cache_max_age_hours)
    output = args.output.resolve()
    if output.exists():
        raise ValueError(f"destino já existe: {output}")
    shutil.copytree(args.inherit_bundle.resolve(), output)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("schemaVersion") != 4:
        raise ValueError("escudos exigem pacote schema 4")
    previous = {f["path"]: f for f in manifest["files"] if f.get("component") == COMPONENT}
    if args.previous_bundle:
        earlier_root = args.previous_bundle.resolve()
        earlier = json.loads((earlier_root / "manifest.json").read_text(encoding="utf-8-sig"))
        for f in earlier["files"]:
            if f.get("component") == COMPONENT and f["path"] not in previous:
                shutil.copyfile(earlier_root / "patches" / f["recipe"], output / "patches" / f["recipe"])
                previous[f["path"]] = f
        if not (output / "crests.json").exists() and (earlier_root / "crests.json").exists():
            shutil.copyfile(earlier_root / "crests.json", output / "crests.json")
    manifest["files"] = [f for f in manifest["files"] if f.get("component") != COMPONENT]
    patches = output / "patches"
    origin_sizes = {}
    for f in previous.values():
        recipe = json.loads((patches / f["recipe"]).read_text(encoding="utf8"))
        for variant in recipe.get("variants", [recipe]):
            origin_sizes[variant["originalSha256"]] = variant["originalSize"]
        origin_sizes[f["sha256"]] = f["size"]
    regenerated = set()
    provenance = []
    skipped = []
    previews = args.output.with_name(args.output.name + "-png")
    for club in approved["clubs"]:
        status, body = fetcher.get(club["imageUrl"], "image/png")
        if status != 200 or not body:
            skipped.append({"teamFile": club["teamFile"], "reason": f"download {status}"})
            continue
        if not args.allow_changed_source and club.get("sourceSha256") != sha(body):
            skipped.append({"teamFile": club["teamFile"], "reason": "imagem da fonte mudou desde a aprovação"})
            continue
        files = []
        for folder, side in SIZES.items():
            path = f"teams/{folder}/{club['stem']}.png"
            vanilla_path = args.original_game / path
            if not vanilla_path.exists():
                continue
            vanilla = vanilla_path.read_bytes()
            target = render(body, side)
            if sha(target) == sha(vanilla):
                continue
            name = recipe_name(path)
            origins = {sha(vanilla): len(vanilla)}
            old = previous.get(path)
            if old:
                for value in [old["sha256"]] + old["acceptedOriginalSha256"]:
                    if value != sha(target) and value in origin_sizes and len(origins) < 64:
                        origins.setdefault(value, origin_sizes[value])
            (patches / name).write_text(json.dumps(crest_recipe(path, origins, target), separators=(",", ":")),
                                        encoding="utf8")
            manifest["files"].append({
                "operation": "replace", "path": path, "size": len(target), "sha256": sha(target),
                "acceptedOriginalSha256": list(origins), "recipe": name, "component": COMPONENT,
                "vanillaSha256": sha(vanilla), "vanillaSize": len(vanilla)})
            regenerated.add(path)
            preview = previews / folder / f"{club['stem']}.png"
            preview.parent.mkdir(parents=True, exist_ok=True)
            preview.write_bytes(target)
            files.append({"path": path, "sha256": sha(target)})
        if files:
            provenance.append({**{k: club[k] for k in ("teamFile", "name", "source", "sourceId", "imageUrl")},
                               "sourceSha256": sha(body), "files": files})
    kept = [f for path, f in previous.items() if path not in regenerated]
    manifest["files"].extend(kept)
    if args.version:
        manifest["version"] = args.version
    if args.preview:
        manifest.update(kind="BRASFOOT_HOMOLOGATION_PATCH", publicationAllowed=False,
                        compatibilityTestedInGame=False, channel="local-preview")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf8")
    kept_paths = {f["path"] for f in kept}
    earlier = json.loads((output / "crests.json").read_text(encoding="utf8")) if (output / "crests.json").exists() else {}
    provenance += [club for club in earlier.get("clubs", [])
                   if any(item["path"] in kept_paths for item in club.get("files", []))]
    (output / "crests.json").write_text(json.dumps(
        {"schemaVersion": 1, "component": COMPONENT, "approved": str(args.approved.name), "clubs": provenance,
         "skipped": skipped}, ensure_ascii=False, indent=1), encoding="utf8")
    check_bundle(output)
    return {"clubs": len(provenance), "files": sum(len(c["files"]) for c in provenance), "kept": len(kept),
            "skipped": skipped,
            "manifestFiles": len(manifest["files"]), "previewPng": str(previews)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Acrescenta o componente de escudos a um pacote")
    sub = parser.add_subparsers(dest="command", required=True)
    approve = sub.add_parser("approve", help="gera a lista aprovada a partir de uma auditoria")
    approve.add_argument("--audit", type=Path, required=True)
    approve.add_argument("--status", action="append", default=None)
    approve.add_argument("--out", type=Path, default=ROOT / "config/crest-updates-2026.json")
    approve.add_argument("--cache", type=Path, default=ROOT / "data/private/crest-audit-cache")
    bundle = sub.add_parser("bundle", help="monta o pacote com os escudos aprovados")
    bundle.add_argument("--approved", type=Path, default=ROOT / "config/crest-updates-2026.json")
    bundle.add_argument("--inherit-bundle", type=Path, required=True)
    bundle.add_argument("--previous-bundle", type=Path)
    bundle.add_argument("--output", type=Path, required=True)
    bundle.add_argument("--original-game", type=Path, default=ROOT / "data/private/vanilla-22-23")
    bundle.add_argument("--cache", type=Path, default=ROOT / "data/private/crest-audit-cache")
    bundle.add_argument("--delay", type=float, default=0.5)
    bundle.add_argument("--cache-max-age-hours", type=float, default=24 * 365)
    bundle.add_argument("--allow-changed-source", action="store_true")
    bundle.add_argument("--version")
    bundle.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    if args.command == "approve":
        result = approved_from_audit(args.audit, args.status or ["provavelmente desatualizado"])
        previous = json.loads(args.out.read_text(encoding="utf8")) if args.out.exists() else {}
        result["excluded"] = previous.get("excluded", [])
        excluded = {item["teamFile"] for item in result["excluded"]}
        result["clubs"] = [club for club in result["clubs"] if club["teamFile"] not in excluded]
        fetcher = Fetcher(args.cache, 0.5, 24 * 365)
        for club in result["clubs"]:
            status, body = fetcher.get(club["imageUrl"], "image/png")
            if status == 200 and body:
                club["sourceSha256"] = sha(body)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf8")
        print(json.dumps({"clubs": len(result["clubs"]), "out": str(args.out)}, ensure_ascii=False))
    else:
        print(json.dumps(build(args), ensure_ascii=False))


if __name__ == "__main__":
    main()
