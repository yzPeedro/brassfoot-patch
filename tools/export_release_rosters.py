"""Export the actual compiled roster lists and their coverage to the website."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def write(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def export(report_path):
    report=json.loads(report_path.read_text(encoding='utf8'))
    mapped=json.loads((ROOT/'data/competitions/2026-abc-original-file-map.json').read_text(encoding='utf8'))
    by_file={c['teamFile']:c for c in report['clubs']}
    clubs={}
    for row in mapped['clubs']:
        file=row['originalTeamFile'] or 'teams/maranhao_ma.ban'
        result=by_file[file]
        clubs[row['clubId']]={'division':row['division'],'teamFile':file,'includedInPackage':True,
                              'sourceUrl':result['sourceUrl'],'reviewedOn':result['observedAt'][:10],
                              'rosterPolicy':result['rosterPolicy'],
                              'players':[p['name'] for p in result['finalPlayers']],
                              'positionCodes':[p['positionCode'] for p in result['finalPlayers']]}
    version=report['version']
    public={'schemaVersion':3,'season':2026,'sourceRelease':version,'includedInPackage':True,
            'totalClubs':len(clubs),'totalPlayers':sum(len(c['players'])for c in clubs.values()),'clubs':clubs}
    write(ROOT/'site/data/published-rosters-2026.json',public)
    target_path=ROOT/'site/data/target-abc-2026.json'
    target=json.loads(target_path.read_text(encoding='utf8'))
    target.update(activeBaselineRelease=version,publishedRosterVersion=version,
                  publishedRosterSnapshot=True,targetPlayers='compiled-sourced-squads',status='published',blockers=[])
    target.pop('experimentalABaselineClubs',None)
    target['serieD'].update(policy='configuration-preserved',doNotInstallAnySerieDTeam=False,
                           nameNormalizationIncluded=True)
    for club in target['clubs']:club['rosterStatus']='included-current-snapshot'
    write(target_path,target)
    release_path=ROOT/'site/data/release-clubs-60.json'
    current=json.loads(release_path.read_text(encoding='utf8'))
    current.update(releaseVersion=version,rosters2026={'includedClubs':60,'newBCDeltasInstalled':40})
    for club in current['clubs']:club['rosterStatus']='included-current-snapshot'
    write(release_path,current)
    coverage={'schemaVersion':1,'version':version,'date':report['referenceDate'],'counts':report['counts'],
              'limitations':report['limitations'],'clubs':[
                  {k:c[k] for k in ('teamFile','club','countryCode','sourceUrl','observedAt','rosterPolicy','compiledPlayers')}
                  for c in report['clubs'] if c['sourceUrl']], 'testsExecuted':False}
    write(ROOT/'site/data/roster-coverage.json',coverage)
    write(ROOT/'config/roster-build-2026.4.1.json',coverage)
    print(json.dumps({'publicBrazilClubs':len(clubs),'publicBrazilPlayers':public['totalPlayers'],
                      'sourceSquads':report['counts']['sourceSquads']}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True)
    export(p.parse_args().report)
