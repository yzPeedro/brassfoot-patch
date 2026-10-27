(() => {
  'use strict';
  const byId = id => document.getElementById(id);
  const menu = byId('mobile-menu');
  const nav = byId('nav');
  menu?.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open)); nav?.classList.toggle('open', open);
  });
  nav?.addEventListener('click', event => {
    if (event.target.closest('a')) { menu?.setAttribute('aria-expanded', 'false'); nav.classList.remove('open'); }
  });
  const select = byId('download-platform');
  const button = byId('download-panel');
  const platforms = {windows:'Windows', linux:'Linux', darwin:'macOS'};
  const agent = navigator.userAgentData?.platform || navigator.platform || navigator.userAgent;
  const os = /win/i.test(agent) ? 'windows' : /mac/i.test(agent) ? 'darwin' : /linux/i.test(agent) ? 'linux' : null;
  if (select && os) select.value = os + '-amd64';
  if (byId('detected-os') && os) byId('detected-os').textContent = platforms[os].toUpperCase() + ' DETECTADO';
  let manifest = null;
  const releaseBase = 'https://github.com/yzPeedro/brassfoot-patch/releases/';
  function refreshDownload() {
    if (!select || !button) return;
    const [platform, architecture] = select.value.split('-');
    const note = byId('platform-note');
    if (note) note.textContent = platform === 'windows'
      ? 'Atualizador experimental. Instale a V4 primeiro se a sua base ainda não for compatível. Nenhum teste executado nesta edição.'
      : 'Utilitário de patch experimental. O jogo requer Wine ou outra camada de compatibilidade, instalada separadamente. Execução não homologada. Escolha a arquitetura do seu computador.';
    const item = manifest?.artifacts?.find(a => a.platform === platform && a.architecture === architecture);
    if (!item) { button.href = releaseBase + 'tag/v2026.4.0'; button.textContent = 'Ver arquivos da edição ↗'; return; }
    button.href = item.downloadUrl;
    button.textContent = 'Baixar para ' + platforms[platform] + ' ↗';
    if (byId('release-detail')) byId('release-detail').textContent = `${item.name} · ${(item.sizeBytes / 1048576).toFixed(1)} MB · ${manifest.version}`;
    if (byId('asset-hash')) byId('asset-hash').textContent = 'SHA-256: ' + item.sha256;
  }
  select?.addEventListener('change', refreshDownload);
  refreshDownload();
  if (typeof fetch !== 'function') return;
  fetch('./data/distribution.json', {cache:'no-cache'}).then(r => r.ok ? r.json() : null).then(data => {
    if (!data || !/^20\d{2}\.\d+\.\d+$/.test(data.version) || data.status !== 'published' || !Array.isArray(data.artifacts)) return;
    const prefix = releaseBase + 'download/v' + data.version + '/';
    if (data.artifacts.some(a => !/^[a-zA-Z0-9._-]+$/.test(a.name) || a.downloadUrl !== prefix + a.name ||
        !/^[a-f0-9]{64}$/.test(a.sha256) || !Number.isSafeInteger(a.sizeBytes) || a.sizeBytes <= 0)) return;
    manifest = data; refreshDownload();
  }).catch(() => {});
  fetch('./data/world-status.json', {cache:'no-cache'}).then(r => r.ok ? r.json() : null).then(data => {
    if (!data) return;
    const c = data.coverage || data.counts || data.summary || {};
    const metrics = { 'world-countries': c.countries ?? c.countriesCataloged, 'world-competitions': c.competitions ?? c.competitionsCataloged, 'world-clubs': c.clubs ?? c.clubsCataloged };
    for (const [id, count] of Object.entries(metrics)) if (byId(id) && Number.isInteger(count) && count >= 0) byId(id).textContent = count.toLocaleString('pt-BR');
    const when = data.updatedAt || data.observedAt || data.generatedAt;
    if (when && !Number.isNaN(Date.parse(when)) && byId('world-freshness')) byId('world-freshness').textContent = 'Última coleta: ' + new Date(when).toLocaleString('pt-BR', {timeZone:'America/Sao_Paulo'}) + ' (Brasília). Dados catalogados não representam novas ligas jogáveis.';
  }).catch(() => {});
})();
