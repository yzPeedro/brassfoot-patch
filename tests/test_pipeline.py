"""Run: python -m unittest discover -s tests -v
Tests against samples need a user-supplied zip, no game data is redistributed.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import subprocess
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from catalog import analyze, resolve_2026_clubs
from roster_to_tsv import generate


class CatalogTests(unittest.TestCase):
    def test_tiny_mock(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)
            team={'name':'Teste','id':'teste_bra','stadium':'','manager':'',
                  'primaryColor':'#ffffff','secondaryColor':'#000000',
                  'a':29,'aid':0,'b':0,'c':12,'g':1000,'i':29,'internalId':0,
                  'n':0,'o':0,'sid':0,'tid':0,'valid':True,'vid':185,
                  'players':[{'name':f'Jogador {i}','aid':0,'b':False,'c':29,'d':24,'e':i%5,
                  'f':0,'g':7,'h':9,'hash':5,'i':0,'j':False,'sid':0,'tid':i+1} for i in range(18)],
                  'secondaryPlayers':[]}
            with zipfile.ZipFile(root/'fake.zip','w') as z:
                z.writestr('teste_bra.ban.json',json.dumps(team))
            result=analyze(root/'fake.zip',root/'output')
            self.assertEqual(result['teamCount'],1)
            self.assertEqual(result['players'],18)
            self.assertEqual(result['serieA2026Missing'],20)
            self.assertTrue((root/'output'/'catalog-2022-23.sqlite').is_file())
            (root/'test.json').write_text(json.dumps(team),encoding='utf-8')
            self.assertEqual(generate(root/'test.json',root/'squad.tsv'),18)

    def test_normalized_real_world_club_names_and_aliases(self):
        teams=[{'id':club_id,'name':name,'a':29} for club_id,name in [
            ('flarj','Flamengo'),('flurj','Fluminense'),
            ('miirassol_sp','Mirassol'),('bragantino_bra','RB Bragantino'),
            ('vasco','Vasco'),('gremio','Grêmio'),
        ]]
        teams.append({'id':'fluminenseba_bra','name':'Fluminense Feira','a':29})
        results={item['club']: item['id'] for item in resolve_2026_clubs(teams)}
        self.assertEqual(results['Flamengo'],'flarj')
        self.assertEqual(results['Fluminense'],'flurj')
        self.assertEqual(results['Mirassol'],'miirassol_sp')
        self.assertEqual(results['Red Bull Bragantino'],'bragantino_bra')
        self.assertEqual(results['Vasco da Gama'],'vasco')
        self.assertEqual(results['Grêmio'],'gremio')

    def test_reject_ambiguous_country_matched_team(self):
        teams=[{'id':'a','name':'Flamengo','a':29},
               {'id':'b','name':'Flamengo','a':29}]
        with self.assertRaisesRegex(ValueError,'ambígua'):
            resolve_2026_clubs(teams)

    def test_non_brazilian_names_not_inferred_as_brazil(self):
        teams=[{'id':'foreign','name':'Flamengo','a':100}]
        resolved={item['club']: item['id'] for item in resolve_2026_clubs(teams)}
        self.assertIsNone(resolved['Flamengo'])

    def test_bad_roster_rejected(self):
        with TemporaryDirectory() as t:
            a=Path(t)/'bad.json';a.write_text('{"players": []}',encoding='utf8')
            with self.assertRaises(ValueError):generate(a,Path(t)/'out.tsv')

    def test_replace_roster_with_player_change(self):
        archive=ROOT/'input'/'brassfoot-amostras.zip'
        if not archive.exists(): self.skipTest('Arquivo de amostras do usuário não incluído')
        with TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            classes=tmp/'classes'; classes.mkdir()
            subprocess.run(['javac','-encoding','UTF-8','-d',str(classes),
                *map(str,(ROOT/'src').rglob('*.java'))],check=True)
            with zipfile.ZipFile(archive) as z:
                n=next(n for n in z.namelist() if n.endswith('cruzeiro_bra.ban'))
                original=tmp/'cruzeiro_bra.ban'; original.write_bytes(z.read(n))
            cmd=['java','-cp',str(classes),'app.Main']
            obj=json.loads(subprocess.run([*cmd,'inspect',str(original)],capture_output=True,text=True,check=True).stdout)
            modified=json.loads(json.dumps(obj))
            modified['players'][0]['name']='Automated Test Player'
            newp=dict(modified['players'][-1]);newp['name']='New Synthetic Test Player';newp['tid']=0
            modified['players'].append(newp)
            source=tmp/'roster.json';source.write_text(json.dumps(modified),encoding='utf-8')
            tsv=tmp/'roster.tsv';generate(source,tsv)
            destination=tmp/'cruzeiro-patched.ban'
            subprocess.run([*cmd,'replace-roster',str(original),str(tsv),str(destination)],capture_output=True,text=True,check=True)
            decoded=json.loads(subprocess.run([*cmd,'inspect',str(destination)],capture_output=True,text=True,check=True).stdout)
            self.assertEqual(decoded,modified)
            self.assertEqual(json.loads(subprocess.run([*cmd,'inspect',str(original)],capture_output=True,text=True,check=True).stdout),obj)
            self.assertNotEqual(original.read_bytes(),destination.read_bytes())

    def test_all_user_sample_roundtrips_when_archive_available(self):
        archive=ROOT/'input'/'brassfoot-amostras.zip'
        if not archive.exists():self.skipTest('Arquivo de amostras do usuário não incluído')
        with TemporaryDirectory() as temp:
            build=Path(temp);classes=build/'classes';classes.mkdir()
            sources=[str(x) for x in (ROOT/'src').rglob('*.java')]
            subprocess.run(['javac','-encoding','UTF-8','-d',str(classes),*sources],check=True)
            with zipfile.ZipFile(archive) as z:
                for n in z.namelist():
                    if not n.endswith('.ban'):continue
                    orig=build/Path(n).name
                    orig.write_bytes(z.read(n))
                    cmd=['java','-cp',str(classes),'app.Main']
                    exported=build/(orig.name+'.json')
                    exported.write_text(subprocess.run([*cmd,'inspect',str(orig)],capture_output=True,text=True,check=True).stdout,encoding='utf-8')
                    roster=build/(orig.name+'.tsv');generate(exported,roster)
                    rebuilt=build/(orig.name+'.rebuilt')
                    subprocess.run([*cmd,'replace-roster',str(orig),str(roster),str(rebuilt)],check=True,capture_output=True)
                    self.assertEqual(orig.read_bytes(),rebuilt.read_bytes(),orig.name)


if __name__=='__main__':unittest.main()
