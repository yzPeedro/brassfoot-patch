//go:build !windows || hubcli

package main

import (
	"archive/zip"
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

func main() {
	if err := runPortable(); err != nil {
		recordDiagnostic(diagnose(err))
		fmt.Fprintln(os.Stderr, productName+": "+err.Error())
		os.Exit(1)
	}
}

func portableConfirmation(message string, graphical bool) bool {
	if graphical {
		if accepted, answered := graphicalConfirmation(message); answered {
			return accepted
		}
	}
	fmt.Println(message)
	fmt.Print("Digite SIM para continuar: ")
	answer, err := bufio.NewReader(os.Stdin).ReadString('\n')
	return err == nil && strings.EqualFold(strings.TrimSpace(answer), "SIM")
}

func runPortable() error {
	game := flag.String("game", "", "pasta principal da sua instalação do Brasfoot")
	yes := flag.Bool("yes", false, "confirmar aplicação ou restauração sem pergunta interativa")
	restore := flag.Bool("restore", false, "restaurar o backup íntegro desta edição")
	inspectOnly := flag.Bool("inspect", false, "mostrar compatibilidade sem modificar o jogo")
	version := flag.Bool("version", false, "mostrar edição e commit do instalador")
	only := flag.String("only", "", "instalar só um componente: patch ou live")
	feed := flag.String("feed", "", "pasta local com release.json e o pacote, em vez do GitHub")
	bundle := flag.String("bundle", "", "arquivo .zip do pacote baixado da release, para uso sem internet")
	remove := flag.String("remove", "", "remover componentes: rosters, season, live, crests ou all (separados por vírgula)")
	flag.Parse()
	if flag.NArg() != 0 {
		return errors.New("argumentos inesperados; consulte --help")
	}
	if *version {
		fmt.Printf("%s / atualizador %s / edição %s / %s-%s / %s\n", productName, hubVersion, patchYearText, runtime.GOOS, runtime.GOARCH, sourceCommit)
		return nil
	}
	if stateDirRequired && stateDir == "" {
		return errors.New("informe --state-dir com uma pasta descartável para o estado do atualizador")
	}
	if *restore && *inspectOnly {
		return errors.New("escolha --restore ou --inspect")
	}
	if *only != "" && *only != componentPatch && *only != componentLive {
		return errors.New("--only aceita patch ou live")
	}
	if *only != "" && *restore {
		return errors.New("--only não se aplica à restauração")
	}
	graphical := *game == "" && !*yes && !*inspectOnly
	if *game == "" {
		*game = detectedPortableGame()
	}
	if *game == "" {
		if *yes || *inspectOnly {
			return errors.New("instalação não encontrada; informe --game /caminho/do/Brasfoot")
		}
		var err error
		*game, err = folderPicker()
		if err != nil {
			return fmt.Errorf("nenhuma pasta foi selecionada; use --game para escolher a instalação: %w", err)
		}
	}
	if *game == "" {
		return errors.New("nenhuma instalação foi selecionada")
	}
	if strings.EqualFold(filepath.Base(filepath.Clean(*game)), "teams") {
		*game = filepath.Dir(filepath.Clean(*game))
	}
	fmt.Printf("%s · atualizador %s\n", productName, hubVersion)
	if portablePlatformNotice != "" {
		fmt.Println(portablePlatformNotice)
	}
	if err := checkPortableGameClosed(); err != nil && !*inspectOnly {
		return err
	}
	if err := loadPortablePayload(*feed, *bundle); err != nil {
		return err
	}
	if *remove != "" {
		return runPortableRemoval(*game, *remove, *yes, graphical)
	}
	payload, err := stageBundledPayload()
	if err != nil {
		return err
	}
	defer os.RemoveAll(filepath.Dir(payload))
	var plan Plan
	if *only != "" {
		plan, err = stageComponents(filepath.Dir(payload), *game, Selection{Patch: *only == componentPatch, Live: *only == componentLive})
	} else if err = prepareBundledPayload(*game, payload); err == nil {
		plan, err = inspect(payload, *game)
	}
	if err != nil {
		return err
	}
	if *inspectOnly {
		return json.NewEncoder(os.Stdout).Encode(map[string]any{
			"product": productName, "version": hubVersion, "payloadVersion": plan.Manifest.Version,
			"game": plan.Game, "files": len(plan.Items), "alreadyInstalled": plan.AlreadyInstalled,
			"platform": runtime.GOOS, "architecture": runtime.GOARCH, "gameplayVerified": false,
		})
	}
	action := "Atualizar o Brasfoot? Será criado um backup antes das alterações."
	if *restore {
		action = "Restaurar os arquivos anteriores do Brasfoot a partir do backup?"
	}
	if !*yes && !portableConfirmation(action+"\nPasta: "+plan.Game+"\nEdição 2026. Feche o jogo antes de continuar. Saves não fazem parte do pacote.", graphical) {
		fmt.Println("Operação cancelada. Nenhum arquivo do jogo foi alterado.")
		return nil
	}
	if err = checkPortableGameClosed(); err != nil {
		return err
	}
	if *restore {
		backup, err := restorePatch(plan, func(done, total int) { fmt.Printf("Restaurando arquivos: %d/%d\n", done, total) })
		if err != nil {
			return err
		}
		fmt.Println("Arquivos anteriores restaurados. Backup preservado em: " + backup)
		return nil
	}
	result, err := install(plan, InstallOptions{Progress: func(stage string, done, total int) {
		label := map[string]string{"backup": "Criando backup", "install": "Atualizando clubes", "done": "Finalizando"}[stage]
		fmt.Printf("%s: %d/%d\n", label, done, total)
	}})
	if err != nil {
		return err
	}
	fmt.Printf("Atualização concluída: %s.\n", result.Version)
	if result.BackupPath != "" {
		fmt.Println("Backup e relatório: " + result.BackupPath)
	}
	return nil
}

func loadPortablePayload(feed, bundle string) error {
	if bundle != "" {
		data, err := os.ReadFile(bundle)
		if err != nil {
			return err
		}
		feedOverride = filepath.Dir(bundle)
		reader, err := zip.NewReader(bytes.NewReader(data), int64(len(data)))
		if err != nil {
			return fmt.Errorf("pacote inválido: %w", err)
		}
		body, err := fs.ReadFile(reader, "bundled_release/manifest.json")
		if err != nil {
			return errors.New("pacote sem manifesto")
		}
		var manifest Manifest
		if err = json.Unmarshal(body, &manifest); err != nil {
			return err
		}
		payload, err := bundleFromZip(data, ReleaseFeed{PatchVersion: manifest.Version})
		if err != nil {
			return err
		}
		setPayload(payload)
		fmt.Printf("Pacote local: versão %s.\n", manifest.Version)
		return nil
	}
	if feed != "" {
		absolute, err := filepath.Abs(feed)
		if err != nil {
			return err
		}
		feedOverride = absolute
	}
	fmt.Println("Buscando a versão mais recente no GitHub...")
	status := refreshFeed(nil)
	if !status.Loaded {
		return fmt.Errorf("não foi possível obter a versão mais recente: %s", status.Problem)
	}
	if status.Cached {
		fmt.Printf("Sem conexão: usando a versão %s guardada neste computador.\n", status.Feed.PatchVersion)
	} else {
		fmt.Printf("Versão do patch: %s.\n", status.Feed.PatchVersion)
	}
	if hubUpdateAvailable(status.Feed) {
		fmt.Printf("Há um atualizador mais novo (%s): %s\n", status.Feed.Hub.Version, "https://github.com/yzPeedro/brassfoot-patch/releases/latest")
	}
	return nil
}

func runPortableRemoval(game, remove string, yes, graphical bool) error {
	m := bundledManifestFromFS()
	if !supportsTargets(m) {
		return errors.New("esta versão do patch ainda não permite remover componentes")
	}
	resolved, _, err := validGame(game)
	if err != nil {
		return err
	}
	harvestOriginals(m, resolved)
	report := componentReport(m, resolved)
	installed := map[string]bool{
		componentRosters: report.Rosters != statusAbsent,
		componentSeason:  report.Season != statusAbsent,
		componentLive:    report.Live != statusAbsent,
		componentCrests:  report.Crests != "" && report.Crests != statusAbsent,
	}
	target := TargetState{Rosters: installed[componentRosters], Season: installed[componentSeason], Live: installed[componentLive], Crests: installed[componentCrests]}
	for _, name := range strings.Split(remove, ",") {
		switch strings.TrimSpace(strings.ToLower(name)) {
		case "all":
			target = TargetState{}
		case componentRosters:
			target.Rosters = false
		case componentSeason:
			target.Season = false
		case componentLive:
			target.Live = false
		case componentCrests:
			target.Crests = false
		default:
			return fmt.Errorf("componente desconhecido em --remove: %s (use rosters, season, live, crests ou all)", name)
		}
	}
	question := "Remover os componentes escolhidos? Um backup dos arquivos alterados será criado. Suas carreiras salvas continuam abrindo com ou sem o patch.\nPasta: " + resolved
	if !yes && !portableConfirmation(question, graphical) {
		fmt.Println("Operação cancelada. Nenhum arquivo do jogo foi alterado.")
		return nil
	}
	root, err := os.MkdirTemp("", "brasfoot-mega-patch-remove-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(root)
	plan, err := stageTarget(root, resolved, target)
	if err != nil {
		return err
	}
	if plan.Empty || (plan.Plan.AlreadyInstalled && len(plan.Deletes) == 0) {
		fmt.Println("Nada a remover: o jogo já está como pedido.")
		return nil
	}
	result, err := applyTarget(plan, InstallOptions{Progress: func(stage string, done, total int) {
		fmt.Printf("%s: %d/%d\n", map[string]string{"backup": "Criando backup", "install": "Aplicando", "done": "Finalizando"}[stage], done, total)
	}})
	if err != nil {
		return err
	}
	fmt.Println("Remoção concluída. Backup em: " + result.BackupPath)
	return nil
}
