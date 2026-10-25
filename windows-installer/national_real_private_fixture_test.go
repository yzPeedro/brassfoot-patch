package main

import (
  "encoding/json"
  "os"
  "path/filepath"
  "testing"
)

// Private integration fixture: no original Brasfoot binaries are committed.
func TestV3RealNationalConfigInPrivate703TeamGame(t *testing.T) {
  teamRoot:=os.Getenv("BRASSFOOT_TEST_703_TEAMS")
  sourcePath:=os.Getenv("BRASSFOOT_TEST_BRA_CONFIG")
  targetPath:=os.Getenv("BRASSFOOT_TEST_BRA_TARGET")
  if teamRoot==""||sourcePath==""||targetPath==""{t.Skip("private game fixture unavailable")}
  original,e:=os.ReadFile(sourcePath);if e!=nil{t.Fatal(e)}
  changed,e:=os.ReadFile(targetPath);if e!=nil{t.Fatal(e)}
  if len(original)!=1089||len(changed)!=1089{t.Fatal("invalid original competition config")}
  root:=t.TempDir();game:=filepath.Join(root,"game")
  os.MkdirAll(filepath.Join(game,"teams"),0700)
  os.MkdirAll(filepath.Join(game,"conf_ligas_nacionais"),0700)
  entries,e:=os.ReadDir(teamRoot);if e!=nil{t.Fatal(e)}
  copied:=0
  for _,entry:=range entries {
    if !entry.Type().IsRegular()||filepath.Ext(entry.Name())!=".ban"{continue}
    b,e:=os.ReadFile(filepath.Join(teamRoot,entry.Name()));if e!=nil{t.Fatal(e)}
    if e=os.WriteFile(filepath.Join(game,"teams",entry.Name()),b,0600);e!=nil{t.Fatal(e)}
    copied++
  }
  if copied!=703{t.Fatalf("expected 703 teams, got %d",copied)}
  destination:=filepath.Join(game,"conf_ligas_nacionais","BRA.cfg")
  os.WriteFile(destination,original,0600)
  os.WriteFile(filepath.Join(game,"options.bcf"),[]byte("settings"),0600)
  os.WriteFile(filepath.Join(game,"career.s22"),[]byte("career"),0600)
  payload:=filepath.Join(root,"payload")
  os.MkdirAll(filepath.Join(payload,"conf_ligas_nacionais"),0700)
  item:=ManifestFile{Operation:"replace",Path:nationalConfigPath,Size:int64(len(changed)),SHA256:digestBytes(changed),AcceptedOriginalSHA256:[]string{digestBytes(original)}}
  m:=Manifest{SchemaVersion:3,Kind:"BRASFOOT_HOMOLOGATION_PATCH",PatchSeason:2026,Version:"2026.99.10",Files:[]ManifestFile{item}}
  b,_:=json.Marshal(m)
  os.WriteFile(filepath.Join(payload,"manifest.json"),b,0600)
  os.WriteFile(filepath.Join(payload,"conf_ligas_nacionais","BRA.cfg"),changed,0600)
  plan,e:=inspect(payload,game);if e!=nil{t.Fatal(e)}
  t.Setenv("LOCALAPPDATA",filepath.Join(root,"appdata"))
  if _,e=install(plan,InstallOptions{});e!=nil{t.Fatal(e)}
  got,_:=os.ReadFile(destination)
  if digestBytes(got)!=digestBytes(changed){t.Fatal("config install mismatch")}
  plan,e=inspect(payload,game);if e!=nil||!plan.AlreadyInstalled{t.Fatalf("idempotence %v",e)}
  if _,e=restorePatch(plan,nil);e!=nil{t.Fatal(e)}
  got,_=os.ReadFile(destination)
  if digestBytes(got)!=digestBytes(original){t.Fatal("original cfg not restored")}
  for n,w:=range map[string]string{"options.bcf":"settings","career.s22":"career"}{
    b,_:=os.ReadFile(filepath.Join(game,n));if string(b)!=w{t.Fatalf("personal file touched: %s",n)}
  }
  t.Logf("PASS %d private original teams, national config transaction and restore",copied)
}
