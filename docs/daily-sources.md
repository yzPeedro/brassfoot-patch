# Daily cached sources

`tools/daily_sources.py` is an offline intake boundary. It reads only an
explicit allow-list of JSON files below a caller-provided cache directory;
there is no HTTP client, API key, retry loop, or fallback to invented data.

Each source declares a name, relative cache path, and HTTPS provenance URL.
The default bound is 25 sources and 256,000 bytes per source. Paths that leave
the cache directory, symlinks, invalid records, non-HTTPS provenance, duplicate
names, and malformed JSON fail closed.

`daily_snapshot` adapts the cached records to `world_snapshot.create_snapshot`.
It returns a content-hash change report, preserves prior trusted fields through
the snapshot layer, and reports `network_requests: 0`. Tests use only
synthetic `example.invalid` sources. This is a cache contract, not evidence of
live sports collection or release readiness.
