#!/usr/bin/env python3
"""Read-only report of career JComboBox fields and calls in an embedded JAR.

Never modifies game; output contains method names, line numbers and instruction
signatures only, never class bytes or original game resources.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

CLASS_PATH = 'a/hU.class'
MAX_ARCHIVE_BYTES = 200 * 1024 * 1024
MAX_CLASS_BYTES = 3 * 1024 * 1024
METHOD = re.compile(r'^\s{2}(?:public|private|protected)\s+[^\n]*\(.*\)(?:\s+throws[^;]+)?;$')
COMBO_FIELD = re.compile(r'Field\s+([A-Za-z_][\w$]*):Ljavax/swing/JComboBox;')
COMBO_CALL = re.compile(r'Method javax/swing/JComboBox\.([\w$]+):')
ENGINE_CALL = re.compile(r'Method best/f\.([\w$]+):')


def trace(archive: Path) -> dict:
    archive = archive.resolve(strict=True)
    if archive.stat().st_size > MAX_ARCHIVE_BYTES or not zipfile.is_zipfile(archive):
        raise ValueError('Expected a normal game exe containing a ZIP/JAR')
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        if sum(x.filename == CLASS_PATH for x in entries) != 1:
            raise ValueError('Career dialog class missing or duplicated')
        entry = z.getinfo(CLASS_PATH)
        if (entry.file_size > MAX_CLASS_BYTES or entry.compress_size == 0
                or entry.file_size > 100 * entry.compress_size):
            raise ValueError('Unsafe Java class size/compression ratio')
        cls = z.read(entry)
    if not cls.startswith(b'\xca\xfe\xba\xbe'):
        raise ValueError('Not a JVM class file')
    with tempfile.TemporaryDirectory(prefix='brasfoot-structure-only-') as temp:
        target = Path(temp) / CLASS_PATH
        target.parent.mkdir(parents=True)
        target.write_bytes(cls)
        command = subprocess.run(['javap', '-p', '-c', str(target)], capture_output=True,
                                 text=True, timeout=40, check=True)
    lines = command.stdout.splitlines()
    current = None
    methods = []
    for line in lines:
        if METHOD.match(line):
            current = {'method': line.strip(), 'comboFields': collections.Counter(),
                       'comboActions': collections.Counter(), 'engineCalls': collections.Counter(),
                       'selectorSnippets': []}
            methods.append(current)
            continue
        if current is None:
            continue
        field = COMBO_FIELD.search(line)
        combo = COMBO_CALL.search(line)
        engine = ENGINE_CALL.search(line)
        if field:
            current['comboFields'][field.group(1)] += 1
        if combo:
            current['comboActions'][combo.group(1)] += 1
        if engine:
            current['engineCalls'][engine.group(1)] += 1
    # Second pass: bounded evidence from immediately preceding instructions.
    current = None
    recent = collections.deque(maxlen=9)
    for line in lines:
        if METHOD.match(line):
            current = next((m for m in methods if m['method'] == line.strip()), None)
            recent.clear()
            continue
        if current is not None and ('JComboBox.getSelectedIndex:' in line
                                    or 'JComboBox.getSelectedItem:' in line
                                    or 'JComboBox.setModel:' in line
                                    or 'JComboBox.addItem:' in line):
            if len(current['selectorSnippets']) < 12:
                current['selectorSnippets'].append([x.strip()[:170] for x in recent][-6:] + [line.strip()[:170]])
        recent.append(line)
    useful = [m for m in methods if m['comboFields'] or m['comboActions']]
    all_fields = sorted({f for m in useful for f in m['comboFields']})
    for m in useful:
        for key in ('comboFields', 'comboActions', 'engineCalls'):
            m[key] = dict(m[key])
    return {
        'schemaVersion': 1, 'class': CLASS_PATH, 'sha256': hashlib.sha256(cls).hexdigest(),
        'readOnly': True, 'gameplayConfirmed': False, 'divisionMappingConfirmed': False,
        'comboFieldNames': all_fields, 'methodsWithComboReferences': useful,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-exe', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(trace(args.game_exe), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
