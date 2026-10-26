(() => {
  'use strict';

  // The verified release URL is present in HTML. Never block downloads while
  // checking GitHub API or release metadata: users may have CORS/API failures.
  const byId = id => document.getElementById(id);
  const buttons = [byId('download-hero'), byId('download-panel')].filter(Boolean);
  const status = byId('release-status');
  const badge = byId('release-badge');
  const detail = byId('release-detail');
  const version = byId('release-version');
  const alternate = document.querySelector('.release-alt-link');

  const shipped = {
    version: '2026.3.5',
    tag: 'v2026.3.5',
    asset: 'Brasfoot-Patch-V4-Elencos-2026.3.5.exe',
    size: 5419520,
    sha256: 'eb546eec17a6e7e20ffb65a32078bccfdea2e2b7f62f429688e698d5a458e45d'
  };
  const base = 'https://github.com/yzPeedro/brassfoot-patch/releases/download/';
  const releaseUrl = 'https://github.com/yzPeedro/brassfoot-patch/releases/tag/';
  const currentUrl = base + shipped.tag + '/' + shipped.asset;

  function showRelease(versionText, url, sha256) {
    // Anchors work without JavaScript. JS only updates a *verified* newer asset.
    for (const button of buttons) {
      button.href = url;
      button.removeAttribute('aria-disabled');
      button.textContent = 'BAIXAR PATCH ' + versionText + ' ↗';
    }
    if (status) status.textContent = 'DISPONÍVEL';
    if (badge) badge.textContent = 'PUBLICADO';
    if (version) version.textContent = versionText;
    if (detail) detail.textContent = 'Versão ' + versionText + ' · Windows · Download gratuito';
    if (alternate) alternate.href = releaseUrl + 'v' + versionText;
  }

  showRelease(shipped.version, currentUrl, shipped.sha256);

  // Optional enhancement for later releases. A failed fetch never disables
  // the already published and SHA-verified download in the HTML.
  if (typeof fetch !== 'function') return;
  fetch('./data/release.json', {cache:'no-store'}).then(async response => {
    if (!response.ok) return;
    const meta = await response.json();
    if (!meta || meta.status !== 'published' ||
        !/^20[0-9]{2}\.[0-9]+\.[0-9]+$/.test(meta.publishedVersion || '') ||
        !/^[a-f0-9]{64}$/i.test(meta.sha256 || '') ||
        !Number.isInteger(meta.fileSizeBytes) || meta.fileSizeBytes <= 0) return;
    const expected = base + 'v' + meta.publishedVersion + '/' + meta.assetName;
    if (expected !== meta.downloadUrl ||
        !/^Brasfoot-Patch-[a-zA-Z0-9._-]+\.exe$/.test(meta.assetName || '')) return;
    if (meta.publishedVersion === shipped.version) {
      // Current binary already checked against the public release by SHA-256.
      return;
    }
    const api = await fetch('https://api.github.com/repos/yzPeedro/brassfoot-patch/releases/tags/v' + meta.publishedVersion,
      {cache:'no-store', headers:{Accept:'application/vnd.github+json'}});
    if (!api.ok) return;
    const release = await api.json();
    if (release.draft || release.tag_name !== 'v' + meta.publishedVersion) return;
    const asset = (release.assets || []).find(item =>
      item.name === meta.assetName && item.state === 'uploaded' &&
      item.size === meta.fileSizeBytes &&
      item.browser_download_url === expected &&
      item.digest === 'sha256:' + meta.sha256);
    if (asset) showRelease(meta.publishedVersion, expected, meta.sha256);
  }).catch(() => {
    // The static download remains functional when offline or rate-limited.
  });
})();
