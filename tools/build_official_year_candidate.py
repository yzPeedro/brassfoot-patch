#!/usr/bin/env python3
"""Build a separate, EXPERIMENTAL candidate from the known official Brasfoot game.

It does not execute or overwrite the original game, change career saves, or
modify licensing code. A synthetic test is NOT gameplay validation.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import os
from pathlib import Path
import zipfile

if __package__:
    from .patch_official_career_year import patch_official
else:
    from patch_official_career_year import patch_official

OFFICIAL_EXE_SIZE = 7_320_384
OFFICIAL_FINGERPRINTS = {
    "a/hU.class": "37fb17d876aab1263756bca97c3f9488007b7afe59f8c68494cf711a0f61a234",
    "best/f.class": "dbd5bd8633e3a1c2f211e8bd6c322db8f7401c5ccf7cc622cc4050f0624df71b",
    "best/p.class": "466327e6cedae77503021dd222a33bf9163e453b639ebc29a399d9d851f4c256",
}
OFFICIAL_PATCHED_SELECTOR_SHA = "9cb4b93ff5bc52bfe364c545128ecc69c7d5615d1c09d6ba01ca34d4c35dc591"
MAX_ENTRIES = 4000
MAX_ENTRY_UNCOMPRESSED = 10 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED = 160 * 1024 * 1024


class CandidateError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_candidate(original: Path, output: Path) -> dict:
    original = original.resolve(strict=True)
    output = output.resolve()
    if not original.is_file() or original.name.lower() != 'bf22-23.exe':
        raise CandidateError('Requires the original extracted bf22-23.exe, not the setup installer')
    if output.suffix.lower() != '.exe' or output == original or output.exists():
        raise CandidateError('Output must be a new separate .exe path')
    if output.is_relative_to(original.parent):
        raise CandidateError('Output cannot be inside the source game folder')
    if original.stat().st_size != OFFICIAL_EXE_SIZE:
        raise CandidateError('Executable size differs from the verified official release')
    with original.open('rb') as file:
        if file.read(2) != b'MZ':
            raise CandidateError('Original must be a PE executable')
    if not zipfile.is_zipfile(original):
        raise CandidateError('Original does not contain a readable embedded JAR')
    with zipfile.ZipFile(original, 'r') as archive:
        files = archive.infolist()
        names = [f.filename for f in files]
        if (len(names) != len(set(names)) or not 1 <= len(names) <= MAX_ENTRIES
                or any(f.flag_bits & 1 for f in files)):
            raise CandidateError('Ambiguous, encrypted or oversized Java container')
        if (any(f.file_size > MAX_ENTRY_UNCOMPRESSED or
                f.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED) for f in files)
                or sum(f.file_size for f in files) > MAX_TOTAL_UNCOMPRESSED):
            raise CandidateError('Embedded archive exceeds safe extraction limits')
        if not set(OFFICIAL_FINGERPRINTS).issubset(names):
            raise CandidateError('Expected original Java classes are missing')
        for name, sha in OFFICIAL_FINGERPRINTS.items():
            if digest(archive.read(name)) != sha:
                raise CandidateError(f'Original code fingerprint mismatch in {name}')
        selector = patch_official(archive.read('a/hU.class'))
        if digest(selector) != OFFICIAL_PATCHED_SELECTOR_SHA:
            raise CandidateError('Patched selector differs from the verified laboratory result')
        if archive.testzip() is not None:
            raise CandidateError('CRC verification failed in the original archive')
        prefix_size = min(item.header_offset for item in files)
        if not 128 <= prefix_size <= OFFICIAL_EXE_SIZE:
            raise CandidateError('Invalid Windows launcher prefix')
        prefix = original.read_bytes()[:prefix_size]
        if not prefix.startswith(b'MZ'):
            raise CandidateError('Launcher prefix is missing MZ signature')
        output.parent.mkdir(parents=True, exist_ok=True)
        # Only a distinct new file is ever created. On error, it is deleted.
        try:
            with output.open('xb') as out:
                out.write(prefix)
                with zipfile.ZipFile(out, 'w', allowZip64=True) as updated:
                    updated.comment = archive.comment
                    for member in files:
                        data = selector if member.filename == 'a/hU.class' else archive.read(member)
                        info = copy.copy(member)
                        info.header_offset = 0
                        updated.writestr(info, data)
                out.flush()
                os.fsync(out.fileno())
            with zipfile.ZipFile(output) as updated:
                if updated.testzip() is not None or updated.namelist() != names:
                    raise CandidateError('Reconstructed archive integrity check failed')
                if digest(updated.read('a/hU.class')) != OFFICIAL_PATCHED_SELECTOR_SHA:
                    raise CandidateError('The updated selector differs from the intended patch')
                for name in names:
                    if name == 'a/hU.class':
                        continue
                    if digest(updated.read(name)) != digest(archive.read(name)):
                        raise CandidateError(f'Unrelated game file was modified: {name}')
            with output.open('rb') as file:
                if file.read(prefix_size) != prefix:
                    raise CandidateError('Original launcher prefix was modified')
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    return {
        'output': str(output), 'outputSha256': digest(output.read_bytes()),
        'changedJavaClasses': ['a/hU.class'], 'unmodifiedEntries': len(names)-1,
        'changedExistingGameOrSaves': False,
        'verifiedInRealBrasfoot': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-exe', type=Path, required=True)
    parser.add_argument('--output-exe', type=Path, required=True)
    parser.add_argument('--experimental', action='store_true', required=True,
                        help='Acknowledge no real-game validation has been performed')
    args = parser.parse_args()
    try:
        print(build_candidate(args.original_exe, args.output_exe))
    except (OSError, CandidateError, zipfile.BadZipFile) as exc:
        parser.exit(1, f'REJECTED (no installed files modified): {exc}\n')


if __name__ == '__main__':
    main()
