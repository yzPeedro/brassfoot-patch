"""Build unverified 156-club alpha offline; includes only original synthetic bytes."""
import json,base64,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
B=R/"windows-installer/bundled_release"
S=R/"preview-builder"
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
def main():
 old=json.loads((B/"manifest.json").read_text())
 assert old["version"]=="2026.0.2" and len(old["files"])==20
 ver=json.loads((S/"verified-existing.json").read_text())["files"]
 rows=[x.split("\t") for x in (S/"missing-teams.tsv").read_text().splitlines() if x and not x.startswith("#")]
 assert len(rows)==46 and len(ver)==90
 out=S/"generated"
 out.mkdir(exist_ok=True)
 assert not list(out.glob("*.ban")), "Stale generated files"
 classes=S/"classes"
 classes.mkdir(exist_ok=True)
 subprocess.run(["javac","-encoding","UTF-8","-d",str(classes),*[str(p) for p in sorted((S/"src").rglob("*.java"))]],check=True)
 subprocess.run(["java","-cp",str(classes),"app.GeneratePreview",str(S/"missing-teams.tsv"),str(out)],check=True)
 adds=[]
 for key,name,uf,div,internal in rows:
  b=(out/(key+".ban")).read_bytes()
  assert len(b)>200
  name="teams/"+key+".ban"
  adds.append(dict(operation="add",path=name,size=len(b),sha256=sha(b),acceptedOriginalSha256=[]))
  write(B/"patches"/(key+".ban.json"),dict(schemaVersion=1,path=name,originalSha256=sha(b""),originalSize=0,targetSha256=sha(b),targetSize=len(b),operations=[dict(add=base64.b64encode(b).decode())]))
 verify=[dict(operation="verify",path=z["path"],size=z["size"],sha256=z["sha256"],acceptedOriginalSha256=[]) for z in ver]
 p="conf_ligas_nacionais/BRA.cfg"
 oldhash="76b7af89b81859ed8ee29f78de34ced3c48636ec0a27554c29d8d0da55bc2834"
 newhash="edda3712891e30fa212dddddbcbba9af8dd4c8a83c02d735e3b80f014a776dcd"
 cfg=dict(operation="replace",path=p,size=1089,sha256=newhash,acceptedOriginalSha256=[oldhash])
 write(B/"patches"/"BRA.cfg.json",dict(schemaVersion=1,path=p,originalSha256=oldhash,originalSize=1089,targetSha256=newhash,targetSize=1089,operations=[dict(copy=[0,984]),dict(add="EA=="),dict(copy=[985,7]),dict(add="YA=="),dict(copy=[993,96])]))
 files=[dict(x,operation="replace") for x in old["files"]]+verify+adds+[cfg]
 assert len(files)==157 and len({f["path"].lower() for f in files})==157
 write(B/"manifest.json",dict(schemaVersion=3,kind="BRASFOOT_HOMOLOGATION_PATCH",patchSeason=2026,version="2026.1.0",publicationAllowed=False,compatibilityTestedInGame=False,label="ALFA nao testada dentro do jogo",files=files))
 print("Built 20 A + 90 historical (verify only) + 46 fictional adds + experimental BRA cfg")
if __name__=="__main__":main()
