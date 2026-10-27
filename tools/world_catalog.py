"""Stdlib SQLite global football catalog foundation (Brasfoot Mega Patch)."""
from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS countries (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    iso_code TEXT,
    source_url TEXT,
    observed_at TEXT,
    effective_at TEXT,
    confidence REAL,
    capability TEXT NOT NULL DEFAULT 'catalog'
);

CREATE TABLE IF NOT EXISTS associations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country_id TEXT NOT NULL REFERENCES countries(id),
    source_url TEXT,
    observed_at TEXT,
    effective_at TEXT,
    confidence REAL,
    capability TEXT NOT NULL DEFAULT 'catalog'
);

CREATE TABLE IF NOT EXISTS competitions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    association_id TEXT NOT NULL REFERENCES associations(id),
    tier INTEGER,
    source_url TEXT,
    observed_at TEXT,
    effective_at TEXT,
    confidence REAL,
    capability TEXT NOT NULL DEFAULT 'catalog'
);

CREATE TABLE IF NOT EXISTS seasons (
    id TEXT PRIMARY KEY,
    competition_id TEXT NOT NULL REFERENCES competitions(id),
    label TEXT NOT NULL,
    start_year INTEGER NOT NULL,
    end_year INTEGER NOT NULL,
    source_url TEXT,
    observed_at TEXT,
    effective_at TEXT,
    confidence REAL,
    capability TEXT NOT NULL DEFAULT 'catalog',
    UNIQUE(competition_id, label)
);

CREATE TABLE IF NOT EXISTS clubs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    country_id TEXT NOT NULL REFERENCES countries(id),
    source_url TEXT,
    observed_at TEXT,
    effective_at TEXT,
    confidence REAL,
    capability TEXT NOT NULL DEFAULT 'catalog'
);

CREATE TABLE IF NOT EXISTS club_memberships (
    id TEXT PRIMARY KEY,
    club_id TEXT NOT NULL REFERENCES clubs(id),
    competition_id TEXT NOT NULL REFERENCES competitions(id),
    season_id TEXT NOT NULL REFERENCES seasons(id),
    division_label TEXT,
    source_url TEXT,
    observed_at TEXT,
    effective_at TEXT,
    confidence REAL,
    capability TEXT NOT NULL DEFAULT 'catalog'
);

CREATE TABLE IF NOT EXISTS players (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    birth_date TEXT,
    nationality_country_id TEXT REFERENCES countries(id),
    source_url TEXT,
    observed_at TEXT,
    effective_at TEXT,
    confidence REAL,
    capability TEXT NOT NULL DEFAULT 'catalog'
);

CREATE TABLE IF NOT EXISTS coaches (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    nationality_country_id TEXT REFERENCES countries(id),
    source_url TEXT,
    observed_at TEXT,
    effective_at TEXT,
    confidence REAL,
    capability TEXT NOT NULL DEFAULT 'catalog'
);

