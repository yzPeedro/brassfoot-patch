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

// Ensures a signed executable delta is applied IN PLACE with a persistent
// SHA-verified backup. No proprietary Brasfoot bytes are included in fixtures.
func TestV4ExecutableAndRosterInstallRestoreInPlace(t *testing.T) {
    game, payload, originalTeamHash, _ := makeFixture(t)
    originalExe := []byte{'M','Z',0,0,'b','f','2','2','-','2','3'}
    patchedExe := []byte{'M','Z',0,0,'b','f','2','0','2','6'}
    exe := filepath.Join(game, gameExecutablePath)
    if err := os.WriteFile(exe, originalExe, 0600); err != nil { t.Fatal(err) }
    if err := os.WriteFile(filepath.Join(payload, gameExecutablePath), patchedExe, 0600); err != nil { t.Fatal(err) }
    save := filepath.Join(game, "important-career.s22")
    if err := os.WriteFile(save, []byte("private saved game"), 0600); err != nil { t.Fatal(err) }
    saveHash, _ := sha(save)

    manifest := filepath.Join(payload, "manifest.json")
    body, err := os.ReadFile(manifest)
    if err != nil { t.Fatal(err) }
    var m Manifest
    if err := json.Unmarshal(body, &m); err != nil { t.Fatal(err) }
    m.SchemaVersion, m.Version = 4, "2026.3.0"
    m.Files = append(m.Files, ManifestFile{Operation:"replace", Path: gameExecutablePath,
        Size:int64(len(patchedExe)), SHA256:digestBytes(patchedExe),
        AcceptedOriginalSHA256:[]string{digestBytes(originalExe)}})
    data, _ := json.Marshal(m)
    if err := os.WriteFile(manifest, data, 0600); err != nil { t.Fatal(err) }
    t.Setenv("LOCALAPPDATA", filepath.Join(t.TempDir(),"backups"))
    plan, err := inspect(payload, game)
    if err != nil || plan.AlreadyInstalled || len(plan.Items) != 2 { t.Fatalf("preflight failed: %v",err) }
    result, err := install(plan, InstallOptions{})
    if err != nil { t.Fatal(err) }
    if result.Status != "installed" { t.Fatal(result) }
    installed, _ := sha(exe)
    if installed != digestBytes(patchedExe) { t.Fatal("existing exe path was not updated") }
    oldBackup, _ := sha(filepath.Join(result.BackupPath,gameExecutablePath))
    if oldBackup != digestBytes(originalExe) { t.Fatal("missing or invalid original exe backup") }
    fresh, err := inspect(payload, game)
    if err != nil || !fresh.AlreadyInstalled { t.Fatalf("install not idempotent: %v", err) }
    if _, err := restorePatch(fresh,nil); err != nil { t.Fatal(err) }
    restored, _ := sha(exe)
    restoredTeam, _ := sha(filepath.Join(game,"teams","a.ban"))
    afterSave, _ := sha(save)
    if restored != digestBytes(originalExe) || restoredTeam != originalTeamHash || saveHash != afterSave {
        t.Fatal("rollback did not restore exe and team or altered save")
    }
}

func TestV4RejectsUnsignedOrUnknownExecutable(t *testing.T) {
    game, payload, _, _ := makeFixture(t)
    original := []byte("MZ-original")
    updated := []byte("MZ-updated")
    _ = os.WriteFile(filepath.Join(game,gameExecutablePath),original,0600)
    _ = os.WriteFile(filepath.Join(payload,gameExecutablePath),updated,0600)
    m := Manifest{SchemaVersion:4,Kind:"BRASFOOT_HOMOLOGATION_PATCH",PatchSeason:2026,Version:"2026.3.0",
        Files: []ManifestFile{{Operation:"replace",Path:gameExecutablePath,Size:int64(len(updated)),
            SHA256:digestBytes(updated),AcceptedOriginalSHA256:[]string{strings.Repeat("f",64)}}}}
    raw,_:=json.Marshal(m)
    _ = os.WriteFile(filepath.Join(payload,"manifest.json"),raw,0600)
    if _,err:=inspect(payload,game);err==nil { t.Fatal("unknown original exe accepted") }
    m.Files[0].Path="another-game.exe"
    raw,_=json.Marshal(m);_ = os.WriteFile(filepath.Join(payload,"manifest.json"),raw,0600)
    if _,err:=inspect(payload,game);err==nil { t.Fatal("unlisted executable accepted") }
}

func TestV4RecipeRebuildsOriginalExeWithNoFullGamePayload(t *testing.T) {
    game, _, _, _ := makeFixture(t)
    original := []byte("MZ-original")
    target := []byte("MZ-updated")
    if err:=os.WriteFile(filepath.Join(game,gameExecutablePath),original,0600);err!=nil{t.Fatal(err)}
    f:=ManifestFile{Operation:"replace",Path:gameExecutablePath,Size:int64(len(target)),
        SHA256:digestBytes(target),AcceptedOriginalSHA256:[]string{digestBytes(original)}}
    m:=Manifest{SchemaVersion:4,Kind:"BRASFOOT_HOMOLOGATION_PATCH",PatchSeason:2026,
        Version:"2026.3.0",Files:[]ManifestFile{f}}
    body,_:=json.Marshal(m)
    recipe:=patchRecipe{SchemaVersion:1,Path:f.Path,OriginalSHA256:digestBytes(original),
        OriginalSize:len(original),TargetSHA256:f.SHA256,TargetSize:len(target),
        Operations:[]patchOp{{Add:base64.StdEncoding.EncodeToString(target)}}}
    diff,_:=json.Marshal(recipe)
    fsys:=fstest.MapFS{"bundled_release/manifest.json":{Data:body},
        "bundled_release/patches/bf22-23.exe.json":{Data:diff}}
    staged:=filepath.Join(t.TempDir(),"staging")
    if err:=os.MkdirAll(staged,0700);err!=nil{t.Fatal(err)}
    if err:=os.WriteFile(filepath.Join(staged,"manifest.json"),body,0600);err!=nil{t.Fatal(err)}
    if err:=preparePayloadWithFS(fsys,game,staged);err!=nil{t.Fatal(err)}
    plan,err:=inspect(staged,game)
    if err!=nil||len(plan.Items)!=1 {t.Fatalf("v4 staged exe rejected: %v",err)}
    t.Setenv("LOCALAPPDATA",filepath.Join(t.TempDir(),"backups"))
    if _,err:=install(plan,InstallOptions{TestFailAfter:1});err==nil {t.Fatal("expected interrupted transaction")}
    current,_:=sha(filepath.Join(game,gameExecutablePath))
    if current!=digestBytes(original) {t.Fatal("in-place exe not restored after interrupted install")}
}
