"""Gera a classe de dados dos estaduais (best.CompEstaduaisData) a partir de config/estaduais/<UF>.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ESTADUAIS = ROOT / "config" / "estaduais"
UF = sorted("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())


def text(value) -> str:
    return json.dumps(value or "", ensure_ascii=False)


def array(values, render) -> str:
    return "{" + ",".join(render(v) for v in values) + "}"


def ready_states(folder: Path = ESTADUAIS) -> list[dict]:
    if not folder.exists():
        return []
    states = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))]
    return [s for s in states if s.get("engine") == "ready"]


def source(folder: Path = ESTADUAIS) -> str:
    states = ready_states(folder)
    rows = lambda render: ",\n".join("        " + render(s) for s in states)
    knockout = lambda s, render: array(s["knockout"], render)
    lines = [
        "package best;",
        "",
        "final class CompEstaduaisData {",
        "    private CompEstaduaisData() {",
        "    }",
        "",
        "    static final int[] STATE = " + array(states, lambda s: str(UF.index(s["state"]))) + ";",
        "",
        "    static final String[][] TEAMS = {\n" + rows(lambda s: array(s["teams"], text)) + "\n    };",
        "",
        "    static final String[] P1_TYPE = " + array(states, lambda s: text(s["phase1"]["type"])) + ";",
        "",
        "    static final int[] P1_LEGS = " + array(states, lambda s: str(s["phase1"].get("legs", 1))) + ";",
        "",
        "    static final String[][][] GROUPS = {\n"
        + rows(lambda s: array(s["phase1"].get("groups") or [], lambda g: array(g, text))) + "\n    };",
        "",
        "    static final int[] RELEGATED = " + array(states, lambda s: str(s.get("relegated", 0))) + ";",
        "",
        "    static final String[][][][] KO_TIES = {\n"
        + rows(lambda s: knockout(s, lambda r: array(r["ties"], lambda t: array(t, text)))) + "\n    };",
        "",
        "    static final boolean[][] KO_LEGS = {\n"
        + rows(lambda s: knockout(s, lambda r: "true" if r["legs"] == 2 else "false")) + "\n    };",
        "",
        "    static final String[][] KO_TIEBREAK = {\n"
        + rows(lambda s: knockout(s, lambda r: text(r.get("tiebreak", "penalties")))) + "\n    };",
        "",
        "    static final String[][] KO_HOME = {\n"
        + rows(lambda s: knockout(s, lambda r: text(r.get("home", "better-second")))) + "\n    };",
        "}",
        "",
    ]
    return "\n".join(lines)
