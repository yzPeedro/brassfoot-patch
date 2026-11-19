"""Gera a classe de dados dos estaduais (best.CompEstaduaisData) a partir de config/estaduais/<UF>.json."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ESTADUAIS = ROOT / "config" / "estaduais"
REGIONAIS = ROOT / "config" / "regionais"
LIGAS = ROOT / "config" / "ligas"
UF = sorted("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())


def text(value) -> str:
    return json.dumps(value or "", ensure_ascii=False)


def array(values, render) -> str:
    return "{" + ",".join(render(v) for v in values) + "}"


def ready_states(*folders: Path) -> list[dict]:
    states = []
    for folder in folders or (ESTADUAIS, REGIONAIS, LIGAS):
        if folder.exists():
            states += [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("*.json"))
                       if p.name != "aliases.json"]
    return [s for s in states if s.get("engine") == "ready"]


def key(state: dict) -> int:
    return state["key"] if "key" in state else UF.index(state["state"])


def source(*folders: Path) -> str:
    states = ready_states(*folders)
    rows = lambda render: ",\n".join("        " + render(s) for s in states)
    knockout = lambda s, render: array(s["knockout"], render)
    lines = [
        "package best;",
        "",
        "final class CompEstaduaisData {",
        "    private CompEstaduaisData() {",
        "    }",
        "",
        "    static final int[] STATE = " + array(states, lambda s: str(key(s))) + ";",
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
        "    static final String[][] FIXTURES = {\n"
        + rows(lambda s: array([f for pair in s["phase1"].get("fixtures") or [] for f in pair], text)) + "\n    };",
        "",
        "    static final int[][][] OPPONENTS = {\n"
        + rows(lambda s: array(s["phase1"].get("opponents") or [], lambda o: array(o, str))) + "\n    };",
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
        "",
        "    static final String[][][] KO_ENTRANTS = {\n"
        + rows(lambda s: knockout(s, lambda r: array(r.get("entrants") or [], text))) + "\n    };",
        "}",
        "",
    ]
    return "\n".join(lines)
