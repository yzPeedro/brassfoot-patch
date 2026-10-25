"""Reproducible release manifest: 20 A, 20 B, 20 C, 20 selected D.
Historical B/C/D squads remain old; Maranhão uses clearly marked fictional players.
Never embeds proprietary original game data.
"""
from pathlib import Path
import base64,hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"preview-builder"
BUNDLE=ROOT/"windows-installer"/"bundled_release"
SELECTED=[
("ABC","RN"),("América","RN"),("CSA","AL"),("ASA","AL"),
("Sampaio Corrêa","MA"),("Moto Club","MA"),("Ferroviário","CE"),
("Treze","PB"),("Sousa","PB"),("Sergipe","SE"),("Altos","PI"),
("Retrô","PE"),("Brasil","RS"),("Joinville","SC"),("Tuna Luso","PA"),
("Manaus","AM"),("Madureira","RJ"),("Portuguesa","RJ"),
("Luverdense","MT"),("Aparecidense","GO")
]
EXPECTED_ORIGINAL="76b7af89b81859ed8ee29f78de34ced3c48636ec0a27554c29d8d0da55bc2834"
EXPECTED_ALPHA="edda3712891e30fa212dddddbcbba9af8dd4c8a83c02d735e3b80f014a776dcd"
EXPECTED_TARGET="ded1604e7d143622b580bec9237cd7accf1a1bbe2de7ffc11b28dc02853d0503"

def h(data):return hashlib.sha256(data).hexdigest()
def put(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def cfg_recipe(original_hash,old_groups,old_teams):
 return dict(schemaVersion=1,path="conf_ligas_nacionais/BRA.cfg",
    originalSha256=original_hash,targetSha256=EXPECTED_TARGET,
    originalSize=1089,targetSize=1089,
    operations=[{"copy":[0,984]},{"add":base64.b64encode(bytes([2])).decode()},
                {"copy":[985,7]},{"add":base64.b64encode(bytes([20])).decode()},
                {"copy":[993,96]}])
def build():
 old=json.loads((BUNDLE/"manifest.json").read_text(encoding="utf-8"))
 if old["version"]!="2026.0.2" or len(old["files"])!=20:
  raise ValueError("Only clean v2026.0.2 source may generate new release")
 existing=json.loads((SRC/"verified-existing.json").read_text(encoding="utf-8"))["files"]
 if len(existing)!=90:raise ValueError("Expected 90 hashed historical records")
 B=[x for x in existing if x["division"]=="B"]
 C=[x for x in existing if x["division"]=="C"]
 D=[]
 for club,uf in SELECTED:
  matches=[x for x in existing if x["division"]=="D" and x["name"]==club and x["state"]==uf]
  if len(matches)!=1:raise ValueError("Ambiguous Série D club: "+club+"/"+uf)
  D.append(matches[0])
 if len(B)!=20 or len(C)!=19 or len(D)!=20 or len({x["path"] for x in B+C+D})!=59:
  raise ValueError("Division club counts not validated")
 source_rows=[row for row in (SRC/"missing-teams.tsv").read_text(encoding="utf-8").splitlines()
              if row and not row.startswith("#")]
 ma=[row for row in source_rows if row.split("\t")[1:3]==["Maranhão","MA"]]
 if len(ma)!=1 or ma[0].split("\t")[3]!="C":
  raise ValueError("Maranhão identity not resolved")
 gen=SRC/"generated"
 gen.mkdir(parents=True,exist_ok=True)
 if list(gen.glob("*.ban")):raise RuntimeError("Stale generated records")
 selection=SRC/"ma-only.tsv"
 selection.write_text(ma[0]+"\n",encoding="utf-8")
 classes=SRC/"classes";classes.mkdir(parents=True,exist_ok=True)
 sources=sorted(str(p) for p in (SRC/"src").rglob("*.java"))
 subprocess.run(["javac","-encoding","UTF-8","-d",str(classes),*sources],check=True)
 subprocess.run(["java","-cp",str(classes),"app.GeneratePreview",str(selection),str(gen)],check=True)
 teamname=ma[0].split("\t")[0]+".ban"
 raw=(gen/teamname).read_bytes()
 if not raw.startswith(b"\xac\xed\x00\x05"):raise ValueError("Invalid generated serialization")
 path="teams/"+teamname
 put(BUNDLE/"patches"/(teamname+".json"),dict(schemaVersion=1,path=path,
   originalSha256=h(b""),targetSha256=h(raw),originalSize=0,targetSize=len(raw),
   operations=[dict(add=base64.b64encode(raw).decode())]))
 added=dict(operation="add",path=path,size=len(raw),sha256=h(raw),acceptedOriginalSha256=[])
 verified=[dict(operation="verify",path=x["path"],size=x["size"],
                sha256=x["sha256"],acceptedOriginalSha256=[]) for x in B+C+D]
 cfgpath="conf_ligas_nacionais/BRA.cfg"
 cfg=dict(operation="replace",path=cfgpath,size=1089,sha256=EXPECTED_TARGET,
          acceptedOriginalSha256=[EXPECTED_ORIGINAL,EXPECTED_ALPHA])
 put(BUNDLE/"patches"/"BRA.cfg.json",cfg_recipe(EXPECTED_ORIGINAL,8,64))
 put(BUNDLE/"patches"/("BRA.cfg."+EXPECTED_ALPHA+".json"),cfg_recipe(EXPECTED_ALPHA,16,96))
 files=[dict(x,operation="replace") for x in old["files"]]+verified+[added,cfg]
 if len(files)!=81 or len({x["path"].casefold() for x in files})!=81:raise ValueError("80 club manifest invalid")
 put(BUNDLE/"manifest.json",dict(schemaVersion=3,kind="BRASFOOT_HOMOLOGATION_PATCH",
   patchSeason=2026,version="2026.1.1",publicationAllowed=False,
   compatibilityTestedInGame=False,
   label="Versao publica 2026.1.1 - configuracao experimental de Serie D",
   files=files))
 print("2026.1.1 built: 20 Serie A + 20 Serie B + 19+1 Serie C + 20 Serie D + 1 BRA.cfg = 81 operations")
 print("Serie D groups: 2 x 10. Elencos B/C/D historicos, Maranhao com atletas ficticios.")
if __name__=="__main__":build()
