"""Patch GUI copy ONLY in alpha workflow; do not affect stable release source."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"windows-installer"/"main_windows.go"
s=p.read_text(encoding="utf8")
changes={
"PRÉVIA 2026.0.2 — ACOMPANHE LIMITAÇÕES":"ALFA 2026.1.0 - JOGO NAO HOMOLOGADO",
"20 clubes brasileiros  •  730 atletas  •  Temporada 2026":"156 clubes: 20 A, 90 historicos e 46 gerados • 2026",
"PRÉVIA EXPERIMENTAL: 713 jogadores com atributos estimados. Compatibilidade testada; dados ainda estimados.":"ALFA SEM TESTE NO JOGO: 46 times com atletas FICTICIOS. Serie D 96/16 nao homologada.",
"Isto vai restaurar os 20 arquivos originais das equipes a partir do backup conferido.":"Isto vai desfazer apenas as alteracoes desta transacao, incluindo clubes e BRA.cfg.",
"Somente arquivos teams/*.ban serão alterados. Carreiras, saves e configurações serão preservados.":"Equipes e BRA.cfg serao alterados. Saves ficam fora do patch. Teste somente em copia isolada.",
"A compatibilidade foi testada pelo criador do patch; elencos incluem atributos estimados.":"Esta ALFA NAO FOI TESTADA DENTRO DO BRASFOOT. 46 times tem jogadores ficticios.",
}
for before,after in changes.items():
 if s.count(before)!=1: raise RuntimeError("GUI source changed: "+before)
 s=s.replace(before,after)
before="Jogo detectado e %d arquivos de equipes verificados.\\n\\nEsta é uma PRÉVIA COM DADOS ESTIMADOS: 713 jogadores têm atributos estimados.\\n\\nO instalador vai substituir SOMENTE os %d arquivos .ban aprovados em teams/. Vai salvar antes backups íntegros em AppData; NÃO vai editar saves, carreiras ou configurações.\\n\\nSalve e FECHE o Brasfoot antes de continuar.\\n\\nDeseja instalar na pasta selecionada?"
after="ALFA 2026.1.0, %d itens verificados.\\n\\n46 clubes novos com 18 ATLETAS FICTICIOS. 90 clubes historicos de 2022/23 sem atualizacao. Serie D 96/16 NAO TESTADA NO JOGO.\\n\\nO instalador vai modificar ate %d arquivos, inclusive BRA.cfg, com backup e opcao de desfazer. Seus saves nao sao editados.\\n\\nUSE APENAS EM COPIA ISOLADA DO BRASFOOT! Feche o jogo. Deseja continuar?"
if s.count(before)!=1:raise RuntimeError("Confirmation dialog changed")
s=s.replace(before,after)
p.write_text(s,encoding="utf8")
print("Alpha GUI marked prominently as unverified and requires opt-in.")
