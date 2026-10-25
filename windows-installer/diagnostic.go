package main

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// Diagnostic gives a clear cause and an action, rather than a raw filesystem error.
type Diagnostic struct {
	Code, Title, Reason, Action, Detail string
}

func (d Diagnostic) Full() string {
	return fmt.Sprintf("%s — %s\n\nO que aconteceu:\n%s\n\nComo resolver:\n%s\n\nDetalhes técnicos:\n%s", d.Code, d.Title, d.Reason, d.Action, d.Detail)
}

type UnknownOriginalError struct {
	Relative, Actual string
	Accepted         []string
}

func (e *UnknownOriginalError) Error() string {
	return fmt.Sprintf("arquivo original não reconhecido: %s (SHA-256 encontrado: %s)", e.Relative, e.Actual)
}

func diagnose(err error) Diagnostic {
	if err == nil {
		return Diagnostic{Code: "OK", Title: "Tudo pronto", Reason: "Verificações concluídas.", Action: "Você pode instalar o patch."}
	}
	raw := err.Error()
	var unknown *UnknownOriginalError
	if errors.As(err, &unknown) {
		expected := strings.Join(unknown.Accepted, "\n")
		return Diagnostic{"BF-104", "Arquivos do jogo diferentes da versão suportada",
			"O arquivo " + unknown.Relative + " não corresponde ao original esperado. Isso pode ocorrer se já existe outro patch, arquivos foram modificados ou o Brasfoot é de outra edição.",
			"Não apague arquivos nem force a instalação. Use uma instalação original compatível e tente novamente. Seus saves permanecem intactos.",
			"Arquivo: " + unknown.Relative + "\nSHA-256 encontrado: " + unknown.Actual + "\nSHA-256 aceitos: \n" + expected}
	}
	lower := strings.ToLower(raw)
	switch {
	case strings.Contains(lower, "pasta do jogo não encontrada") || strings.Contains(lower, "the system cannot find the path") || strings.Contains(lower, "no such file or directory") && strings.Contains(lower, "pasta do jogo"):
		return Diagnostic{"BF-101", "Pasta do Brasfoot não encontrada", "O caminho selecionado não existe ou não está acessível.", "Clique em PROCURAR e selecione a pasta onde o Brasfoot está instalado (a que contém options.bcf e teams).", raw}
	case strings.Contains(lower, "options.bcf"):
		return Diagnostic{"BF-102", "Esta não é a pasta principal do Brasfoot", "O arquivo options.bcf está ausente ou não é um arquivo normal.", "Selecione a pasta raiz do jogo, por exemplo C:\\Brasfoot22-23, e não a subpasta teams.", raw}
	case strings.Contains(lower, "teams/") || strings.Contains(lower, "estrutura de equipes"):
		return Diagnostic{"BF-103", "Estrutura de equipes não reconhecida", "A pasta teams não existe ou não contém arquivos .ban válidos suficientes.", "Verifique se escolheu o Brasfoot 2022-2023, e não uma pasta de saves, Downloads ou outro jogo.", raw}
	case strings.Contains(lower, "arquivo ausente") || strings.Contains(lower, "arquivo não encontrado na instalação"):
		return Diagnostic{"BF-105", "Faltam arquivos do clube no seu Brasfoot", "Um dos clubes de 2026 não existe na pasta teams ou não pode ser lido.", "Confirme que o Brasfoot foi instalado corretamente. Não copie arquivos aleatórios de outras versões.", raw}
	case strings.Contains(lower, "pacote") || strings.Contains(lower, "manifest") || strings.Contains(lower, "hash corrompido"):
		return Diagnostic{"BF-106", "Pacote de elencos inválido", "A verificação de integridade do conteúdo embutido falhou.", "Baixe novamente o instalador de homologação. Não altere manualmente os arquivos.", raw}
	case strings.Contains(lower, "permission") || strings.Contains(lower, "permissão") || strings.Contains(lower, "access is denied") || errors.Is(err, os.ErrPermission):
		return Diagnostic{"BF-107", "Sem permissão para atualizar os arquivos", "O Windows negou o acesso a um arquivo ou pasta necessária para a instalação.", "Feche o Brasfoot. Verifique a permissão de gravação da pasta do jogo; se necessário, execute o instalador como administrador.", raw}
	case strings.Contains(lower, "rollback incompleto"):
		return Diagnostic{"BF-109", "Restauração automática incompleta", "Uma falha ocorreu e não foi possível restaurar todos os arquivos de equipes.", "Não abra o Brasfoot ainda. Preserve a pasta de backups mostrada no diagnóstico e restaure os arquivos com segurança.", raw}
	case strings.Contains(lower, "originais restaurados"):
		return Diagnostic{"BF-108", "Instalação interrompida; originais restaurados", "A instalação não terminou, mas o instalador restaurou os arquivos das equipes.", "Mantenha o jogo fechado, confira o backup indicado abaixo e tente novamente após corrigir a causa.", raw}
	case strings.Contains(lower, "parcialmente instalado"):
		return Diagnostic{"BF-110", "Instalação anterior incompleta", "Parte das equipes já contém o patch e outra parte está na versão original.", "Não force a instalação. Restaure os arquivos da pasta de backup anterior para o mesmo diretório teams e tente novamente.", raw}
	case strings.Contains(lower, "espaço insuficiente"):
		return Diagnostic{"BF-111", "Pouco espaço em disco", "Não há espaço suficiente para cópias de segurança e substituição segura.", "Libere espaço na unidade do Brasfoot e na unidade de backups do Windows.", raw}
	default:
		return Diagnostic{"BF-199", "Não foi possível concluir a instalação", "Uma verificação de segurança impediu a alteração ou ocorreu uma falha inesperada.", "Confirme que o jogo está fechado e examine os detalhes. Não tente forçar o patch em arquivos desconhecidos.", raw}
	}
}

func checkWritableTeams(game string) error {
	dir := filepath.Join(game, "teams")
	f, err := os.CreateTemp(dir, ".brassfoot-permission-check-*")
	if err != nil {
		return fmt.Errorf("sem permissão para gravar na pasta teams: %w", err)
	}
	name := f.Name()
	err = f.Close()
	removeErr := os.Remove(name)
	if err != nil {
		return err
	}
	if removeErr != nil {
		return fmt.Errorf("não foi possível limpar o teste de permissão: %w", removeErr)
	}
	return nil
}
