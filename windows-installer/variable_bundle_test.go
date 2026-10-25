package main

import (
    "encoding/base64"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "strings"
    "testing"
    "testing/fstest"
)

func TestVariableSizeBundleAndSavePreservation(t *testing.T) {
    for _, count := range []int{1,156} {
        t.Run(fmt.Sprintf("clubs-%d",count),func(t *testing.T){
            root:=t.TempDir(); game:=filepath.Join(root,"game")
            if err:=os.MkdirAll(filepath.Join(game,"teams"),0700);err!=nil{t.Fatal(err)}
            if err:=os.WriteFile(filepath.Join(game,"options.bcf"),[]byte("options"),0600);err!=nil{t.Fatal(err)}
            if err:=os.WriteFile(filepath.Join(game,"career.s22"),[]byte("career stays"),0600);err!=nil{t.Fatal(err)}
            manifest:=Manifest{SchemaVersion:2,Kind:"BRASFOOT_HOMOLOGATION_PATCH",PatchSeason:2026,Version:"2026.1.0"}
            fsys:=fstest.MapFS{}
            for i:=0;i<count||i<10;i++{
                path:=fmt.Sprintf("teams/team%03d.ban",i)
                original:=[]byte{0xac,0xed,0,5,byte(i),byte(i>>8),7}
                if err:=os.WriteFile(filepath.Join(game,filepath.FromSlash(path)),original,0600);err!=nil{t.Fatal(err)}
                if i>=count{continue}
                updated:=[]byte{0xac,0xed,0,5,byte(i),byte(i>>8),9}
                f:=ManifestFile{Path:path,Size:int64(len(updated)),SHA256:digestBytes(updated),AcceptedOriginalSHA256:[]string{digestBytes(original)}}
                manifest.Files=append(manifest.Files,f)
                recipe:=patchRecipe{SchemaVersion:1,Path:path,OriginalSHA256:digestBytes(original),TargetSHA256:f.SHA256,OriginalSize:len(original),TargetSize:len(updated),Operations:[]patchOp{{Add:base64.StdEncoding.EncodeToString(updated)}}}
                raw,_:=json.Marshal(recipe)
                fsys["bundled_release/patches/"+filepath.Base(path)+".json"]=&fstest.MapFile{Data:raw}
            }
            body,_:=json.Marshal(manifest)
            fsys["bundled_release/manifest.json"]=&fstest.MapFile{Data:body}
            stage:=filepath.Join(root,"stage")
            if err:=os.MkdirAll(stage,0700);err!=nil{t.Fatal(err)}
            if err:=os.WriteFile(filepath.Join(stage,"manifest.json"),body,0600);err!=nil{t.Fatal(err)}
            if err:=preparePayloadWithFS(fsys,game,stage);err!=nil{t.Fatal(err)}
            plan,err:=inspect(stage,game);if err!=nil{t.Fatal(err)}
            if len(plan.Items)!=count||plan.AlreadyInstalled{t.Fatalf("unexpected plan: %d",len(plan.Items))}
            t.Setenv("LOCALAPPDATA",filepath.Join(root,"appdata"))
            res,err:=install(plan,InstallOptions{});if err!=nil{t.Fatal(err)}
            if res.Files!=count{t.Fatalf("expected %d files",count)}
            again,err:=inspect(stage,game)
            if err!=nil||!again.AlreadyInstalled{t.Fatalf("not idempotent: %v",err)}
            saved,err:=os.ReadFile(filepath.Join(game,"career.s22"))
            if err!=nil||string(saved)!="career stays"{t.Fatal("save changed")}
        })
    }
}

func TestVariableBundleDuplicateIsRejectedBeforeStaging(t *testing.T){
    root:=t.TempDir();game:=filepath.Join(root,"game")
    _=os.MkdirAll(filepath.Join(game,"teams"),0700)
    _=os.WriteFile(filepath.Join(game,"options.bcf"),[]byte("options"),0600)
    for i:=0;i<10;i++{_ =os.WriteFile(filepath.Join(game,"teams",fmt.Sprintf("team%03d.ban",i)),[]byte{0xac,0xed,0,5},0600)}
    f:=ManifestFile{Path:"teams/team000.ban",Size:4,SHA256:strings.Repeat("a",64),AcceptedOriginalSHA256:[]string{strings.Repeat("b",64)}}
    body,_:=json.Marshal(Manifest{SchemaVersion:2,PatchSeason:2026,Version:"2026.1.0",Files:[]ManifestFile{f,f}})
    fsys:=fstest.MapFS{"bundled_release/manifest.json":{Data:body}}
    err:=preparePayloadWithFS(fsys,game,filepath.Join(root,"stage"))
    if err==nil||!strings.Contains(err.Error(),"duplicado"){t.Fatalf("expected duplicate rejection, got %v",err)}
}
