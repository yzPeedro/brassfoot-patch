//go:build !windows

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
	"os/exec"
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

func folderPicker() (string, error) {
	if runtime.GOOS == "darwin" {
		out, err := exec.Command("osascript", "-e", `POSIX path of (choose folder with prompt "Selecione a pasta do Brasfoot dentro da sua instalação Wine/CrossOver")`).Output()
		return strings.TrimSpace(string(out)), err
	}
	if path, err := exec.LookPath("zenity"); err == nil {
		out, err := exec.Command(path, "--file-selection", "--directory", "--title="+productName+" — Pasta do jogo").Output()
		return strings.TrimSpace(string(out)), err
	}
	if path, err := exec.LookPath("kdialog"); err == nil {
		out, err := exec.Command(path, "--getexistingdirectory", ".", "--title", productName).Output()
		return strings.TrimSpace(string(out)), err
	}
	return "", errors.New("seletor de pastas indisponível; use --game /caminho/da/pasta/do/Brasfoot")
}

func portableConfirmation(message string, graphical bool) bool {
	if graphical {
		if runtime.GOOS == "darwin" {
			// Message is passed as argv, never interpolated into AppleScript.
			return exec.Command("osascript", "-e", `on run argv
display dialog (item 1 of argv) with title "Brasfoot Mega Patch" buttons {"Cancelar", "Continuar"} default button "Cancelar" cancel button "Cancelar"
end run`, "--", message).Run() == nil
		}
		if path, err := exec.LookPath("zenity"); err == nil {
			return exec.Command(path, "--question", "--title="+productName, "--text="+message, "--default-cancel").Run() == nil
		}
		if path, err := exec.LookPath("kdialog"); err == nil {
			return exec.Command(path, "--title", productName, "--yesno", message).Run() == nil
		}
	}
	fmt.Println(message)
	fmt.Print("Digite SIM para continuar: ")
	answer, err := bufio.NewReader(os.Stdin).ReadString('\n')
	return err == nil && strings.EqualFold(strings.TrimSpace(answer), "SIM")
}

func detectedPortableGame() string {
	home, _ := os.UserHomeDir()
	prefixes := []string{os.Getenv("WINEPREFIX"), filepath.Join(home, ".wine")}
	for _, pattern := range []string{
		filepath.Join(home, "Library", "Application Support", "CrossOver", "Bottles", "*"),
		filepath.Join(home, ".local", "share", "bottles", "bottles", "*"),
		filepath.Join(home, ".var", "app", "com.usebottles.bottles", "data", "bottles", "bottles", "*"),
	} {
		matches, _ := filepath.Glob(pattern)
		prefixes = append(prefixes, matches...)
	}
	for _, prefix := range prefixes {
		if prefix == "" {
			continue
		}
		for _, name := range []string{"Brasfoot22-23", "Brasfoot 2022-2023", "Program Files/Brasfoot22-23", "Program Files (x86)/Brasfoot22-23"} {
			candidate := filepath.Join(prefix, "drive_c", filepath.FromSlash(name))
			if _, _, err := validGame(candidate); err == nil {
				return candidate
			}
		}
	}
	return ""
}

func checkPortableGameClosed() error {
	out, err := exec.Command("ps", "-axo", "command=").Output()
	if err != nil {
		return errors.New("não foi possível identificar processos; confira se o comando ps está disponível")
	}
	for _, line := range strings.Split(string(out), "\n") {
		lower := strings.ToLower(line)
		if strings.Contains(lower, "bf22-23.exe") || (strings.Contains(lower, "java") && strings.Contains(lower, "brasfoot") && strings.Contains(lower, ".jar")) {
			return errors.New("o Brasfoot está aberto; salve sua carreira, feche o jogo e tente novamente")
		}
	}
	return nil
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
	remove := flag.String("remove", "", "remover componentes: rosters, season, live ou all (separados por vírgula)")
	flag.Parse()
	if flag.NArg() != 0 {
		return errors.New("argumentos inesperados; consulte --help")
	}
	if *version {
		fmt.Printf("%s / atualizador %s / edição %s / %s-%s / %s\n", productName, hubVersion, patchYearText, runtime.GOOS, runtime.GOARCH, sourceCommit)
		return nil
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
	fmt.Printf("%s · atualizador %s\nO jogo Windows requer uma camada de compatibilidade já configurada.\n", productName, hubVersion)
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
	}
	target := TargetState{Rosters: installed[componentRosters], Season: installed[componentSeason], Live: installed[componentLive]}
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
		default:
			return fmt.Errorf("componente desconhecido em --remove: %s (use rosters, season, live ou all)", name)
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
