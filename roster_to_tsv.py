#!/usr/bin/env python3
"""Convert exported Brasfoot JSON to validated TSV for the Java .ban writer.
Input format: exported club JSON with a 'players' list. Does not alter any file
from Brasfoot. Do not confuse these 2022-23 snapshots with 2026 squads.
"""
import argparse
import base64
import json
from pathlib import Path

COLUMNS=('name','aid','b','c','d','e','f','g','h','hash','i','j','sid','tid')

def generate(source: Path, target: Path):
    raw=json.loads(source.read_text(encoding='utf-8-sig'))
    players=raw.get('players')
    if not isinstance(players,list) or not 16<=len(players)<=40:
        raise ValueError('Esperados 16 a 40 jogadores em players')
    data=[]
    for p in players:
        if set(COLUMNS)-set(p): raise ValueError('Campos de jogador ausentes: '+repr(set(COLUMNS)-set(p)))
        line=[]
        for k in COLUMNS:
            v=p[k]
            if k=='name':
                if not isinstance(v,str) or not v.strip(): raise ValueError('Nome vazio')
                line.append(base64.b64encode(v.encode('utf-8')).decode('ascii'))
            elif k in ('b','j'):
                if not isinstance(v,bool): raise ValueError('Booleano inválido: '+k)
                line.append(str(v).lower())
            else:
                if type(v) is not int: raise ValueError('Inteiro inválido: '+k)
                line.append(str(v))
        data.append('\t'.join(line))
    if target.exists(): raise FileExistsError(str(target))
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text('\n'.join(data)+'\n',encoding='utf-8')
    return len(players)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps({'players':generate(args.json,args.out),'output':str(args.out)}))
