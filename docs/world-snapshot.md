# World catalog snapshots

`tools/world_snapshot.py` provides a deterministic JSON snapshot layer for
callers that already have source results. It does not collect data, contact
services, or make claims about a live sports update. Feed records use
`{type, id, fields, provenance}` and source results use
`{status: "ok"|"failed", records, error}`. Stable entity IDs are supplied by
the caller; fields are keyed by entity type and ID.

## Content and provenance

The content hash covers normalized entities, field values and provenance,
plus unresolved conflicts. It excludes `observed_at` and operational
`source_status`. Therefore repeating identical content at a later observation
time does not advance `content_version`. A content change advances the version
once and the returned `diff` lists field additions and changes. Source URL and
effective date are kept per field; the observation clock is snapshot metadata.

Each source result is independent. A failed source or a successful result with
no records updates its operational status but does not clear trusted fields.
A source omitted from a run likewise leaves existing fields intact. When a
different source supplies a conflicting field value, the trusted value stays
in place and both values with source provenance are retained under
`content.conflicts` for later reconciliation. A changed value from the same
source updates that field.

## Persistence and operation

`create_snapshot(results, previous, path=..., dry_run=True)` computes a proposed
snapshot without writing. With `dry_run=False`, it writes a complete temporary
file in the destination directory, flushes it, and atomically replaces the
destination. If the process stops before replacement, the previous destination
remains intact. `load_snapshot` validates the format version and content hash
before the snapshot is trusted. `diff_snapshots` creates a compact field-level
comparison for review.

This layer preserves sufficient point-in-time content for its represented
fields, but source acquisition, retention policy, publication history, and
release binding remain the responsibility of separate systems. Tests use only
synthetic fixtures and `example.invalid` provenance.
