//go:build windows

package main

import (
 "os"
 "path/filepath"
 "testing"
)

func TestV4RealRosterInstallRestoreCI(t *testing.T) {
 game:=os.Getenv("BRASFOOT_V4_CI_GAME")
 if game=="" {t.Skip("Windows V4 real-game fixture only; never run on user installs")}
 saveFile:=filepath.Join(game,"career-ci-custom-user.sav")
 if err:=os.WriteFile(saveFile,[]byte("CI-USER-SAVE-MUST-SURVIVE"),0600);err!=nil {t.Fatal(err)}
 defer os.Remove(saveFile)
 originals:=make(map[string]string)
 payload,err:=stageBundledPayload()
 if err!=nil {t.Fatal(err)}
 defer os.RemoveAll(filepath.Dir(payload))
 if err=prepareBundledPayload(game,payload);err!=nil {t.Fatalf("Cannot reconstruct 60 players from V4: %v",err)}
 p,err:=inspect(payload,game)
 if err!=nil {t.Fatalf("V4 full roster manifest rejected: %v",err)}
 if len(p.Items)!=60 || p.AlreadyInstalled {t.Fatalf("Expected 60 pending V4 team modifications, got %d, installed=%v",len(p.Items),p.AlreadyInstalled)}
 for _,item:=range p.Items {
  hash,e:=sha(filepath.Join(game,filepath.FromSlash(item.File.Path)))
  if e!=nil {t.Fatal(e)}
  originals[item.File.Path]=hash
 }
 result,err:=install(p,InstallOptions{})
 if err!=nil {t.Fatalf("Real V4 60-team application failed: %v",err)}
 if result.Files!=60 {t.Fatalf("Expected 60 applied files, got %d",result.Files)}
 for _,item:=range p.Items {
  hash,e:=sha(filepath.Join(game,filepath.FromSlash(item.File.Path)))
  if e!=nil || hash!=item.File.SHA256 {t.Fatalf("Bad SHA after installation: %s: %v",item.File.Path,e)}
 }
 got,e:=os.ReadFile(saveFile)
 if e!=nil || string(got)!="CI-USER-SAVE-MUST-SURVIVE" {t.Fatalf("CI user save changed after install: %v",e)}
 after,err:=inspect(payload,game)
 if err!=nil || !after.AlreadyInstalled {t.Fatalf("Installed game not recognized: %v",err)}
 if _,err=restorePatch(after,nil);err!=nil {t.Fatalf("Real V4 60-team restore failed: %v",err)}
 for _,item:=range p.Items {
  hash,e:=sha(filepath.Join(game,filepath.FromSlash(item.File.Path)))
  if e!=nil || hash!=originals[item.File.Path] {t.Fatalf("Original not restored: %s: %v",item.File.Path,e)}
 }
 got,e=os.ReadFile(saveFile)
 if e!=nil || string(got)!="CI-USER-SAVE-MUST-SURVIVE" {t.Fatalf("CI user save changed after restore: %v",e)}
 t.Log("PASS 60 V4-player .ban patches applied and SHA-confirmed; all original files restored, save unchanged. NOT gameplay or source validation.")
}
