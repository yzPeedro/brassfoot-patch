package main

import (
  "encoding/base64"
  "encoding/json"
  "os"
  "path/filepath"
  "strings"
  "testing"
  "testing/fstest"
)

// Fixture bytes are synthetic. No proprietary configuration is committed.
func TestV3NationalLeagueConfigBackupInstallRestore(t *testing.T) {
  root:=t.TempDir()
  game:=filepath.Join(root,"game")
  if err:=os.MkdirAll(filepath.Join(game,"teams"),0700);err!=nil{t.Fatal(err)}
  if err:=os.MkdirAll(filepath.Join(game,"conf_ligas_nacionais"),0700);err!=nil{t.Fatal(err)}
  for i:=0;i<10;i++ {
    if err:=os.WriteFile(filepath.Join(game,"teams",string(rune('a'+i))+".ban"),[]byte{0xac,0xed,0,5,1},0600);err!=nil{t.Fatal(err)}
  }
  os.WriteFile(filepath.Join(game,"options.bcf"),[]byte("settings"),0600)
  os.WriteFile(filepath.Join(game,"career.s22"),[]byte("career"),0600)
  orig:=[]byte{0xac,0xed,0,5,1,2,3,4}
  updated:=[]byte{0xac,0xed,0,5,1,2,99,4}
  target:=filepath.Join(game,"conf_ligas_nacionais","BRA.cfg")
  os.WriteFile(target,orig,0600)
  payload:=filepath.Join(root,"payload")
  os.MkdirAll(payload,0700)
  entry:=ManifestFile{Path:nationalConfigPath,Operation:"replace",Size:int64(len(updated)),SHA256:digestBytes(updated),AcceptedOriginalSHA256:[]string{digestBytes(orig)}}
  m:=Manifest{SchemaVersion:3,Kind:"BRASFOOT_HOMOLOGATION_PATCH",PatchSeason:2026,Version:"2026.99.1",Files:[]ManifestFile{entry}}
  body,_:=json.Marshal(m)
  os.WriteFile(filepath.Join(payload,"manifest.json"),body,0600)
  recipe:=patchRecipe{SchemaVersion:1,Path:entry.Path,OriginalSHA256:digestBytes(orig),TargetSHA256:entry.SHA256,OriginalSize:len(orig),TargetSize:len(updated),Operations:[]patchOp{{Copy:[]int{0,6}},{Add:base64.StdEncoding.EncodeToString([]byte{99})},{Copy:[]int{7,1}}}}
  delta,_:=json.Marshal(recipe)
  fsys:=fstest.MapFS{"bundled_release/manifest.json":{Data:body},"bundled_release/patches/BRA.cfg.json":{Data:delta}}
  if err:=preparePayloadWithFS(fsys,game,payload);err!=nil{t.Fatal(err)}
  plan,err:=inspect(payload,game)
  if err!=nil||plan.AlreadyInstalled||len(plan.Items)!=1{t.Fatalf("plan %v",err)}
  t.Setenv("LOCALAPPDATA",filepath.Join(root,"appdata"))
  if _,err=install(plan,InstallOptions{});err!=nil{t.Fatal(err)}
  got,_:=os.ReadFile(target)
  if digestBytes(got)!=digestBytes(updated){t.Fatal("national config not installed")}
  patched,err:=inspect(payload,game)
  if err!=nil||!patched.AlreadyInstalled{t.Fatalf("idempotence %v",err)}
  if _,err=restorePatch(patched,nil);err!=nil{t.Fatal(err)}
  restored,_:=os.ReadFile(target)
  if digestBytes(restored)!=digestBytes(orig){t.Fatal("national config not restored")}
  for n,want:=range map[string]string{"options.bcf":"settings","career.s22":"career"} {
    data,_:=os.ReadFile(filepath.Join(game,n))
    if string(data)!=want{t.Fatalf("personal file changed: %s",n)}
  }
  m.SchemaVersion=2
  body,_=json.Marshal(m)
  os.WriteFile(filepath.Join(payload,"manifest.json"),body,0600)
  if _,err=inspect(payload,game);err==nil{t.Fatal("v2 accepted national config")}
}

func TestV3NationalLeagueConfigPathRestrictions(t *testing.T) {
  game,payload,_,_,_:=v3Fixture(t)
  dir:=filepath.Join(game,"conf_ligas_nacionais")
  os.MkdirAll(dir,0700)
  os.WriteFile(filepath.Join(dir,"BRA.cfg"),[]byte{0xac,0xed,0,5,1},0600)
  for _,c:=range []struct{p,op string}{
    {"conf_ligas_nacionais/ESP.cfg","replace"},
    {"conf_ligas_nacionais/BRA.cfg","add"},
    {"conf_ligas_nacionais/../BRA.cfg","replace"},
  } {
    m:=Manifest{SchemaVersion:3,Kind:"BRASFOOT_HOMOLOGATION_PATCH",PatchSeason:2026,Version:"2026.99.2",Files:[]ManifestFile{{Path:c.p,Operation:c.op,Size:5,SHA256:strings.Repeat("1",64),AcceptedOriginalSHA256:[]string{strings.Repeat("2",64)}}}}
    b,_:=json.Marshal(m)
    os.WriteFile(filepath.Join(payload,"manifest.json"),b,0600)
    if _,err:=inspect(payload,game);err==nil{t.Fatalf("unsafe path accepted: %s %s",c.p,c.op)}
  }
}
