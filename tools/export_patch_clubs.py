"""Build the public explorer from the exact roster compiler output.

All clubs in the resulting game are listed, including unchanged base clubs.
Coverage is explicit; a club's presence never means its squad was updated.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRAITS = ['Colocação', 'Defesa de pênalti', 'Reflexo', 'Saída do gol',
          'Armação', 'Cabeceio', 'Cruzamento', 'Desarme', 'Drible',
          'Finalização', 'Marcação', 'Passe', 'Resistência', 'Velocidade']
LABELS = {'updated':'Elenco atualizado', 'partial':'Dados parciais', 'preserved':'Elenco preservado'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def world_entry(file, club, prior=None):
    prior = prior or {}
    coverage = 'updated' if club['replaced'] else prior.get('coverage', 'preserved')
    keep = not club['replaced']
    aliases = sorted({x for x in (*prior.get('aliases', ()), prior.get('name')) if x and x != club['name']})
    return {'id':'club-' + hashlib.sha256(file.encode('utf8')).hexdigest()[:16],'name':club['name'],
            'aliases':aliases,'countryId':club['countryId'],'competition':club['competition'],
            'division':club['division'],'state':club['state'] or prior.get('state'),
            'coverage':coverage,'coverageLabel':LABELS[coverage],'teamFile':file,
            'playerCount':len(club['players']),'players':club['players'],
            'sourceUrl':prior.get('sourceUrl') if keep else club['sourceUrl'],
            'observedAt':prior.get('observedAt') if keep else club['observedAt']}


def export(report_path, output, world=None, world_provenance=None):
    world = dict(world or {})
    report = read(report_path)
    edition = read(ROOT/'config/edition.json')
    manifest = read(ROOT/'windows-installer/bundled_release/manifest.json')
    if manifest['version'] != edition['version'] or (report['version'] != edition['version'] and not world):
        raise ValueError('compiled roster, bundle and edition must refer to the same release')
    country_names = read(ROOT/'config/brasfoot-country-names.json')
    brazil_path = ROOT/'data/competitions/2026-abc-original-file-map.json'
    if brazil_path.is_file():
        brazil = {x['originalTeamFile'] or 'teams/maranhao_ma.ban': x for x in read(brazil_path)['clubs']}
    else:
        # Public release metadata also carries the 60 stable file identities.
        published = read(ROOT/'site/data/published-rosters-2026.json')['clubs']
        catalog = {x['id']:x for x in read(ROOT/'site/data/target-abc-2026.json')['clubs']}
        brazil = {row['teamFile']:dict(catalog[ident],clubId=ident) for ident,row in published.items()}
    sources = {}
    for filename in (f"rosters-{report['version']}.json",'live-rosters-supplement.json'):
        for club in read(ROOT/'config'/filename)['clubs']:
            sources[club['teamFile']] = club
    known_targets = {x['path']: x['sha256'] for x in manifest['files']}
    clubs = []
    country_counts = Counter()
    coverage_counts = Counter()
    for row in report['clubs']:
        file = row['teamFile']
        compiled = report_path.parent/'teams'/Path(file).name
        if file in known_targets and file not in world and hashlib.sha256(compiled.read_bytes()).hexdigest() != known_targets[file]:
            raise ValueError('compiled roster differs from published patch: ' + file)
        source = sources.get(file,{})
        domestic = brazil.get(file,{})
        country_id = row['countryCode']
        country = country_names[str(country_id)]
        coverage = 'updated' if row['rosterPolicy']=='source-replacement' else 'partial' if row['sourceUrl'] else 'preserved'
        name = row['club']
        aliases = sorted({x for x in (source.get('name'),domestic.get('club'),domestic.get('name')) if x and x != name})
        division = domestic.get('division')
        competition = 'Brasileirão Série '+division if division else source.get('league') or ''
        players = [{'name':p['name'],'position':p['positionCode'],
                    'side':'Esquerdo' if p['side']==1 else 'Direito',
                    'traits':[TRAITS[t] for t in p['traits']]} for p in row['finalPlayers']]
        if len(players) != row['compiledPlayers']:
            raise ValueError('compiled player list is incomplete: '+file)
        club_id = 'club-' + hashlib.sha256(file.encode('utf8')).hexdigest()[:16]
        entry = {'id':club_id,'name':name,'aliases':aliases,
                 'countryId':country_id,'country':country,'competition':competition,
                 'division':division,'state':domestic.get('state'),
                 'coverage':coverage,'coverageLabel':LABELS[coverage],
                 'teamFile':file,'playerCount':len(players),'players':players,
                 'sourceUrl':row['sourceUrl'],'observedAt':row['observedAt']}
        if file in world:
            entry = world_entry(file, world.pop(file), entry)
        clubs.append(entry)
    expected_clubs = report['counts']['teamsTotal'] + len(world)
    for file, club in sorted(world.items()):
        if not club['new']:
            raise ValueError('world club missing from the roster report: ' + file)
        clubs.append(world_entry(file, club))
    for entry in clubs:
        entry['country'] = country_names[str(entry['countryId'])]
        country_counts[entry['countryId']] += 1
        coverage_counts[entry['coverage']] += 1
    result = {'schemaVersion':1,'version':edition['version'],
              'generatedAt':datetime.now(timezone.utc).isoformat(),
              'totalClubs':len(clubs),'totalPlayers':sum(c['playerCount'] for c in clubs),
              'totalCountries':len(country_counts),'coverage':dict(coverage_counts),
              'provenance':{'compilerReportSha256':hashlib.sha256(report_path.read_bytes()).hexdigest(),
                            'scope':'All clubs in the resulting game, including unchanged original squads',
                            'individualAttributes':'Game values may be preserved or estimated; not independently verified',
                            **(world_provenance or {})},
              'countries':sorted([{'id':ident,'name':country_names[str(ident)],'count':count}
                                  for ident,count in country_counts.items()],key=lambda c:c['name']),
              'clubs':sorted(clubs,key=lambda c:c['name'].casefold())}
    if result['totalClubs'] != expected_clubs or (not world_provenance and
            result['totalPlayers'] != report['counts']['playersTotal']):
        raise ValueError('export totals differ from the production compiler')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    print(json.dumps({k:result[k] for k in ('version','totalClubs','totalPlayers','totalCountries','coverage')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'site/data/patch-clubs.json')
    args=parser.parse_args()
    export(args.report,args.output)
