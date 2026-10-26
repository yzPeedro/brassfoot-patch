# World Catalog Foundation

Stdlib SQLite global football catalog (`tools/world_catalog.py`).

Persistent stable IDs for countries, associations, competitions, seasons, clubs,
players, coaches and memberships. Field provenance (source URL, observed/effective
timestamps, confidence). Separate capability states: catalog/generated/playable.
Foreign keys enforced; duplicate rejection and transaction rollback supported.

Synthetic fixtures only; no production data or network collection.
