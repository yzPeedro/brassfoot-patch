package main

import (
  "encoding/json"
"encoding/base64"
  "os"
  "path/filepath"
  "strings"
  "testing"
"testing/fstest"
)

func v3Fixture(t *testing.T) (string,string,[]byte,[]byte,[]byte) {
  t.Helper()
  root:=t.TempDir();game:=filepath.Join(root,"game");payload:=filepath.Join(root,"payload")
  if err:=os.MkdirAll(filepath.Join(game,"teams"),0700);err!=nil{t.Fatal(err)}
  if err:=os.MkdirAll(filepath.Join(payload,"teams"),0700);err!=nil{t.Fatal(err)}
  _=os.WriteFile(filepath.Join(game,"options.bcf"),[]byte("private options"),0600)
  _=os.WriteFile(filepath.Join(game,"save.s22"),[]byte("career is private"),0600)
  original:=[]byte{0xac,0xed,0,5,0,1,2,3}; target:=[]byte{0xac,0xed,0,5,0,1,3,4};added:=[]byte{0xac,0xed,0,5,5,6,7,8}
  for i:=0;i<10;i++{name:=string(rune('a'+i))+".ban";_ =os.WriteFile(filepath.Join(game,"teams",name),original,0600)}
  _=os.WriteFile(filepath.Join(payload,"teams","a.ban"),target,0600)
  _=os.WriteFile(filepath.Join(payload,"teams","created.ban"),added,0600)
  m:=Manifest{SchemaVersion:3,Kind:"BRASFOOT_HOMOLOGATION_PATCH",PatchSeason:2026,Version:"2026.1.0",Files:[]ManifestFile{
    {Operation:"add",Path:"teams/created.ban",Size:int64(len(added)),SHA256:digestBytes(added)},
    {Operation:"replace",Path:"teams/a.ban",Size:int64(len(target)),SHA256:digestBytes(target),AcceptedOriginalSHA256:[]string{digestBytes(original)}},
  }}
  b,_:=json.Marshal(m)
  _=os.WriteFile(filepath.Join(payload,"manifest.json"),b,0600)
  t.Setenv("LOCALAPPDATA",filepath.Join(root,"appdata"))
  return game,payload,original,target,added
}

func TestV3AddReplaceRestoreAndPreserveSaves(t *testing.T){
  game,payload,original,target,added:=v3Fixture(t)
  plan,err:=inspect(payload,game);if err!=nil{t.Fatal(err)}
  if plan.AlreadyInstalled||len(plan.Items)!=2{t.Fatal("bad v3 preflight")}
  if _,err=install(plan,InstallOptions{});err!=nil{t.Fatal(err)}
  for name,want:=range map[string][]byte{"a.ban":target,"created.ban":added}{got,_:=os.ReadFile(filepath.Join(game,"teams",name));if digestBytes(got)!=digestBytes(want){t.Fatal("wrong installed data "+name)}}
  patched,err:=inspect(payload,game);if err!=nil||!patched.AlreadyInstalled{t.Fatalf("v3 idempotence: %v",err)}
  if _,err=restorePatch(patched,nil);err!=nil{t.Fatal(err)}
  orig,_:=os.ReadFile(filepath.Join(game,"teams","a.ban"));if digestBytes(orig)!=digestBytes(original){t.Fatal("original not restored")}
  if _,err=os.Lstat(filepath.Join(game,"teams","created.ban"));!os.IsNotExist(err){t.Fatal("new team not removed")}
  save,_:=os.ReadFile(filepath.Join(game,"save.s22"));if string(save)!="career is private"{t.Fatal("save corrupted")}
}

func TestV3AddRollbackAndCollisionSafety(t *testing.T){
  game,payload,original,_,_:=v3Fixture(t)
  plan,err:=inspect(payload,game);if err!=nil{t.Fatal(err)}
  if _,err=install(plan,InstallOptions{TestFailAfter:1});err==nil{t.Fatal("injected failure should have rolled back")}
  if _,err=os.Lstat(filepath.Join(game,"teams","created.ban"));!os.IsNotExist(err){t.Fatal("rolled back added file still exists")}
  unchanged,_:=os.ReadFile(filepath.Join(game,"teams","a.ban"));if digestBytes(unchanged)!=digestBytes(original){t.Fatal("rollback touched original")}
  _=os.WriteFile(filepath.Join(game,"teams","created.ban"),[]byte{0xac,0xed,0,5,99},0600)
  if _,err=inspect(payload,game);err==nil||!strings.Contains(err.Error(),"já existe"){t.Fatalf("did not reject unknown created team: %v",err)}
}

func TestV3MixedAlreadyInstalledAndNewAddition(t *testing.T){
  game,payload,_,target,_:=v3Fixture(t)
  _=os.WriteFile(filepath.Join(game,"teams","a.ban"),target,0600)
  plan,err:=inspect(payload,game);if err!=nil{t.Fatal(err)}
  if plan.AlreadyInstalled||!plan.Items[1].AlreadyInstalled{t.Fatal("mixed state incorrect")}
  if _,err=install(plan,InstallOptions{});err!=nil{t.Fatal(err)}
  patched,err:=inspect(payload,game);if err!=nil||!patched.AlreadyInstalled{t.Fatalf("patched state %v",err)}
  if _,err=restorePatch(patched,nil);err!=nil{t.Fatalf("mixed restore %v",err)}
  b,_:=os.ReadFile(filepath.Join(game,"teams","a.ban"));if digestBytes(b)!=digestBytes(target){t.Fatal("preexisting patched file should not be restored")}
  if _,err=os.Lstat(filepath.Join(game,"teams","created.ban"));!os.IsNotExist(err){t.Fatal("added file not removed")}
}

func TestV3BundledNewTeamIsCreatedFromVerifiedRecipe(t *testing.T) {
  game,_,_,_,added:=v3Fixture(t)
  f:=ManifestFile{Operation:"add",Path:"teams/newclub.ban",Size:int64(len(added)),SHA256:digestBytes(added)}
  m:=Manifest{SchemaVersion:3,Kind:"BRASFOOT_HOMOLOGATION_PATCH",PatchSeason:2026,Version:"2026.2.0",Files:[]ManifestFile{f}}
  body,_:=json.Marshal(m)
  recipe:=patchRecipe{SchemaVersion:1,Path:f.Path,OriginalSHA256:digestBytes(nil),OriginalSize:0,TargetSHA256:f.SHA256,TargetSize:len(added),Operations:[]patchOp{{Add:base64.StdEncoding.EncodeToString(added)}}}
  delta,_:=json.Marshal(recipe)
  fsys:=fstest.MapFS{"bundled_release/manifest.json":{Data:body},"bundled_release/patches/newclub.ban.json":{Data:delta}}
  staged:=filepath.Join(t.TempDir(),"staged")
  if err:=os.MkdirAll(staged,0700);err!=nil{t.Fatal(err)}
  if err:=os.WriteFile(filepath.Join(staged,"manifest.json"),body,0600);err!=nil{t.Fatal(err)}
  if err:=preparePayloadWithFS(fsys,game,staged);err!=nil{t.Fatal(err)}
  plan,err:=inspect(staged,game);if err!=nil{t.Fatal(err)}
  if len(plan.Items)!=1||plan.AlreadyInstalled{t.Fatal("unexpected add-only preflight")}
  if _,err=install(plan,InstallOptions{});err!=nil{t.Fatal(err)}
  got,_:=os.ReadFile(filepath.Join(game,"teams","newclub.ban"))
  if digestBytes(got)!=digestBytes(added){t.Fatal("reconstructed new team differs")}
}
