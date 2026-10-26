#!/usr/bin/env python3
"""Atualiza o website DEPOIS de confirmar uma release real com EXE e SHA-256.

Não publica artefatos nem chama API. O orquestrador fornece apenas metadados
já verificados do GitHub Releases. Falha ao encontrar marcadores HTML esperados.
"""
from __future__ import annotations

import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import sys
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
VERSION = re.compile(r"2026\.[0-9]+\.[0-9]+\Z")
ASSET = "Brassfoot-Patch-2026-Setup.exe"
URL = "https://github.com/yzPeedro/brassfoot-patch/releases/download/"


def version_tuple(value: str) -> tuple[int, int, int]:
    if not VERSION.fullmatch(value):
        raise ValueError("Versão fora de 2026.n.n")
    return tuple(map(int, value.split(".")))


def write_atomic(path: Path, content: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def replace_marked(html: str, name: str, replacement: str) -> str:
    pattern = re.compile(r'(<(?P<tag>p|h3)\b[^>]*\bdata-release-copy="' +
                         re.escape(name) + r'"[^>]*>)(.*?)(</(?P=tag)>)', re.DOTALL)
    if len(pattern.findall(html)) != 1:
        raise ValueError(f"Não há marcador único do site: {name}")
    return pattern.sub(lambda match: match.group(1) + replacement + match.group(4), html, count=1)


def replace_guide(doc: str, body: str) -> str:
    marker = re.compile(r'(<main class="guide">[\s\S]*?<a class="home"[^>]*>.*?</a>)'
                        r'[\s\S]*?(<p class="muted">)')
    if len(marker.findall(doc)) != 1:
        raise ValueError("Guia estático mudou; não substituí-lo às cegas")
    return marker.sub(lambda m: m.group(1) + "\n" + body + "\n" + m.group(2), doc, count=1)


def build(previous: dict, version: str, size: int, digest: str, published: date,
          notes: str) -> dict[Path, str]:
    if version_tuple(version) <= version_tuple(previous["publishedVersion"]):
        raise ValueError("A nova release precisa de versão maior que a versão atual")
    if not SHA256.fullmatch(digest) or size <= 0:
        raise ValueError("Integridade pública ausente")
    if not notes.strip():
        raise ValueError("Release sem changelog")
    if len(notes) > 10000:
        raise ValueError("Notas maiores que o limite permitido")

    metadata = {
        "schemaVersion": 1,
        "status": "published",
        "publishedVersion": version,
        "publishedAt": published.isoformat(),
        "assetName": ASSET,
        "downloadUrl": URL + "v" + version + "/" + quote(ASSET),
        "fileSizeBytes": size,
        "sha256": digest,
        "compatibilityVerifiedInGame": True,
        "scopeOfGameValidation": "Instalação in-place verificada automaticamente em instalação isolada e validada no Brasfoot Windows antes da publicação",
        "competitionSeason": 2026,
        "serieDConfigPreserved": True,
        "serieDMembershipMayChange": True,
        "rostersBCStatus": "verified-2026",
        "installationMode": "in-place",
        "releaseNotes": notes.strip(),
    }
    replacements = {
        "hero": "Ano 2026 e 60 clubes brasileiros nas Séries A, B e C, com 20 times por divisão e elencos B/C atualizados e verificados nesta edição.",
        "method": "Instalação direta no Brasfoot já existente: os arquivos afetados recebem backup íntegro, as alterações são verificadas e o jogo permanece na pasta original.",
        "installer": "A versão " + version + " atualiza a instalação existente do Brasfoot 22–23, com ano inicial 2026, elencos A/B/C, backup e restauração, sem exigir outra cópia do jogo.",
        "step3-title": "Atualização na pasta original",
        "step3": "O instalador substitui apenas arquivos previamente reconhecidos, mantendo diretório, atalhos e saves originais.",
        "step4": "O executável e os demais arquivos atualizados recebem backup por SHA-256. Se houver falha, o instalador restaura os originais verificados.",
        "limitations": "Versão " + version + ": atualiza os 60 clubes A/B/C com elencos 2026 verificados, mantendo o ano inicial 2026. Série D e saves preservados conforme o manifesto. Consulte a release para restrições específicas.",
        "release": "Versão " + version + ": patch gratuito in-place com elencos 2026 das Séries A/B/C. Sem segunda instalação do jogo.",
        "faq-download": "Sim. A versão " + version + " está disponível como instalador gráfico Windows e atualiza a instalação existente. Confira os requisitos de compatibilidade antes de executar.",
        "faq-saves": "Não. O instalador faz backup dos arquivos afetados, inclusive do executável original, e não altera os bytes dos saves. A compatibilidade com carreiras antigas pode exigir iniciar uma nova carreira.",
        "faq-terminal": "Não. Baixe o instalador Windows .exe, informe a pasta do Brasfoot e acompanhe a atualização pela janela gráfica. Não exige PowerShell ou ferramentas de desenvolvimento.",
    }
    changes: dict[Path, str] = {}
    index_file = SITE / "index.html"
    html = index_file.read_text(encoding="utf-8")
    for name, body in replacements.items():
        html = replace_marked(html, name, escape(body))
    previous_software_version = '"softwareVersion": "' + previous["publishedVersion"] + '"'
    if html.count(previous_software_version) != 1:
        raise ValueError("Versão JSON-LD não encontrada ou ambígua")
    html = html.replace(previous_software_version, '"softwareVersion": "' + version + '"', 1)
    changes[index_file] = html

    guide_file = SITE / "como-instalar" / "index.html"
    guide = guide_file.read_text(encoding="utf-8")
    guide_body = (f'<h1>Como instalar o Brasfoot Patch {version}</h1>'
        '<p class="lead">Este patch é gratuito e precisa do Brasfoot 22–23 previamente instalado no Windows.</p>'
        '<h2>1. Baixe o instalador gráfico</h2><p>Use o botão principal do site ou '
        f'<a href="{metadata["downloadUrl"]}">o executável da versão {version}</a>. '
        'Não é necessário baixar o jogo completo.</p>'
        '<h2>2. Indique a pasta existente do Brasfoot</h2>'
        '<p>O instalador detecta instalações comuns ou permite selecionar a pasta. '
        'Confere versão, assinatura de arquivos, integridade e espaço livre antes de alterar dados.</p>'
        '<h2>3. Atualize na pasta original</h2>'
        '<p>Após confirmar a compatibilidade, ele verifica que o Brasfoot está fechado, cria '
        'backups íntegros do executável e dos demais arquivos afetados e aplica alterações '
        'diferenciais. Não cria uma segunda instalação.</p>'
        '<h2>4. Abra o mesmo Brasfoot</h2>'
        '<p>Use o atalho habitual. O seletor de ano oferece 2026 e os clubes nacionais A/B/C '
        'seguem a temporada. Os saves preexistentes são preservados.</p>'
        '<h2>Se algo falhar</h2><p>O rollback devolve os arquivos de backup. Não force versões '
        'desconhecidas nem abra o Brasfoot durante a instalação. '
        '<a href="../compatibilidade/">Veja compatibilidade e segurança.</a></p>')
    changes[guide_file] = replace_guide(guide, guide_body)

    compat_file = SITE / "compatibilidade" / "index.html"
    compat = compat_file.read_text(encoding="utf-8")
    compat_body = (f'<h1>Compatibilidade e backups — {version}</h1>'
        '<p class="lead">Esta edição reconhece versões exatas do Brasfoot 22–23 por SHA-256 '
        'e atualiza o jogo que já está instalado.</p>'
        '<h2>Executável original</h2><p>O arquivo bf22-23.exe recebe um backup permanente, '
        'que é conferido antes da substituição por operações diferenciais. '
        'Arquivos de origem desconhecida são recusados.</p>'
        '<h2>Saves e atalhos</h2><p>O mesmo diretório e atalhos continuam sendo usados. '
        'Saves e preferências não são reescritos, embora a compatibilidade de '
        'carreiras antigas com regras alteradas não possa ser presumida.</p>'
        '<h2>Séries A, B, C e D</h2><p>São 20 clubes por divisão nacional A/B/C, '
        'elencos de 2026 verificados e configuração original da Série D preservada. '
        'Veja as notas da release para limites de calendário e temporadas.</p>'
        '<h2>Restauração</h2><p>O sistema verifica SHA-256 antes de desfazer o patch; '
        'não sobrescreve alterações de origem desconhecida realizadas posteriormente.</p>')
    changes[compat_file] = replace_guide(compat, compat_body)

    history_file = SITE / "versoes" / "index.html"
    history = history_file.read_text(encoding="utf-8")
    marker = "<h2>2026.2.0"
    if history.count(marker) != 1:
        raise ValueError("Ponto de inserção do changelog desapareceu")
    new_entry = (f'<h2>{version} — {published.strftime("%d/%m/%Y")}</h2>'
                 '<p>Instalador gráfico in-place, backup integral dos arquivos afetados, '
                 'elencos A/B/C atualizados para 2026 e publicação automática com SHA-256. '
                 f'<a href="https://github.com/yzPeedro/brassfoot-patch/releases/tag/v{version}">'
                 'Detalhes e artefato público</a>.</p>\n')
    changes[history_file] = history.replace(marker, new_entry + marker, 1)
    sitemap_file = SITE / "sitemap.xml"
    sitemap = sitemap_file.read_text(encoding="utf-8")
    if "<lastmod>" not in sitemap:
        raise ValueError("Sitemap não tem datas verificáveis")
    changes[sitemap_file] = re.sub(r"<lastmod>\d{4}-\d\d-\d\d</lastmod>",
                                   "<lastmod>" + published.isoformat() + "</lastmod>", sitemap)
    changes[SITE / "data" / "release.json"] = json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--file-size", type=int, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--published-at", required=True)
    parser.add_argument("--notes-file", type=Path, required=True)
    args = parser.parse_args()
    if args.filename != ASSET:
        parser.error("O download principal precisa ser Brassfoot-Patch-2026-Setup.exe")
    try:
        day = date.fromisoformat(args.published_at)
        previous = json.loads((SITE / "data" / "release.json").read_text(encoding="utf-8"))
        notes = args.notes_file.read_text(encoding="utf-8")
        changes = build(previous, args.version, args.file_size, args.sha256, day, notes)
        for path, value in changes.items():
            write_atomic(path, value)
        print(f"Site preparado para release pública v{args.version}: {len(changes)} arquivos")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Site NÃO atualizado: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
