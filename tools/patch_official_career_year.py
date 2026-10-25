#!/usr/bin/env python3
"""Proof-of-concept 2026-only career selector for one VERIFIED Brasfoot 22-23 version.

Changes only the official original a/hU.class, in memory or into a separate file.
Does not patch license/DRM, an installed game, or a complete proprietary EXE.
The user's 2023/2024 game is a DIFFERENT version; this is NOT compatible with it.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

OFFICIAL_HU_SHA = "37fb17d876aab1263756bca97c3f9488007b7afe59f8c68494cf711a0f61a234"

class ParseError(ValueError):
    pass

class ClassFile:
    """Only enough JVM ClassFile parsing to safely pinpoint methods and constants."""
    def __init__(self, data: bytes):
        self.data = bytearray(data)
        self.i = 0
        self.cp = [None]
        if self.u4() != 0xCAFEBABE:
            raise ParseError("Invalid Java class magic")
        self.u2()
        self.u2()
        count = self.u2()
        index = 1
        while index < count:
            tag = self.u1()
            if tag == 1:
                length = self.u2()
                start = self.i
                name = self.take(length)
                self.cp.append(("utf8", start, length, name))
            elif tag in (3, 4):
                self.take(4)
                self.cp.append(("other",))
            elif tag in (5, 6):
                self.take(8)
                self.cp.extend([("other",), None])
                index += 1
            elif tag in (7, 8, 16, 19, 20):
                self.cp.append((tag, self.u2()))
            elif tag in (9, 10, 11, 12, 17, 18):
                self.cp.append((tag, self.u2(), self.u2()))
            elif tag == 15:
                self.take(3)
                self.cp.append(("other",))
            else:
                raise ParseError(f"Unknown constant-pool tag {tag}")
            index += 1
        self.take(6)
        for _ in range(self.u2()):
            self.take(2)
        for _ in range(self.u2()):
            self.member()
        self.methods = {}
        for _ in range(self.u2()):
            self.member(method=True)

    def take(self, size):
        if self.i + size > len(self.data):
            raise ParseError("Truncated Java class")
        data = bytes(self.data[self.i:self.i + size])
        self.i += size
        return data

    def u1(self):
        return self.take(1)[0]

    def u2(self):
        return struct.unpack(">H", self.take(2))[0]

    def u4(self):
        return struct.unpack(">I", self.take(4))[0]

    def utf8(self, index):
        if index <= 0 or index >= len(self.cp):
            raise ParseError("Invalid constant pool index")
        item = self.cp[index]
        if not item or item[0] != "utf8":
            raise ParseError("Constant is not UTF8")
        return item[3].decode("utf-8")

    def member(self, method=False):
        self.u2()
        name_index = self.u2()
        self.u2()
        name = self.utf8(name_index)
        for _ in range(self.u2()):
            attr_name = self.utf8(self.u2())
            length = self.u4()
            start = self.i
            if method and attr_name == "Code":
                self.u2()
                self.u2()
                size = self.u4()
                self.methods[name] = (self.i, size)
            self.i = start + length
            if self.i > len(self.data):
                raise ParseError("Invalid attribute length")

    def cp_string(self, value):
        indexes = [i for i, item in enumerate(self.cp) if item and item[0] == 8
                   and self.utf8(item[1]) == str(value)]
        if len(indexes) != 1:
            raise ParseError(f"String {value} is ambiguous or missing")
        return indexes[0]

    def replace_constant(self, before, after):
        matches = [item for item in self.cp if item and item[0] == "utf8"
                   and item[3] == before.encode("utf-8")]
        if len(matches) != 1 or len(before) != len(after):
            raise ParseError("String constant replacement is unsafe")
        _, offset, length, _ = matches[0]
        self.data[offset:offset + length] = after.encode("utf-8")


def patch_verified_variant(original: bytes, *, expected_sha256: str,
                           source_years: tuple[int, int]) -> bytes:
    """Patch a structurally compatible *fingerprinted* class; no in-game proof.

    Only callers with an independently verified original hash may use this
    adapter. The CLI still accepts exclusively the known official fingerprint.
    """
    if (not isinstance(expected_sha256, str) or len(expected_sha256) != 64
            or any(c not in "0123456789abcdef" for c in expected_sha256)):
        raise ParseError("An exact lowercase SHA-256 fingerprint is required")
    if (len(source_years) != 2 or any(type(year) is not int or year < 2000
                                   or year > 2099 for year in source_years)
            or source_years[0] >= source_years[1] or 2026 in source_years):
        raise ParseError("Unsupported source year pair")
    if hashlib.sha256(original).hexdigest() != expected_sha256:
        raise ParseError("Unknown Brasfoot version: original a/hU.class SHA mismatch")
    klass = ClassFile(original)
    if "mQ" not in klass.methods:
        raise ParseError("Expected career year initialization method not found")
    start, length = klass.methods["mQ"]
    instructions = bytes(klass.data[start:start + length])
    first = klass.cp_string(source_years[0])
    second = klass.cp_string(source_years[1])
    if max(first, second) > 255:
        raise ParseError("Unexpected wide LDC constants")
    calls = []
    for index in (first, second):
        signature = bytes((0x12, index, 0xB6))
        if instructions.count(signature) != 1:
            raise ParseError("Unexpected JComboBox.addItem sequence")
        calls.append(instructions.index(signature))
    if calls[0] >= calls[1]:
        raise ParseError("Unexpected year ordering")
    first_invoke = instructions[calls[0] + 2:calls[0] + 5]
    second_invoke = instructions[calls[1] + 2:calls[1] + 5]
    if first_invoke != second_invoke or first_invoke[0] != 0xB6:
        raise ParseError("Different UI method targets")
    # JVM stack: JComboBox, String. Consume both rather than invoke addItem.
    # Keeps method code length and all StackMapTable branch offsets unchanged.
    invocation_offset = start + calls[1] + 2
    klass.data[invocation_offset:invocation_offset + 3] = b"\x57\x57\x00"
    # Old anoinicio preference=1 must not select an item that no longer exists.
    selection = b"\x04\xB6"
    if instructions.count(selection) != 1:
        raise ParseError("Old selected-index branch changed")
    klass.data[start + instructions.index(selection)] = 0x03
    # Send 2026 to the actual engine rather than merely changing the UI.
    year_literals = tuple(b"\x11" + year.to_bytes(2, "big") for year in source_years)
    consumers = []
    for method, (offset, count) in klass.methods.items():
        code = bytes(klass.data[offset:offset + count])
        if all(code.count(item) == 1 for item in year_literals):
            consumers.append((method, offset, code))
    if len(consumers) != 1:
        raise ParseError("Original game year engine setter could not be isolated")
    _, consumer_start, consumer_code = consumers[0]
    for target in year_literals:
        index = consumer_start + consumer_code.index(target)
        klass.data[index:index + 3] = b"\x11\x07\xEA"  # JVM sipush 2026
    klass.replace_constant(str(source_years[0]), "2026")
    result = bytes(klass.data)
    verified = ClassFile(result)
    if verified.cp_string(2026) != first or len(result) != len(original):
        raise ParseError("Patched class integrity check failed")
    return result


def patch_official(original: bytes) -> bytes:
    """Public official 2022/2023 fingerprint only; fail closed for all others."""
    return patch_verified_variant(
        original, expected_sha256=OFFICIAL_HU_SHA, source_years=(2022, 2023)
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original-class", type=Path, required=True)
    p.add_argument("--output-class", type=Path, required=True)
    args = p.parse_args()
    original_path = args.original_class.resolve(strict=True)
    output = args.output_class.resolve()
    if output.exists() or output == original_path:
        p.error("Refusing to overwrite the original or existing output")
    original = original_path.read_bytes()
    result = patch_official(original)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(result)
    print("LABORATORY CLASS ONLY. Original SHA256", hashlib.sha256(original).hexdigest())
    print("Patched class SHA256", hashlib.sha256(result).hexdigest())
    print("No installed game, saves, league files, DRM or executable modified")


if __name__ == "__main__":
    main()
