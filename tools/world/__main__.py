from __future__ import annotations

import argparse
import json
import time

from tools.world import catalog, fifa, report, scores365, uefa, wikidata, wikipedia

COLLECTORS = {"wikidata": wikidata.collect, "fifa": fifa.collect, "uefa": uefa.collect, "365scores": scores365.collect,
              "wikipedia": wikipedia.collect}


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m tools.world",
                                     description="Catálogo mundial do Super Update: coleta, montagem e cobertura")
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect")
    collect.add_argument("--source", choices=[*COLLECTORS, "all"], default="all")
    collect.add_argument("--refresh", action="store_true")
    collect.add_argument("--max-age-hours", type=float)
    sub.add_parser("build")
    sub.add_parser("report")
    args = parser.parse_args()
    started = time.monotonic()
    if args.command == "collect":
        names = list(COLLECTORS) if args.source == "all" else [args.source]
        results = []
        for name in names:
            began = time.monotonic()
            try:
                result = COLLECTORS[name](refresh=args.refresh, max_age_hours=args.max_age_hours)
            except Exception as exc:
                result = {"source": name, "error": f"{type(exc).__name__}: {exc}"}
            result["seconds"] = round(time.monotonic() - began, 1)
            results.append(result)
            print(json.dumps(result, ensure_ascii=False))
    elif args.command == "build":
        print(json.dumps(catalog.build(), ensure_ascii=False))
    else:
        print(json.dumps(report.build(), ensure_ascii=False))
    print(json.dumps({"seconds": round(time.monotonic() - started, 1)}))


if __name__ == "__main__":
    main()
