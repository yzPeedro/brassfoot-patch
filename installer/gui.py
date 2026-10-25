"""Offline graphical Brasfoot installer; no terminal, network or API credentials."""
from __future__ import annotations

import os
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog

from .engine import InstallerError, inspect, install

DARK = '#071b18'
PANEL = '#102b25'
LIME = '#bdff63'
WHITE = '#eef6ed'
MUTED = '#adc6b8'
RED = '#ff9d8e'


def _payload() -> Path:
    bundle_root = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
    return bundle_root / 'payload'


def _backup_root() -> Path:
    local = os.environ.get('LOCALAPPDATA')
    return Path(local) / 'BrasfootPatch2026' / 'backups' if local else Path.home() / '.brassfoot-patch' / 'backups'


def _common_game_paths() -> list[Path]:
    locations = []
    for root in (os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)'), str(Path.home())):
        if not root:
            continue
        for name in ('Brasfoot 2022-2023', 'Brasfoot 2022', 'Brasfoot 2023', 'Brasfoot'):
            candidate = Path(root) / name
            if candidate not in locations:
                locations.append(candidate)
    return locations


class Window:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('Brasfoot Patch 2026 — Instalador')
        self.root.geometry('850x610')
        self.root.minsize(710, 520)
        self.root.configure(bg=DARK)
        self.events: queue.Queue[tuple] = queue.Queue()
        self.cancelled = threading.Event()
        self.plan = None
        self.busy = False
        self.page = 0
        self.path = tk.StringVar(value=next((str(p) for p in _common_game_paths() if (p / 'teams').is_dir()), ''))
        self.title_var = tk.StringVar(value='BRASFOOT PATCH 2026')
        self.subtitle_var = tk.StringVar(value='Atualização de futebol brasileiro para instalações compatíveis.')
        self.status_var = tk.StringVar(value='Pronto para verificar a instalação.')
        self.progress_var = tk.DoubleVar(value=0)
        self.layout()
        self.show_intro()
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.root.after(80, self.drain)

    def label(self, parent, text, size=13, bold=False, color=WHITE):
        return tk.Label(parent, text=text, fg=color, bg=parent['bg'],
                        font=('Segoe UI', size, 'bold' if bold else 'normal'),
                        justify='left', wraplength=740, anchor='w')

    def button(self, parent, text, action, primary=True):
        bg = LIME if primary else PANEL
        fg = DARK if primary else WHITE
        b = tk.Button(parent, text=text, command=action, bg=bg, fg=fg,
                      activebackground='#daffad', activeforeground=DARK,
                      font=('Segoe UI', 12, 'bold'), bd=0, padx=24, pady=14,
                      highlightthickness=0, cursor='hand2')
        b.pack(side='left', padx=(0, 12), pady=(10, 0))
        return b

    def layout(self):
        bar = tk.Frame(self.root, bg=LIME, height=7)
        bar.pack(fill='x')
        header = tk.Frame(self.root, bg=DARK, padx=40, pady=28)
        header.pack(fill='x')
        self.label(header, 'BRASFOOT  /  PATCH 2026', 13, True, LIME).pack(anchor='w')
        self.label(header, 'INSTALADOR WINDOWS', 28, True).pack(anchor='w', pady=(7, 0))
        self.steps = tk.Frame(self.root, bg=DARK, padx=40)
        self.steps.pack(fill='x')
        self.step_widgets = []
        for value in ('01  INÍCIO', '02  LOCALIZAR', '03  VERIFICAR', '04  INSTALAR', '05  CONCLUIR'):
            l = self.label(self.steps, value, 10, True, MUTED)
            l.pack(side='left', padx=(0, 17))
            self.step_widgets.append(l)
        self.panel = tk.Frame(self.root, bg=PANEL, padx=40, pady=35)
        self.panel.pack(fill='both', expand=True, padx=40, pady=22)

    def stage(self, page: int, title: str, description: str):
        self.page = page
        for i, w in enumerate(self.step_widgets):
            w.configure(fg=LIME if i == min(page, 4) else MUTED)
        for child in self.panel.winfo_children():
            child.destroy()
        self.label(self.panel, title, 24, True).pack(anchor='w', pady=(0, 12))
        self.label(self.panel, description, 13, False, MUTED).pack(anchor='w', pady=(0, 25))
        body = tk.Frame(self.panel, bg=PANEL)
        body.pack(fill='both', expand=True)
        return body

    def show_intro(self):
        body = self.stage(0, 'A temporada começa aqui.',
                          'O instalador verifica uma instalação original, cria backup dos arquivos afetados e valida cada cópia. Não modifica seus saves.')
        self.label(body, 'Funciona offline. Não precisa de Python, chave de API ou conhecimento técnico.', 14).pack(anchor='w', pady=(0, 28))
        self.label(body, 'IMPORTANTE: somente pacotes com compatibilidade comprovada são aceitos.', 12, True, LIME).pack(anchor='w')
        self.button(body, 'COMEÇAR  →', self.show_location)

    def show_location(self):
        body = self.stage(1, 'Onde está o Brasfoot?',
                          'Selecione a pasta do jogo que contém o diretório teams e o arquivo options.bcf.')
        entry = tk.Entry(body, textvariable=self.path, bg=DARK, fg=WHITE,
                         font=('Segoe UI', 12), relief='flat', insertbackground=WHITE)
        entry.pack(fill='x', ipady=14, pady=(0, 8))
        self.button(body, 'PROCURAR PASTA', self.browse, False)
        self.button(body, 'VERIFICAR INSTALAÇÃO  →', self.start_preflight)
        self.label(body, 'Nenhum arquivo será modificado durante a verificação.', 11, False, MUTED).pack(fill='x', pady=(25, 0))

    def browse(self):
        result = filedialog.askdirectory(title='Localize a pasta do Brasfoot', initialdir=self.path.get() or str(Path.home()))
        if result:
            self.path.set(result)

    def show_busy(self, installing: bool):
        body = self.stage(3 if installing else 2,
                          'Aplicando atualização...' if installing else 'Verificando compatibilidade...',
                          'A instalação só será confirmada depois da verificação final.' if installing
                          else 'Conferindo o pacote, o jogo e as assinaturas dos arquivos originais.')
        self.label(body, '⚽   INTEGRIDADE  ·  BACKUP  ·  INSTALAÇÃO  ·  VERIFICAÇÃO', 12, True, LIME).pack(anchor='w', pady=(0, 24))
        track = tk.Frame(body, height=20, bg=DARK)
        track.pack(fill='x', pady=(0, 18))
        self.filler = tk.Frame(track, height=20, bg=LIME)
        self.filler.place(relx=0, rely=0, relwidth=0, relheight=1)
        self.percent_label = self.label(body, '0%', 26, True)
        self.percent_label.pack(anchor='w')
        self.status_label = self.label(body, 'Preparando...', 12, False, MUTED)
        self.status_label.pack(anchor='w', pady=(8, 18))
        if installing:
            self.button(body, 'CANCELAR E RESTAURAR', self.cancelled.set, False)

    def show_review(self):
        assert self.plan is not None
        body = self.stage(2, 'Verificação concluída.',
                          'A assinatura de cada arquivo original corresponde à lista de versões autorizadas no pacote.')
        self.label(body, f'PATCH: {self.plan.version}    •    TEMPORADA: {self.plan.season}', 15, True, LIME).pack(anchor='w', pady=(0, 18))
        self.label(body, f'ARQUIVOS: {len(self.plan.items)}   •   PASTA: {self.plan.game}', 12).pack(anchor='w', pady=(0, 24))
        if self.plan.already_installed:
            self.label(body, 'Esta versão já está instalada. Nenhuma alteração é necessária.', 13, True, LIME).pack(anchor='w')
            self.button(body, 'CONCLUIR', lambda: self.finish('Versão já instalada.', True))
        else:
            self.label(body, 'Um backup verificado será preservado fora do diretório do jogo.', 12, True).pack(anchor='w')
            self.button(body, 'INSTALAR PATCH  →', self.start_install)
        self.button(body, 'VOLTAR', self.show_location, False)

    def finish(self, message: str, success: bool):
        body = self.stage(4 if success else 2,
                          'PATCH INSTALADO COM SUCESSO!' if success else 'Instalação não concluída',
                          message)
        self.label(body, 'Os backups são mantidos. Os saves não foram modificados.' if success
                   else 'Nenhum sucesso foi anunciado. Se houve falha, consulte os backups para recuperação.',
                   12, False, LIME if success else RED).pack(anchor='w', pady=(0, 18))
        if not success:
            self.button(body, 'ESCOLHER OUTRA PASTA', self.show_location)
        self.button(body, 'FECHAR', self.root.destroy, False)

    def start_preflight(self):
        if self.busy:
            return
        self.busy = True
        self.show_busy(False)
        def worker():
            try:
                path = Path(self.path.get())
                plan = inspect(_payload(), path, progress=lambda s, n, t: self.events.put(('progress', s, n, t)))
                self.events.put(('ready', plan))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def start_install(self):
        if self.busy or not self.plan:
            return
        self.busy = True
        self.cancelled.clear()
        self.show_busy(True)
        def worker():
            try:
                backups = _backup_root()
                backups.mkdir(parents=True, exist_ok=True)
                report = install(self.plan, backups, cancelled=self.cancelled.is_set,
                                 progress=lambda s, n, t: self.events.put(('progress', s, n, t)))
                self.events.put(('complete', report))
            except Exception as exc:
                self.events.put(('error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def drain(self):
        try:
            while True:
                ev = self.events.get_nowait()
                if ev[0] == 'progress':
                    _, stage, done, total = ev
                    # Completion is never shown before the final hash verification.
                    ratio = done / total if total else 0
                    if stage == 'Verificando arquivos':
                        fraction = 0.20 * ratio
                    elif stage == 'Fazendo backup':
                        fraction = 0.20 + 0.20 * ratio
                    elif stage == 'Instalando patch':
                        fraction = 0.40 + 0.55 * ratio
                    else:
                        fraction = 1.0 if stage == 'Concluído' else 0.0
                    self.filler.place_configure(relwidth=fraction)
                    self.percent_label.configure(text=f'{int(fraction * 100)}%')
                    self.status_label.configure(text=f'{stage}: {done}/{total} arquivos')
                elif ev[0] == 'ready':
                    self.busy = False
                    self.plan = ev[1]
                    self.show_review()
                elif ev[0] == 'complete':
                    self.busy = False
                    r = ev[1]
                    self.finish(f"{r['files']} arquivo(s) verificados. Backup: {r.get('backup','não necessário')}", True)
                elif ev[0] == 'error':
                    self.busy = False
                    self.finish(ev[1], False)
        except queue.Empty:
            pass
        self.root.after(80, self.drain)

    def on_close(self):
        if self.busy:
            self.cancelled.set()
            self.root.title('Cancelamento solicitado: restaurando arquivos...')
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    Window(root)
    root.mainloop()


if __name__ == '__main__':
    main()
