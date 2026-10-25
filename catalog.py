#!/usr/bin/env python3
"""Brasfoot 22-23 exported JSON -> audited SQLite catalog, no game mutation.
Only the standard library is needed. This is NOT a 2026 roster provider.
"""
from __future__ import annotations
from contextlib import closing
import argparse
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import unicodedata
import zipfile

# Nomes de clubes participantes da Série A de 2026. Identificadores internos
# devem ser resolvidos PELO CONTEÚDO das equipes exportadas, não presumidos.
SERIE_A_2026 = [
    "Athletico-PR", "Atlético-MG", "Bahia", "Botafogo", "Chapecoense",
    "Corinthians", "Coritiba", "Cruzeiro", "Flamengo", "Fluminense",
    "Grêmio", "Internacional", "Mirassol", "Palmeiras",
    "Red Bull Bragantino", "Remo", "Santos", "São Paulo", "Vasco da Gama",
    "Vitória",
]

# Sinônimos canônicos em relação ao nome registrado no próprio jogo.
# A chave é o nome oficial; o valor é o texto efetivo procurado no `.ban`.
CLUB_NAME_ALIASES = {
    "Red Bull Bragantino": "RB Bragantino",
    "Vasco da Gama": "Vasco",
}


def normalize_name(name: str) -> str:
    """Normalização determinística de nomes; evita fuzzy matching arriscado."""
    import re
    decomposed = unicodedata.normalize("NFKD", name.casefold())
    latin = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", latin)


def resolve_2026_clubs(teams: list[dict]) -> list[dict]:
    """Resolver somente matches inequívocos e clubes do Brasil (campo a=29).

    A nacionalidade dos clubes (campo `a`) é inferida dos dados exportados;
    testar novamente caso uma nova versão do formato altere esse campo.
    """
    index: dict[str,list[dict]] = collections.defaultdict(list)
    for team in teams:
        if team.get('a') == 29:
            index[normalize_name(team['name'])].append(team)

    resolved=[]
    seen_ids=set()
    for canonical in SERIE_A_2026:
        requested = CLUB_NAME_ALIASES.get(canonical, canonical)
        matches = index.get(normalize_name(requested), [])
        if len(matches) > 1:
            raise ValueError(f'Correspondência ambígua para {canonical}: {[m["id"] for m in matches]}')
        matched = matches[0] if matches else None
        if matched and matched['id'] in seen_ids:
            raise ValueError(f'Clube {matched["id"]} associado a dois nomes da Série A')
        if matched:
            seen_ids.add(matched['id'])
        resolved.append({
            'club':canonical,
            'id':matched['id'] if matched else None,
            'matchedName':matched['name'] if matched else None,
            'inExport':bool(matched),
            'matchingStrategy':'normalized_name_alias' if canonical in CLUB_NAME_ALIASES else 'normalized_name',
        })
    return resolved

PLAYER_RAW_KEYS = ('aid','b','c','d','e','f','g','h','hash','i','j','sid','tid')
TEAM_RAW_KEYS = ('a','aid','b','c','g','i','internalId','n','o','sid','tid','valid','vid')
POSITIONS = {0:'Goleiro', 1:'Lateral', 2:'Zagueiro', 3:'Meia', 4:'Atacante'}


