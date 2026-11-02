from __future__ import annotations

import base64
from bisect import bisect_right

MAX_STEPS = 8
MAX_OPERATIONS = 10000


def flatten_steps(recipe: dict) -> list[dict]:
    if recipe.get("schemaVersion") == 1:
        return [recipe]
    if recipe.get("schemaVersion") != 3:
        raise ValueError("unsupported recipe schema in chain")
    steps = []
    for step in recipe.get("steps", []):
        steps.extend(flatten_steps(step))
    return steps


def compose_operations(first: list[dict], second: list[dict]) -> list[dict]:
    segments = []
    offset = 0
    for operation in first:
        if "copy" in operation:
            start, size = operation["copy"]
            segments.append((offset, size, start, None))
        else:
            data = base64.b64decode(operation["add"], validate=True)
            size = len(data)
            segments.append((offset, size, None, data))
        offset += size
    starts = [segment[0] for segment in segments]
    result: list[list] = []

    def emit_copy(start: int, size: int) -> None:
        if result and result[-1][0] == "copy" and result[-1][1] + result[-1][2] == start:
            result[-1][2] += size
        else:
            result.append(["copy", start, size])

    def emit_add(data: bytes) -> None:
        if result and result[-1][0] == "add":
            result[-1][1].extend(data)
        else:
            result.append(["add", bytearray(data)])

    for operation in second:
        if "add" in operation:
            emit_add(base64.b64decode(operation["add"], validate=True))
            continue
        position, remaining = operation["copy"]
        if position < 0 or remaining <= 0 or position + remaining > offset:
            raise ValueError("copy range outside the intermediate file")
        index = bisect_right(starts, position) - 1
        while remaining > 0:
            segment_start, segment_size, source, data = segments[index]
            inner = position - segment_start
            take = min(remaining, segment_size - inner)
            if take <= 0:
                index += 1
                continue
            if data is None:
                emit_copy(source + inner, take)
            else:
                emit_add(data[inner:inner + take])
            position += take
            remaining -= take
            index += 1
    return [{"copy": [item[1], item[2]]} if item[0] == "copy"
            else {"add": base64.b64encode(bytes(item[1])).decode("ascii")} for item in result]


def compose_steps(first: dict, second: dict) -> dict:
    if first["targetSha256"] != second["originalSha256"] or first["targetSize"] != second["originalSize"]:
        raise ValueError("discontinuous chain")
    operations = compose_operations(first["operations"], second["operations"])
    if not 1 <= len(operations) <= MAX_OPERATIONS:
        raise ValueError("composed step exceeds the installer operation limit")
    return {"schemaVersion": 1, "path": first["path"],
            "originalSha256": first["originalSha256"], "targetSha256": second["targetSha256"],
            "originalSize": first["originalSize"], "targetSize": second["targetSize"],
            "operations": operations}


def fit_chain(steps: list[dict], limit: int = MAX_STEPS) -> list[dict]:
    steps = list(steps)
    while len(steps) > limit:
        best = None
        for index in range(len(steps) - 1):
            try:
                merged = compose_steps(steps[index], steps[index + 1])
            except ValueError:
                continue
            if best is None or len(merged["operations"]) < len(best[1]["operations"]):
                best = (index, merged)
        if best is None:
            raise ValueError("chain cannot be shortened within the installer limits")
        index, merged = best
        steps[index:index + 2] = [merged]
    return steps
