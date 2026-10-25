(() => {
  'use strict';
  const root = document.getElementById('clubs-2026');
  if (!root) return;
  const grid = document.getElementById('clubs-grid');
  const filter = document.getElementById('clubs-division');
  const search = document.getElementById('clubs-search');
  const summary = document.getElementById('clubs-count');
  const counters = [...document.querySelectorAll('[data-division-count]')];
  let clubs = [];

  const normalized = (value) => String(value).normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');

  function render() {
    const term = normalized(search.value.trim());
    const division = filter.value;
    const visible = clubs.filter(club =>
      (!division || club.division === division) &&
      (!term || normalized(club.name + ' ' + club.state).includes(term)));
    const fragment = document.createDocumentFragment();
    for (const club of visible) {
      const item = document.createElement('article');
      item.className = 'club-entry';
      const heading = document.createElement('strong');
      heading.textContent = club.name;
      const detail = document.createElement('span');
      detail.textContent = 'Série ' + club.division + ' · ' + club.state +
        (club.group ? ' · Grupo ' + club.group : '');
      const phase = document.createElement('small');
      phase.textContent = club.gameIntegration === 'release-v2026.0.2-roster-only'
        ? 'Elenco experimental na v2026.0.2'
        : 'Catálogo oficial · não instalado no patch atual';
      item.append(heading, detail, phase);
      fragment.append(item);
    }
    grid.replaceChildren(fragment);
    summary.textContent = visible.length + ' de ' + clubs.length +
      ' clubes no catálogo da CBF';
  }

  fetch('./data/competitions/2026-brazil.json', { cache: 'no-cache' })
    .then(response => {
      if (!response.ok) throw new Error('Catálogo indisponível');
      return response.json();
    })
    .then(data => {
      const expected = { A: 20, B: 20, C: 20, D: 96 };
      if (data.season !== 2026 || data.catalogStatus !== '2026-participants-verified' ||
          !Array.isArray(data.clubs) || data.clubs.length !== 156 ||
          new Set(data.clubs.map(x => x.id)).size !== 156 ||
          Object.keys(expected).some(key =>
            data.counts?.[key] !== expected[key] ||
            data.clubs.filter(x => x.division === key).length !== expected[key])) {
        throw new Error('Catálogo inconsistente');
      }
      clubs = data.clubs;
      for (const counter of counters) {
        const kind = counter.dataset.divisionCount;
        counter.textContent = String(data.counts[kind] ?? '—');
      }
      filter.disabled = false;
      search.disabled = false;
      filter.addEventListener('change', render);
      search.addEventListener('input', render);
      render();
    })
    .catch(() => {
      summary.textContent = 'Não foi possível confirmar a lista oficial. Tente novamente mais tarde.';
      grid.replaceChildren();
    });
})();
