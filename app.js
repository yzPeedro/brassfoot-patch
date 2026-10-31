(() => {
  'use strict';

  const byId = id => document.getElementById(id);
  const all = selector => [...document.querySelectorAll(selector)];
  const scriptUrl = document.currentScript?.src || new URL('./app.js', location.href).href;
  const dataUrl = name => new URL('./data/' + name, scriptUrl).href;
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  const menu = byId('mobile-menu');
  const nav = byId('nav');

  function closeNavigation() {
    menu?.setAttribute('aria-expanded', 'false');
    nav?.classList.remove('open');
  }
  menu?.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open));
    nav?.classList.toggle('open', open);
  });
  nav?.addEventListener('click', event => {
    if (event.target.closest('a')) closeNavigation();
  });

  // Ordinary links remain usable before JavaScript or the manifest has loaded.
  const releaseBase = 'https://github.com/yzPeedro/brassfoot-patch/releases/';
  const currentVersion = '2026.4.1';
  const platforms = {windows: 'Windows', linux: 'Linux', darwin: 'macOS'};
  const packages = [
    {platform: 'windows', architecture: 'amd64', label: 'Windows · 64 bits', file: 'windows-x64.exe'},
    {platform: 'linux', architecture: 'amd64', label: 'Linux · Intel / AMD', file: 'linux-x64.tar.gz'},
    {platform: 'linux', architecture: 'arm64', label: 'Linux · ARM64', file: 'linux-arm64.tar.gz'},
    {platform: 'darwin', architecture: 'amd64', label: 'macOS · Intel', file: 'macos-x64.tar.gz'},
    {platform: 'darwin', architecture: 'arm64', label: 'macOS · Apple Silicon', file: 'macos-arm64.tar.gz'}
  ];
  const packageKey = item => item.platform + '-' + item.architecture;
  const agent = navigator.userAgentData?.platform || navigator.platform || navigator.userAgent;
  const mobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent) ||
    (/Mac/i.test(agent) && navigator.maxTouchPoints > 1);
  const detectedOS = mobile ? null : /win/i.test(agent) ? 'windows' : /mac/i.test(agent) ? 'darwin' : /linux/i.test(agent) ? 'linux' : null;
  const reportedArm = /aarch64|arm64/i.test(navigator.userAgent + ' ' + agent);
  let selectedKey = (detectedOS || 'windows') + (reportedArm && detectedOS && detectedOS !== 'windows' ? '-arm64' : '-amd64');
  let architectureKnown = reportedArm || detectedOS === 'windows';
  let userSelected = false;
  let manifest = null;
  const choices = all('.download-options');

  function artifactFor(item) {
    return manifest?.artifacts.find(artifact => packageKey(artifact) === packageKey(item));
  }
  function artifactUrl(item) {
    // The stable alias follows the newest release even if metadata is cached.
    return releaseBase + 'latest/download/Brasfoot-Mega-Patch-' + item.file;
  }
  function sizeLabel(bytes) {
    return (bytes / 1048576).toLocaleString('pt-BR', {maximumFractionDigits: 1}) + ' MB';
  }
  function refreshDownloads() {
    const selected = packages.find(item => packageKey(item) === selectedKey) || packages[0];
    const artifact = artifactFor(selected);
    all('[data-download-primary]').forEach(link => {
      link.href = artifactUrl(selected);
      link.setAttribute('aria-label', 'Baixar Brasfoot Mega Patch para ' + selected.label);
      const label = link.querySelector('[data-download-label]');
      if (label) label.textContent = selected.label;
    });
    all('[data-download-platform]').forEach(link => {
      const item = packages.find(entry => packageKey(entry) === link.dataset.downloadPlatform);
      if (!item) return;
      link.href = artifactUrl(item);
      link.classList.toggle('is-selected', packageKey(item) === selectedKey);
      const size = link.querySelector('[data-download-size]');
      const match = artifactFor(item);
      if (size) size.textContent = match ? sizeLabel(match.sizeBytes) : item.architecture === 'arm64' ? 'ARM64' : '64 bits';
    });
    all('[data-platform-note]').forEach(note => {
      note.textContent = selected.platform === 'windows'
        ? 'Requer sua própria instalação do Brasfoot 22–23.'
        : 'Para jogar: Brasfoot 22–23 e Wine/CrossOver configurado à parte. Execução neste sistema ainda não verificada.';
    });
    const detected = byId('detected-os');
    if (detected) detected.textContent = userSelected ? 'DOWNLOAD PARA ' + platforms[selected.platform].toUpperCase()
      : detectedOS ? platforms[detectedOS].toUpperCase() + ' IDENTIFICADO' : 'ESCOLHA O COMPUTADOR DE DESTINO';
    all('[data-download-hint]').forEach(hint => {
      hint.textContent = !detectedOS && !userSelected ? 'Use a seta para escolher o sistema do seu computador.'
        : !architectureKnown && !userSelected && selected.platform !== 'windows'
          ? 'Confira a arquitetura do seu computador nas opções da seta.' : 'Outro sistema? Todas as opções estão na seta ao lado.';
    });
    all('[data-release-version]').forEach(label => { label.textContent = manifest?.version || currentVersion; });
    if (byId('release-detail')) byId('release-detail').textContent = artifact
      ? `${artifact.name} · ${sizeLabel(artifact.sizeBytes)}`
      : 'Os dados do arquivo estão disponíveis nas notas da versão mais recente.';
    if (byId('asset-hash')) {
      byId('asset-hash').textContent = artifact ? 'SHA-256: ' + artifact.sha256 : '';
      byId('asset-hash').hidden = !artifact;
    }
  }
  function closeChoices(except) {
    choices.forEach(choice => { if (choice !== except) choice.open = false; });
  }
  choices.forEach(choice => {
    choice.addEventListener('toggle', () => { if (choice.open) closeChoices(choice); });
    choice.addEventListener('click', event => {
      const link = event.target.closest('[data-download-platform]');
      if (!link) return;
      selectedKey = link.dataset.downloadPlatform;
      userSelected = true;
      architectureKnown = true;
      refreshDownloads();
      closeChoices();
      choice.querySelector('summary')?.focus();
      // Preserve the link's native navigation: selecting an option downloads it.
    });
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.download-options')) closeChoices();
    if (!event.target.closest('.site-header')) closeNavigation();
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const openChoice = choices.find(choice => choice.open);
    if (openChoice) { closeChoices(); openChoice.querySelector('summary')?.focus(); }
    if (menu?.getAttribute('aria-expanded') === 'true') { closeNavigation(); menu.focus(); }
  });
  refreshDownloads();

  // Browsers that expose architecture can refine the default; explicit choices win.
  if (detectedOS && navigator.userAgentData?.getHighEntropyValues) {
    navigator.userAgentData.getHighEntropyValues(['architecture', 'bitness']).then(info => {
      if (userSelected || !info.architecture) return;
      if (detectedOS !== 'windows') selectedKey = detectedOS + (/arm/i.test(info.architecture) ? '-arm64' : '-amd64');
      architectureKnown = true;
      refreshDownloads();
    }).catch(() => {});
  }

  // A finite entrance animation keeps text readable and avoids perpetual motion.
  const hero = byId('inicio');
  if (hero && !motion.matches) hero.classList.add('hero-animate');
  const revealElements = all('[data-reveal], .section-heading, .coverage-grid article, .principles > div, .guide-band .wrap, .faq > div');
  let revealObserver;
  if ('IntersectionObserver' in window && !motion.matches) {
    revealObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      });
    }, {threshold: 0.08});
    revealElements.forEach((element, index) => {
      if (element.getBoundingClientRect().top <= window.innerHeight) return;
      element.classList.add('reveal-ready');
      element.style.setProperty('--reveal-delay', (index % 3) * 60 + 'ms');
      revealObserver.observe(element);
    });
  }

  // Only decorative layers follow the pointer; controls and copy remain stable.
  let pointerFrame = 0;
  let pointerTarget = null;
  const board = hero?.querySelector('.season-board');
  function resetPointer() {
    cancelAnimationFrame(pointerFrame);
    pointerFrame = 0;
    pointerTarget = null;
    hero?.style.removeProperty('--spot-x');
    hero?.style.removeProperty('--spot-y');
    board?.style.removeProperty('--board-x');
    board?.style.removeProperty('--board-y');
  }
  hero?.addEventListener('pointermove', event => {
    if (motion.matches || !finePointer.matches || event.pointerType !== 'mouse') return;
    pointerTarget = {x: event.clientX, y: event.clientY};
    if (pointerFrame) return;
    pointerFrame = requestAnimationFrame(() => {
      pointerFrame = 0;
      if (!pointerTarget) return;
      const rect = hero.getBoundingClientRect();
      const x = Math.max(0, Math.min(1, (pointerTarget.x - rect.left) / rect.width));
      const y = Math.max(0, Math.min(1, (pointerTarget.y - rect.top) / rect.height));
      hero.style.setProperty('--spot-x', (x * 100).toFixed(2) + '%');
      hero.style.setProperty('--spot-y', (y * 100).toFixed(2) + '%');
      board?.style.setProperty('--board-x', ((x - 0.5) * 5).toFixed(2) + 'deg');
      board?.style.setProperty('--board-y', ((0.5 - y) * 5).toFixed(2) + 'deg');
    });
  });
  hero?.addEventListener('pointerleave', resetPointer);
  motion.addEventListener('change', () => {
    if (!motion.matches) return;
    resetPointer();
    hero?.classList.remove('hero-animate');
    revealObserver?.disconnect();
    revealElements.forEach(element => element.classList.add('is-visible'));
  });

  if (typeof fetch !== 'function') return;
  fetch(dataUrl('distribution.json'), {cache: 'no-cache'}).then(response => response.ok ? response.json() : null).then(data => {
    if (!data || !/^20\d{2}\.\d+\.\d+$/.test(data.version) || data.status !== 'published' ||
        (data.channel && data.channel !== 'stable') || !Array.isArray(data.artifacts)) return;
    const parts = data.version.split('.').map(Number);
    const minimum = currentVersion.split('.').map(Number);
    const firstDifference = parts.findIndex((part, index) => part !== minimum[index]);
    if (firstDifference !== -1 && parts[firstDifference] < minimum[firstDifference]) return;
    const prefix = releaseBase + 'download/v' + data.version + '/';
    if (data.artifacts.length !== packages.length || new Set(data.artifacts.map(packageKey)).size !== packages.length ||
        data.artifacts.some(item => {
          const known = packages.find(entry => packageKey(entry) === packageKey(item));
          return !known || !/^[a-zA-Z0-9._-]+$/.test(item.name) ||
            (item.downloadUrl !== artifactUrl(known) && item.downloadUrl !== prefix + item.name) ||
            !/^[a-f0-9]{64}$/.test(item.sha256) || !Number.isSafeInteger(item.sizeBytes) || item.sizeBytes <= 0;
        })) return;
    manifest = data;
    refreshDownloads();
  }).catch(() => {});

  fetch(dataUrl('roster-coverage.json'), {cache: 'no-cache'}).then(response => response.ok ? response.json() : null).then(data => {
    if (!data?.counts) return;
    all('[data-roster-count]').forEach(element => {
      const count = data.counts[element.dataset.rosterCount];
      if (Number.isSafeInteger(count) && count >= 0) element.textContent = count.toLocaleString('pt-BR');
    });
  }).catch(() => {});
  if (!byId('world-countries')) return;
  fetch(dataUrl('world-status.json'), {cache: 'no-cache'}).then(response => response.ok ? response.json() : null).then(data => {
    if (!data) return;
    const counts = data.coverage || data.counts || data.summary || {};
    const metrics = {'world-countries': counts.countries ?? counts.countriesCataloged, 'world-competitions': counts.competitions ?? counts.competitionsCataloged, 'world-clubs': counts.clubs ?? counts.clubsCataloged};
    for (const [id, count] of Object.entries(metrics)) {
      if (byId(id) && Number.isInteger(count) && count >= 0) byId(id).textContent = count.toLocaleString('pt-BR');
    }
    const when = data.updatedAt || data.observedAt || data.generatedAt;
    if (when && !Number.isNaN(Date.parse(when)) && byId('world-freshness')) {
      byId('world-freshness').textContent = 'Última coleta: ' + new Date(when).toLocaleString('pt-BR', {timeZone: 'America/Sao_Paulo'}) + ' (Brasília). O catálogo não representa novas ligas jogáveis.';
    }
  }).catch(() => {});
})();

