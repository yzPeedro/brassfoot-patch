(() => {
  'use strict';
  const menu = document.getElementById('mobile-menu');
  const nav = document.getElementById('nav');
  menu?.addEventListener('click', () => {
    const opened = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(opened));
    menu.setAttribute('aria-label', opened ? 'Fechar menu' : 'Abrir menu');
    nav.classList.toggle('open', opened);
  });
  nav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
    nav.classList.remove('open');
    menu?.setAttribute('aria-expanded', 'false');
    menu?.setAttribute('aria-label', 'Abrir menu');
  }));

  const status = document.getElementById('release-status');
  const badge = document.getElementById('release-badge');
  const version = document.getElementById('release-version');
  const detail = document.getElementById('release-detail');
  const heroButton = document.getElementById('download-hero');
  const panelButton = document.getElementById('download-panel');
  const disclaimer = document.getElementById('release-status-text');
  const buttons = [heroButton, panelButton];

  function setReady(release) {
    // Never trust a metadata file by itself as proof that a release is safe.
    // A public HTTPS link and integrity metadata are mandatory before enabling downloads.
    const url = typeof release.downloadUrl === 'string' ? release.downloadUrl : '';
    let parsed;
    try { parsed = new URL(url); } catch { return; }
    if (parsed.protocol !== 'https:' || parsed.hostname !== 'github.com' ||
        !/^\/[\w.-]+\/[\w.-]+\/releases\/download\//.test(parsed.pathname)) return;
    if (release.status !== 'published' || release.compatibilityVerifiedInGame !== true ||
        typeof release.publishedVersion !== 'string' || !/^\d{4}\.\d+\.\d+$/.test(release.publishedVersion) ||
        !/^[a-f\d]{64}$/i.test(release.sha256 || '') ||
        !Number.isInteger(release.fileSizeBytes) || release.fileSizeBytes <= 0) return;
    version.textContent = release.publishedVersion;
    status.textContent = 'DISPONÍVEL';
    badge.textContent = 'PUBLICADO';
    badge.style.color = '#c5ff69';
    detail.textContent = `SHA-256: ${release.sha256}. Verifique a integridade antes de instalar.`;
    disclaimer.textContent = `Versão ${release.publishedVersion} publicada em ${release.publishedAt || 'data não informada'}.`;
    for (const button of buttons) {
      button.disabled = false;
      button.textContent = `BAIXAR VERSÃO ${release.publishedVersion} ↗`;
      button.addEventListener('click', () => { window.location.assign(parsed.href); });
    }
  }

  fetch('./data/release.json', { cache: 'no-cache' })
    .then((r) => { if (!r.ok) throw new Error(`Release manifest HTTP ${r.status}`); return r.json(); })
    .then(async (metadata) => {
      if (metadata?.schemaVersion !== 1 || !['published','awaiting_release'].includes(metadata.status)) return;
      if (metadata.publishedVersion !== '2026.0.2' ||
          !/^[a-f0-9]{64}$/i.test(metadata.sha256 || '') ||
          !Number.isInteger(metadata.fileSizeBytes) || metadata.fileSizeBytes <= 0) return;
      const expected = 'https://github.com/yzPeedro/brassfoot-patch/releases/download/v2026.0.2/Brassfoot-Patch-2026-Setup.exe';
      if (metadata.downloadUrl !== expected) return;
      version.textContent = metadata.publishedVersion;
      detail.textContent = 'Confirmando a integridade do instalador público no GitHub Releases...';
      const response = await fetch('https://api.github.com/repos/yzPeedro/brassfoot-patch/releases/tags/v2026.0.2', {
        cache: 'no-store', headers: { Accept: 'application/vnd.github+json' }
      });
      if (response.status === 404) return;
      if (!response.ok) throw new Error('Não foi possível verificar a release no GitHub.');
      const release = await response.json();
      if (release.draft || release.prerelease || release.tag_name !== 'v2026.0.2') return;
      const asset = (release.assets || []).find((item) =>
        item.name === 'Brassfoot-Patch-2026-Setup.exe' && item.state === 'uploaded' &&
        item.browser_download_url === expected && item.size === metadata.fileSizeBytes &&
        item.digest === 'sha256:' + metadata.sha256
      );
      if (!asset) {
        detail.textContent = 'Arquivo da release não passou na verificação de SHA-256 e tamanho. Download bloqueado.';
        return;
      }
      setReady({ ...metadata, status: 'published', publishedAt: release.published_at?.slice(0, 10) });
    })
    .catch(() => {
      // Keep download controls disabled and expose a meaningful error.
      detail.textContent = 'Não foi possível consultar o estado da versão. Nenhum download será oferecido até confirmar os dados.';
    });
})();