CREATE TABLE IF NOT EXISTS player_memberships (
    id TEXT PRIMARY KEY,
    player_id TEXT NOT NULL REFERENCES players(id),
    club_id TEXT NOT NULL REFERENCES clubs(id),
    season_id TEXT NOT NULL REFERENCES seasons(id),
    role TEXT,
    source_url TEXT,
    observed_at TEXT,
    effective_at TEXT,
    confidence REAL,
    capability TEXT NOT NULL DEFAULT 'catalog'
);
"""

VALID_CAPABILITIES = {"catalog", "generated", "playable"}
TABLES = {"countries", "associations", "competitions", "seasons", "clubs",
          "players", "coaches", "club_memberships", "player_memberships"}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix):
    return "%s-%s" % (prefix, uuid.uuid4().hex[:12])


def provenance_fields(source_url=None, observed_at=None, effective_at=None, confidence=None):
    return {
        "source_url": source_url,
        "observed_at": observed_at or now_iso(),
        "effective_at": effective_at,
        "confidence": confidence,
    }


class WorldCatalog:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        self._transaction_depth = 0

    def close(self):
        self.conn.close()

    @contextmanager
    def transaction(self):
        # SAVEPOINT works both at the outermost level and for nested units.
        # Individual add methods must not commit a surrounding transaction.
        name = "catalog_%d" % self._transaction_depth
        self.conn.execute("SAVEPOINT " + name)
        self._transaction_depth += 1
        try:
            yield self.conn
        except BaseException:
            self.conn.execute("ROLLBACK TO SAVEPOINT " + name)
            self.conn.execute("RELEASE SAVEPOINT " + name)
            raise
        else:
            self.conn.execute("RELEASE SAVEPOINT " + name)
        finally:
            self._transaction_depth -= 1

    def _commit(self):
        if not self._transaction_depth:
            self.conn.commit()

    def _validate_capability(self, cap):
        if cap not in VALID_CAPABILITIES:
            raise ValueError("invalid capability: %s" % cap)

    def add_country(self, name, iso_code=None, **prov):
        cid = prov.pop("entity_id", None) or new_id("country")
        p = provenance_fields(**prov)
        self.conn.execute(
            "INSERT INTO countries (id,name,iso_code,source_url,observed_at,effective_at,confidence,capability) VALUES (?,?,?,?,?,?,?,?)",
            (cid, name, iso_code, p["source_url"], p["observed_at"], p["effective_at"], p["confidence"], "catalog"),
        )
        self._commit()
        return cid

    def add_association(self, name, country_id, **prov):
        if not self.conn.execute("SELECT 1 FROM countries WHERE id=?", (country_id,)).fetchone():
            raise ValueError("unknown country_id")
        aid = prov.pop("entity_id", None) or new_id("assoc")
        p = provenance_fields(**prov)
        self.conn.execute(
            "INSERT INTO associations (id,name,country_id,source_url,observed_at,effective_at,confidence,capability) VALUES (?,?,?,?,?,?,?,?)",
            (aid, name, country_id, p["source_url"], p["observed_at"], p["effective_at"], p["confidence"], "catalog"),
        )
        self._commit()
        return aid

    def add_competition(self, name, association_id, tier=None, **prov):
        if not self.conn.execute("SELECT 1 FROM associations WHERE id=?", (association_id,)).fetchone():
            raise ValueError("unknown association_id")
        cid = prov.pop("entity_id", None) or new_id("comp")
        p = provenance_fields(**prov)
        self.conn.execute(
            "INSERT INTO competitions (id,name,association_id,tier,source_url,observed_at,effective_at,confidence,capability) VALUES (?,?,?,?,?,?,?,?,?)",
            (cid, name, association_id, tier, p["source_url"], p["observed_at"], p["effective_at"], p["confidence"], "catalog"),
        )
        self._commit()
        return cid

    def add_season(self, competition_id, label, start_year, end_year, **prov):
        if not self.conn.execute("SELECT 1 FROM competitions WHERE id=?", (competition_id,)).fetchone():
            raise ValueError("unknown competition_id")
        if end_year < start_year:
            raise ValueError("end_year before start_year")
        sid = prov.pop("entity_id", None) or new_id("season")
        p = provenance_fields(**prov)
        try:
            self.conn.execute(
                "INSERT INTO seasons (id,competition_id,label,start_year,end_year,source_url,observed_at,effective_at,confidence,capability) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (sid, competition_id, label, start_year, end_year, p["source_url"], p["observed_at"], p["effective_at"], p["confidence"], "catalog"),
            )
            self._commit()
        except sqlite3.IntegrityError:
            raise ValueError("duplicate season label for competition")
        return sid

    def add_club(self, name, country_id, **prov):
        if not self.conn.execute("SELECT 1 FROM countries WHERE id=?", (country_id,)).fetchone():
            raise ValueError("unknown country_id")
        cid = prov.pop("entity_id", None) or new_id("club")
        p = provenance_fields(**prov)
        self.conn.execute(
            "INSERT INTO clubs (id,name,country_id,source_url,observed_at,effective_at,confidence,capability) VALUES (?,?,?,?,?,?,?,?)",
            (cid, name, country_id, p["source_url"], p["observed_at"], p["effective_at"], p["confidence"], "catalog"),
        )
        self._commit()
        return cid

    def add_club_membership(self, club_id, competition_id, season_id, division_label=None, **prov):
        for tbl, col, val in (("clubs", "id", club_id), ("competitions", "id", competition_id), ("seasons", "id", season_id)):
            if not self.conn.execute("SELECT 1 FROM %s WHERE %s=?" % (tbl, col), (val,)).fetchone():
                raise ValueError("unknown %s reference" % tbl)
        mid = prov.pop("entity_id", None) or new_id("cm")
        p = provenance_fields(**prov)
        self.conn.execute(
            "INSERT INTO club_memberships (id,club_id,competition_id,season_id,division_label,source_url,observed_at,effective_at,confidence,capability) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (mid, club_id, competition_id, season_id, division_label, p["source_url"], p["observed_at"], p["effective_at"], p["confidence"], "catalog"),
        )
        self._commit()
        return mid

    def add_player(self, full_name, birth_date=None, nationality_country_id=None, **prov):
        if nationality_country_id is not None and not self.conn.execute("SELECT 1 FROM countries WHERE id=?", (nationality_country_id,)).fetchone():
            raise ValueError("unknown nationality country")
        pid = prov.pop("entity_id", None) or new_id("player")
        p = provenance_fields(**prov)
        self.conn.execute(
            "INSERT INTO players (id,full_name,birth_date,nationality_country_id,source_url,observed_at,effective_at,confidence,capability) VALUES (?,?,?,?,?,?,?,?,?)",
            (pid, full_name, birth_date, nationality_country_id, p["source_url"], p["observed_at"], p["effective_at"], p["confidence"], "catalog"),
        )
        self._commit()
        return pid

    def add_coach(self, full_name, nationality_country_id=None, **prov):
        if nationality_country_id is not None and not self.conn.execute("SELECT 1 FROM countries WHERE id=?", (nationality_country_id,)).fetchone():
            raise ValueError("unknown nationality country")
        cid = prov.pop("entity_id", None) or new_id("coach")
        p = provenance_fields(**prov)
        self.conn.execute(
            "INSERT INTO coaches (id,full_name,nationality_country_id,source_url,observed_at,effective_at,confidence,capability) VALUES (?,?,?,?,?,?,?,?)",
            (cid, full_name, nationality_country_id, p["source_url"], p["observed_at"], p["effective_at"], p["confidence"], "catalog"),
        )
        self._commit()
        return cid

    def add_player_membership(self, player_id, club_id, season_id, role=None, **prov):
        for tbl, val in (("players", player_id), ("clubs", club_id), ("seasons", season_id)):
            if not self.conn.execute("SELECT 1 FROM %s WHERE id=?" % tbl, (val,)).fetchone():
                raise ValueError("unknown %s reference" % tbl)
        mid = prov.pop("entity_id", None) or new_id("pm")
        p = provenance_fields(**prov)
        self.conn.execute(
            "INSERT INTO player_memberships (id,player_id,club_id,season_id,role,source_url,observed_at,effective_at,confidence,capability) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (mid, player_id, club_id, season_id, role, p["source_url"], p["observed_at"], p["effective_at"], p["confidence"], "catalog"),
        )
        self._commit()
        return mid

    def set_capability(self, table, entity_id, capability):
        self._validate_capability(capability)
        if table not in TABLES:
            raise ValueError("unknown table")
        cur = self.conn.execute("UPDATE %s SET capability=? WHERE id=?" % table, (capability, entity_id))
        if cur.rowcount == 0:
            raise ValueError("entity not found")
        self._commit()

    def get(self, table, entity_id):
        if table not in TABLES:
            raise ValueError("unknown table")
        row = self.conn.execute("SELECT * FROM %s WHERE id=?" % table, (entity_id,)).fetchone()
        return dict(row) if row else None
