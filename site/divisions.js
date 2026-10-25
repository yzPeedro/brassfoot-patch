(() => {
  'use strict';

  const root = document.getElementById('clubes-2026');
  const body = document.getElementById('clubs-grid');
  const filter = document.getElementById('clubs-division');
  const search = document.getElementById('clubs-search');
  const summary = document.getElementById('clubs-count');
  if (!root || !body || !filter || !search || !summary) return;

  const counters = [...document.querySelectorAll('[data-division-count]')];
  const normalized = value => String(value || '').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim();
  const statusLabel = status => ({
    'experimental-2026': 'Elenco 2026 experimental',
    'historical-2022-23': 'Plantel histórico 2022–23',
    'fictional-placeholder': 'Atletas fictícios'
  })[status] || 'Sem informação';

  let clubs = [];

  function render() {
    const div = filter.value;
    const query = normalized(search.value);
    const found = clubs.filter(c =>
      (!div || div === c.division) &&
      (!query || normalized([c.name, c.state, c.division, c.group || ''].join(' ')).includes(query))
    );

    const fragment = document.createDocumentFragment();
    for (const c of found) {
      const row = document.createElement('tr');
      const name = document.createElement('td');
      name.className = 'club-name';
      name.textContent = c.name;
      const state = document.createElement('td');
      state.textContent = c.state;
      const division = document.createElement('td');
      division.textContent = 'Série ' + c.division;
      const group = document.createElement('td');
      group.textContent = c.group || '—';
      const status = document.createElement('td');
      const badge = document.createElement('span');
      badge.className = 'roster-status roster-' + c.rosterStatus;
      badge.textContent = statusLabel(c.rosterStatus);
      status.append(badge);
      row.append(name, state, division, group, status);
      fragment.append(row);
    }
    body.replaceChildren(fragment);
    summary.textContent = found.length + ' de 80 clubes' +
      (div ? ' na Série ' + div : '') +
      (query ? ' encontrados' : ' na edição 2026.1.1');
  }

  fetch('./data/release-clubs-80.json', {cache: 'no-store'})
    .then(r => {if (!r.ok) throw new Error('HTTP ' + r.status); return r.json();})
    .then(payload => {
      const counts = {A:20, B:20, C:20, D:20};
      if (payload.schemaVersion !== 1 || payload.releaseVersion !== '2026.1.1' ||
          !Array.isArray(payload.clubs) || payload.clubs.length !== 80 ||
          new Set(payload.clubs.map(x => x.id)).size !== 80 ||
          Object.keys(counts).some(d =>
            payload.divisionCounts?.[d] !== 20 ||
            payload.clubs.filter(x => x.division === d).length !== 20)) {
        throw new Error('Invalid division catalog');
      }
      clubs = payload.clubs;
      for (const counter of counters) {
        counter.textContent = String(payload.divisionCounts[counter.dataset.divisionCount] ?? '—');
      }
      search.disabled = false;
      filter.disabled = false;
      search.addEventListener('input', render);
      filter.addEventListener('change', render);
      render();
    })
    .catch(() => {
      summary.textContent = 'Não foi possível carregar a lista de clubes. Recarregue a página.';
      body.replaceChildren();
    });
})();