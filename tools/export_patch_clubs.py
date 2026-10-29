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


def export(report_path, output):
    report = read(report_path)
    edition = read(ROOT/'config/edition.json')
    manifest = read(ROOT/'windows-installer/bundled_release/manifest.json')
    if report['version'] != edition['version'] or manifest['version'] != edition['version']:
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
    for filename in (f"rosters-{edition['version']}.json",'live-rosters-supplement.json'):
        for club in read(ROOT/'config'/filename)['clubs']:
            sources[club['teamFile']] = club
    known_targets = {x['path']: x['sha256'] for x in manifest['files']}
    clubs = []
    country_counts = Counter()
    coverage_counts = Counter()
    for row in report['clubs']:
        file = row['teamFile']
        compiled = report_path.parent/'teams'/Path(file).name
        if file in known_targets and hashlib.sha256(compiled.read_bytes()).hexdigest() != known_targets[file]:
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
        clubs.append({'id':club_id,'name':name,'aliases':aliases,
                      'countryId':country_id,'country':country,'competition':competition,
                      'division':division,'state':domestic.get('state'),
                      'coverage':coverage,'coverageLabel':LABELS[coverage],
                      'teamFile':file,'playerCount':len(players),'players':players,
                      'sourceUrl':row['sourceUrl'],'observedAt':row['observedAt']})
        country_counts[country_id] += 1
        coverage_counts[coverage] += 1
    result = {'schemaVersion':1,'version':report['version'],
              'generatedAt':datetime.now(timezone.utc).isoformat(),
              'totalClubs':len(clubs),'totalPlayers':sum(c['playerCount'] for c in clubs),
              'totalCountries':len(country_counts),'coverage':dict(coverage_counts),
              'provenance':{'compilerReportSha256':hashlib.sha256(report_path.read_bytes()).hexdigest(),
                            'scope':'All clubs in the resulting game, including unchanged original squads',
                            'individualAttributes':'Game values may be preserved or estimated; not independently verified'},
              'countries':sorted([{'id':ident,'name':country_names[str(ident)],'count':count}
                                  for ident,count in country_counts.items()],key=lambda c:c['name']),
              'clubs':sorted(clubs,key=lambda c:c['name'].casefold())}
    if (result['totalClubs'] != report['counts']['teamsTotal'] or
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