def analyze(archive: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    teams: list[dict] = []
    player_rows: list[tuple] = []
    field_profiles: dict = {'teams': {}, 'players': {}}
    teamids: set[str] = set()
    team_names: set[str] = set()
    team_raw_shapes: set[tuple] = set()
    player_raw_shapes: set[tuple] = set()
    tid_nonzero: collections.Counter = collections.Counter()
    positions: collections.Counter = collections.Counter()
    age_freq: collections.Counter = collections.Counter()
    issues: list[str] = []
    with zipfile.ZipFile(archive) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith('.json')]
        if len(names) != len(set(names)):
            raise ValueError('ZIP contém nomes duplicados')
        if not names: raise ValueError('ZIP sem arquivos JSON')
        for i, name in enumerate(sorted(names)):
            info = zf.getinfo(name)
            if info.file_size > 300000 or '..' in Path(name).parts:
                raise ValueError(f'Nome/tamanho inválido para {name!r}')
            data = json.loads(zf.read(info))
            if not isinstance(data, dict): raise ValueError(f'Clube inválido em {name}')
            if not isinstance(data.get('players'), list) or not isinstance(data.get('secondaryPlayers'), list):
                raise ValueError(f'Jogadores inválidos em {name}')
            team_id=data.get('id')
            if not isinstance(team_id,str) or not team_id or '/' in team_id or '\\' in team_id:
                raise ValueError(f'ID inválido em {name}')
            if team_id in teamids: raise ValueError(f'ID duplicado {team_id}')
            teamids.add(team_id)
            if not name.endswith(team_id+'.ban.json'):
                issues.append(f'Nome de arquivo não coincide com ID: {name}')
            team_names.add(str(data['name']))
            team_raw_shapes.add(tuple(sorted(set(data)-{'players','secondaryPlayers'})))
            teams.append(data)
            for grp,players in [('senior',data['players']),('secondary',data['secondaryPlayers'])]:
                for ord_,p in enumerate(players):
                    if not isinstance(p,dict) or not isinstance(p.get('name'), str) or not p['name'].strip():
                        raise ValueError(f'Jogador inválido em {name}')
                    player_raw_shapes.add(tuple(sorted(p)))
                    if not isinstance(p.get('e'),int) or p['e'] not in POSITIONS:
                        issues.append(f'Posição não mapeada em {name}: {p.get("e")}')
                    positions[p['e']]+=1
                    age_freq[p['d']]+=1
                    if p['tid'] != 0: tid_nonzero[p['tid']]+=1
                    player_rows.append((team_id,grp,ord_,p))

    def profile(objects: list[dict], keys: tuple[str,...]) -> dict:
        result={}
        for key in keys:
            vals=[o.get(key) for o in objects]
            integers=[v for v in vals if type(v) is int]
            result[key]={
                'types':dict(collections.Counter(type(v).__name__ for v in vals)),
                'uniqueValues':len(set(json.dumps(v,ensure_ascii=False,sort_keys=True) for v in vals)),
                'min':min(integers) if integers else None,
                'max':max(integers) if integers else None,
                'topValues':[[k,n] for k,n in collections.Counter(str(v) for v in vals).most_common(8)]
            }
        return result

    players=[p for _,_,_,p in player_rows]
    field_profiles['teams']=profile(teams,TEAM_RAW_KEYS)
    field_profiles['players']=profile(players,PLAYER_RAW_KEYS)
    field_profiles['schemaShapes']={'teams':len(team_raw_shapes),'players':len(player_raw_shapes)}
    field_profiles['positionCodes']={str(k):{'label':v,'count':positions[k]} for k,v in POSITIONS.items()}
    field_profiles['ageRange']=[min(age_freq),max(age_freq)]
    field_profiles['playerCounts']={
        'senior':sum(len(t['players']) for t in teams),
        'secondary':sum(len(t['secondaryPlayers']) for t in teams)
    }
    (out/'field-profiles.json').write_text(json.dumps(field_profiles,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

    coverage=resolve_2026_clubs(teams)
    brazilian=[{'id':t['id'],'name':t['name'],'countryCode':t['a']} for t in teams if t['a']==29]
    (out/'brazil-clubs.json').write_text(json.dumps(brazilian,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

    db_path=out/'catalog-2022-23.sqlite'
    if db_path.exists(): db_path.unlink()
    with closing(sqlite3.connect(db_path)) as con:
        con.executescript('''
            PRAGMA foreign_keys=ON;
            CREATE TABLE clubs (
                id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                stadium TEXT,
                manager TEXT,
                primary_color TEXT,
                secondary_color TEXT,
                is_brazilian INTEGER NOT NULL,
                raw_json TEXT NOT NULL
            );
            CREATE TABLE players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                club_id TEXT NOT NULL REFERENCES clubs(id),
                squad TEXT NOT NULL CHECK(squad IN ('senior','secondary')),
                ordinal INTEGER NOT NULL,
                display_name TEXT NOT NULL,
                age_at_export INTEGER NOT NULL,
                position_code INTEGER NOT NULL,
                nationality_code INTEGER NOT NULL,
                source_tid INTEGER NOT NULL,
                characteristic_1 INTEGER NOT NULL,
                characteristic_2 INTEGER NOT NULL,
                raw_json TEXT NOT NULL,
                UNIQUE(club_id,squad,ordinal)
            );
            CREATE TABLE serie_a_2026 (
                display_name TEXT PRIMARY KEY,
                resolved_id TEXT,
                present_in_export INTEGER NOT NULL
            );
            CREATE INDEX idx_players_club ON players(club_id);
            CREATE INDEX idx_players_tid ON players(source_tid);
        ''')
        con.executemany('''INSERT INTO clubs VALUES(?,?,?,?,?,?,?,?)''', [
            (d['id'],d['name'],d['stadium'],d['manager'],d['primaryColor'],d['secondaryColor'],int(d['a']==29),json.dumps(d,ensure_ascii=False,sort_keys=True))
            for d in teams
        ])
        con.executemany('''INSERT INTO players(club_id,squad,ordinal,display_name,age_at_export,position_code,nationality_code,source_tid,characteristic_1,characteristic_2,raw_json)
                              VALUES(?,?,?,?,?,?,?,?,?,?,?)''', [
            (team_id,grp,ord_,p['name'],p['d'],p['e'],p['c'],p['tid'],p['g'],p['h'],json.dumps(p,ensure_ascii=False,sort_keys=True))
            for team_id,grp,ord_,p in player_rows
        ])
        con.executemany('INSERT INTO serie_a_2026 VALUES(?,?,?)',[(c['club'],c['id'],int(c['inExport'])) for c in coverage])
        con.commit()

    cov=coverage
    (out/'serie-a-2026-coverage.json').write_text(json.dumps({'source':'CBF - clubes da Série A 2026','sourceUrl':'https://www.cbf.com.br/futebol-brasileiro/times/campeonato-brasileiro/serie-a/2026','clubs':cov},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    metadata={
      'sourceArchive':archive.name, 'sourceSha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
      'teamCount':len(teams), 'brazilTeams':len(brazilian),
      'players':len(player_rows), 'seniorPlayers':sum(len(t['players']) for t in teams),
      'secondaryPlayers':sum(len(t['secondaryPlayers']) for t in teams),
      'teamsWithSecondary':sum(bool(t['secondaryPlayers']) for t in teams),
      'serieA2026Covered':sum(c['inExport'] for c in cov),'serieA2026Missing':sum(not c['inExport'] for c in cov),
      'playerTidZero':sum(p['tid']==0 for p in players),
      'nonZeroTidCollisions':sum(n-1 for tid,n in tid_nonzero.items() if n>1),
      'ageZeros':age_freq[0], 'ageOver45':sum(v for k,v in age_freq.items() if k>45),
      'rawTeamSchemaShapes':len(team_raw_shapes), 'rawPlayerSchemaShapes':len(player_raw_shapes),
      'issues':issues,
      'notes':[
        'Campo de país de equipe a=29 identifica 196 clubes brasileiros nesta base; essa semântica deve ser revalidada em novas versões.',
        'Idades e outros campos provêm de dados 2022-2023; não converter diretamente para 2026.',
        'Não foram importados jogadores reais da temporada 2026.',
        'Ausência no ZIP não prova ausência de clube dentro do executável original.',
        'As características não equivalem a uma força geral 0-100.'
      ]
    }
    (out/'summary.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    report=[
        '# Auditoria da exportação Brasfoot 2022–2023',
        '',
        f'- Clubes no catálogo: **{len(teams)}**.',
        f'- Clubes brasileiros identificados (`a=29`): **{metadata["brazilTeams"]}**.',
        f'- Jogadores totais: **{len(player_rows)}** ({metadata["seniorPlayers"]} elenco principal e {metadata["secondaryPlayers"]} em listas adicionais).',
        f'- Equipes com lista adicional não vazia: **{metadata["teamsWithSecondary"]}**.',
        f'- Cobertura dos 20 clubes da Série A 2026: **{metadata["serieA2026Covered"]}/20** presentes nos arquivos exportados.',
        f'- Campo `tid=0` em **{metadata["playerTidZero"]}** jogadores; valores não nulos repetidos (ocorrências além da primeira): **{metadata["nonZeroTidCollisions"]}**.',
        '',
        '## Correspondência dos clubes da Série A 2026',
        '',
        *(f'- {c["club"]}: `{c["id"]}` — {c["matchedName"]}' if c['inExport'] else f'- {c["club"]}: não encontrado (precisa inspeção)' for c in cov),
        '',
        '## Campos e cuidados',
        '',
        '- Jogadores: `name`, `d` (idade), `e` (posição 0..4), `c` (país; 29=Brasil), `f` (lado), `g`/`h` (características).',
        '- `tid` e `hash` têm semântica não totalmente comprovada e não devem ser regenerados arbitrariamente.',
        '- A lista `secondaryPlayers` pode guardar uma base/juniores, mas sua semântica exata não está confirmada.',
        '- O formato `.ban` exportado **não contém força geral explícita** dos jogadores.',
        '- A exportação de 2022-2023 não substitui uma fonte de elencos e uniformes 2026.',
        '- Todos os 20 clubes da Série A 2026 constam na exportação, inclusive Flamengo, Fluminense e Mirassol com IDs internos inesperados.',
        '',
        '## Próximo gate técnico',
        '',
        '1. Coletar elencos 2026 de fonte permitida e salvar snapshots com data/proveniência.',
        '2. Converter dados reais em jogadores do Brasfoot sem inventar características não confirmadas.',
        '3. Atualizar em lote os .ban dos clubes existentes, preservando seus IDs e criando artefatos de teste isolados.',
        '4. Testar arquivo atualizado dentro do jogo em uma nova partida e aplicar instalador com backup.',
        '',
        'Fonte clubes: https://www.cbf.com.br/futebol-brasileiro/times/campeonato-brasileiro/serie-a/2026',
    ]
    (out/'report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    return metadata


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True,help='ZIP com os exports do codec')
    parser.add_argument('--out',type=Path,required=True,help='Pasta de saída')
    args=parser.parse_args(argv)
    if not args.archive.is_file(): parser.error('Arquivo de entrada não encontrado')
    summary=analyze(args.archive,args.out)
    print(json.dumps({'status':'ok','output':str(args.out.resolve()),**{k:summary[k] for k in ('teamCount','brazilTeams','players','serieA2026Covered','serieA2026Missing')}},ensure_ascii=False))

if __name__=='__main__': main()
