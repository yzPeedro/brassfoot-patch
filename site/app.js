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
    .then((metadata) => { if (metadata?.schemaVersion === 1) setReady(metadata); })
    .catch(() => {
      // Keep download controls disabled and expose a meaningful error.
      detail.textContent = 'Não foi possível consultar o estado da versão. Nenhum download será oferecido até confirmar os dados.';
    });
})();