// Patch notes progressively replace a complete, readable static fallback.
(() => {
  'use strict';
  const list = document.getElementById('patch-notes-list');
  if (!list || typeof fetch !== 'function') return;
  const script = document.currentScript?.src || new URL('./app.js', location.href).href;
  const node = (tag, className, value) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (value) el.textContent = value;
    return el;
  };
  fetch(new URL('./data/patch-notes.json', script), {cache: 'no-cache'})
    .then(response => response.ok ? response.json() : null)
    .then(data => {
      if (data?.schemaVersion !== 1 || !Array.isArray(data.entries)) return;
      const valid = data.entries.filter(entry => entry && typeof entry.title === 'string' &&
        typeof entry.summary === 'string' && ['site', 'patch'].includes(entry.kind) &&
        Array.isArray(entry.changes) && !Number.isNaN(Date.parse(entry.date)));
      if (!valid.length) return;
      const content = document.createDocumentFragment();
      valid.forEach(entry => {
        const article = node('article', 'patch-note');
        const date = node('div', 'patch-note-date');
        date.append(node('span', 'note-orbit'));
        const time = node('time', '', new Date(entry.date).toLocaleDateString('pt-BR',
          {day: '2-digit', month: 'short', year: 'numeric', timeZone: 'America/Sao_Paulo'}).toUpperCase());
        time.dateTime = entry.date;
        date.append(time, node('span', 'note-kind', entry.kind === 'site' ? 'SITE' : 'PATCH'));
        const body = node('div', 'patch-note-body');
        body.append(node('span', 'note-version', entry.version ? 'VERSÃO ' + entry.version : 'NOVIDADES DO PROJETO'),
          node('h3', '', entry.title), node('p', '', entry.summary));
        const changes = node('ul');
        entry.changes.filter(change => typeof change === 'string').forEach(change => changes.append(node('li', '', change)));
        body.append(changes);
        if (entry.url) {
          try {
            const url = new URL(entry.url);
            if (url.protocol === 'https:' && url.hostname === 'github.com') {
              const link = node('a', 'text-link note-source', 'Ver notas da versão ↗');
              link.href = url.href;
              body.append(link);
            }
          } catch (_) {}
        }
        const arrow = node('span', 'note-arrow', '↗');
        arrow.setAttribute('aria-hidden', 'true');
        article.append(date, body, arrow);
        content.append(article);
      });
      list.replaceChildren(content);
    }).catch(() => {});
})();

(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const toggle = document.getElementById('motion-toggle');
  toggle?.addEventListener('click', () => {
    const paused = document.body.classList.toggle('motion-paused');
    toggle.setAttribute('aria-pressed', String(paused));
    toggle.textContent = paused ? 'Retomar movimento ▷' : 'Pausar movimento Ⅱ';
  });
  if (reduce.matches || !('IntersectionObserver' in window)) return;
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (!entry.isIntersecting) return;
    observer.unobserve(entry.target);
    const el = entry.target;
    const text = el.firstChild;
    const target = Number(el.dataset.countup);
    const suffix = el.dataset.countupSuffix || '';
    const start = performance.now();
    const frame = now => {
      if (reduce.matches) { text.textContent = target.toLocaleString('pt-BR') + suffix; return; }
      const progress = Math.min((now - start) / 1100, 1);
      text.textContent = Math.round(target * (1 - Math.pow(1 - progress, 3))).toLocaleString('pt-BR') + suffix;
      if (progress < 1) requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  }), {threshold: .5});
  document.querySelectorAll('[data-countup]').forEach(el => observer.observe(el));
})();
