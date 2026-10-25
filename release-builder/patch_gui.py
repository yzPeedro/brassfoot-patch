"""Update Windows GUI presentation for the 20x4 public release."""
from pathlib import Path
path=Path(__file__).resolve().parents[1]/"windows-installer"/"main_windows.go"
text=path.read_text(encoding="utf-8")
changes={
"PRÉVIA 2026.0.2 — ACOMPANHE LIMITAÇÕES":"EDIÇÃO 2026.1.1 — QUATRO SÉRIES",
"20 clubes brasileiros  •  730 atletas  •  Temporada 2026":"80 clubes: Série A, B, C e D  •  20 por divisão",
"PRÉVIA EXPERIMENTAL: 713 jogadores com atributos estimados. Compatibilidade testada; dados ainda estimados.":"20 elencos Série A atualizados; Série B/C/D históricos. Maranhão: atletas fictícios.",
"Isto vai restaurar os 20 arquivos originais das equipes a partir do backup conferido.":"Isto vai desfazer as alterações feitas nesta instalação, inclusive BRA.cfg.",
"Somente arquivos teams/*.ban serão alterados. Carreiras, saves e configurações serão preservados.":"Elencos e configurações de liga serão verificados e atualizados. Saves ficam fora das alterações.",
"A compatibilidade foi testada pelo criador do patch; elencos incluem atributos estimados.":"A configuração 20/2 da Série D não foi testada em uma partida completa. Use uma cópia separada do jogo.",
"O patch está sendo aplicado apenas nos arquivos .ban dos clubes selecionados.":"Aplicando alterações verificadas de clubes e competições com backup.",
}
for before,after in changes.items():
 if text.count(before)!=1:
  raise RuntimeError("Unexpected original GUI source: "+before)
 text=text.replace(before,after)
before="Jogo detectado e %d arquivos de equipes verificados.\\n\\nEsta é uma PRÉVIA COM DADOS ESTIMADOS: 713 jogadores têm atributos estimados.\\n\\nO instalador vai substituir SOMENTE os %d arquivos .ban aprovados em teams/. Vai salvar antes backups íntegros em AppData; NÃO vai editar saves, carreiras ou configurações.\\n\\nSalve e FECHE o Brasfoot antes de continuar.\\n\\nDeseja instalar na pasta selecionada?"
after="EDIÇÃO 2026.1.1: %d arquivos verificados.\\n\\nSéries A/B/C/D: 20 clubes cada, Série D com 2 grupos de 10.\\n\\nSérie A: 20 elencos experimentais. B/C/D: históricos; Maranhão: atletas fictícios. O calendário dentro do Brasfoot NÃO foi homologado.\\n\\nSerão alterados até %d arquivos com backup e desfazer; saves não são modificados.\\n\\nIMPORTANTE: teste somente em uma CÓPIA ISOLADA e feche o jogo. Se tiver instalado a antiga versão 156 clubes, execute DESFAZER nela antes de aplicar esta versão.\\n\\nDeseja continuar?"
if text.count(before)!=1:raise RuntimeError("Install warning source mismatch")
text=text.replace(before,after)
path.write_text(text,encoding="utf-8")
print("Windows GUI text updated for 20 x 4 and safe previous-version migration.")
