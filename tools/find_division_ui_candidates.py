#!/usr/bin/env python3
"""Read-only ranked UI class search; does not extract/modify/print game bytecode."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import zipfile

UI_MARKERS = {
    'combo': b'javax/swing/JComboBox',
    'checkbox': b'javax/swing/JCheckBox',
    'radio': b'javax/swing/JRadioButton',
    'list': b'javax/swing/JList',
    'selector': b'getSelectedItem',
    'selectedIndex': b'getSelectedIndex',
}
TEXT_MARKERS = {
    'division': (b'divis', b'Divis', b'DIVIS'),
    'national': (b'nacional', b'Nacional', b'NACIONAIS'),
    'estaduais': (b'estadual', b'Estadual', b'estaduais'),
    'jogando': (b'Jogando', b'jogando'),
    'series': (b'Serie A', b'S\xc3\xa9rie A', b'1\xc2\xaa', b'2\xc2\xaa', b'3\xc2\xaa'),
}


def inspect(path: Path) -> dict:
    if path.stat().st_size > 200_000_000 or not zipfile.is_zipfile(path):
        raise ValueError('Expected embedded game JAR')
    candidates = []
    with zipfile.ZipFile(path) as z:
        classes = [i for i in z.infolist() if i.filename.endswith('.class')]
        if len(classes) > 20000:
            raise ValueError('Excessive number of classes')
        for info in classes:
            if (info.file_size > 3_000_000 or info.compress_size == 0
                    or info.file_size > 100 * info.compress_size):
                continue
            data = z.read(info)
            if not data.startswith(bytes.fromhex('cafebabe')):
                continue
            counts = {tag: data.count(val) for tag, val in UI_MARKERS.items()}
            texts = [tag for tag, variants in TEXT_MARKERS.items() if any(v in data for v in variants)]
            if not counts['combo'] and not counts['checkbox'] and not counts['radio'] and not texts:
                continue
            score = (2 * min(6, counts['combo']) + 3 * min(6, counts['checkbox']) +
                     3 * min(6, counts['radio']) + 2 * min(5, counts['list']) +
                     8 * len(texts) + min(6, counts['selector'] + counts['selectedIndex']))
            candidates.append({'class': info.filename, 'score': score,
                'uiMarkers': {tag: n for tag, n in counts.items() if n}, 'textIndicators': texts})
    return {'readOnly': True, 'competitionMappingVerified': False,
        'classCandidates': sorted(candidates, key=lambda c: (-c['score'], c['class']))[:50]}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--game-exe', required=True, type=Path)
    print(json.dumps(inspect(p.parse_args().game_exe), ensure_ascii=False, indent=2))
