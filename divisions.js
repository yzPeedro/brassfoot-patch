(() => {
  'use strict';

  const byId = id => document.getElementById(id);
  const elements = {
    grid: byId('clubs-grid'), search: byId('clubs-search'),
    country: byId('clubs-country'), competition: byId('clubs-competition'),
    coverage: byId('clubs-roster-filter'), sort: byId('clubs-sort'),
    summary: byId('clubs-count'), activeFilters: byId('clubs-active-filters'),
    reset: byId('clubs-reset'), retry: byId('clubs-retry'),
    pageSize: byId('clubs-page-size'), previous: byId('clubs-previous'),
    next: byId('clubs-next'), pageLabel: byId('clubs-page-label'),
    dialog: byId('club-dialog'), close: byId('club-dialog-close'),
    modalTitle: byId('club-dialog-title'), modalCompetition: byId('club-dialog-division'),
    modalDescription: byId('club-dialog-description'), modalCountry: byId('club-dialog-state'),
    modalStatus: byId('club-dialog-roster-status'), modalCount: byId('club-dialog-player-count'),
    modalRosterTitle: byId('club-dialog-roster-title'), modalNotice: byId('club-dialog-notice'),
    modalPlayers: byId('club-dialog-players'), sourceBox: byId('club-dialog-source-box'),
    sourceLink: byId('club-dialog-source'), sourceReviewed: byId('club-dialog-reviewed'),
    supplementary: byId('club-dialog-365scores')
  };
  const required = ['grid', 'search', 'country', 'competition', 'coverage', 'sort', 'summary',
    'pageSize', 'previous', 'next', 'pageLabel', 'dialog', 'close', 'modalTitle',
    'modalCompetition', 'modalDescription', 'modalCountry', 'modalStatus', 'modalCount',
    'modalRosterTitle', 'modalNotice', 'modalPlayers'];
  if (required.some(key => !elements[key])) return;

  const normalize = value => String(value ?? '').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim();
  const collator = new Intl.Collator('pt-BR', {sensitivity: 'base', numeric: true});
  const number = value => value.toLocaleString('pt-BR');
  const coverageLabels = Object.freeze({
    updated: 'Atualizado', partial: 'Parcial', preserved: 'Preservado'
  });
  const coverageOrder = Object.freeze({updated: 0, partial: 1, preserved: 2});
  const roleLabels = ['Goleiro', 'Lateral', 'Zagueiro', 'Meio-campo', 'Atacante'];
  const sortKeys = ['name', 'country', 'competition', 'coverage', 'playerCount'];
  const controls = [elements.search, elements.country, elements.competition, elements.coverage,
    elements.sort, elements.pageSize, elements.reset].filter(Boolean);
  const quickFilters = [...document.querySelectorAll('[data-country-filter], [data-coverage-filter]')];
  const table = elements.grid.closest('table');
  let catalog = null;
  let records = [];
  let recordsById = new Map();
  let loading = null;
  let page = 1;
  let sortKey = 'name';
  let sortDirection = 'asc';
  let lastFocus = null;
  let lastClubId = null;

  function textElement(tag, text, className) {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    return element;
  }

  function competitionLabel(club) {
    return club.competition.trim() || 'Competição não informada';
  }

  function safeSource(value) {
    if (typeof value !== 'string') return null;
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && url.hostname && !url.username && !url.password ? url : null;
    } catch (_) {
      return null;
    }
  }

  function validateCatalog(data) {
    if (data?.schemaVersion !== 1 || typeof data.version !== 'string' || !data.version.trim() ||
        !Array.isArray(data.countries) || !Array.isArray(data.clubs) ||
        !Number.isInteger(data.totalClubs) || data.totalClubs < 1 ||
        data.clubs.length !== data.totalClubs || !Number.isInteger(data.totalPlayers) ||
        data.totalPlayers < 0) throw new Error('Catálogo incompleto');
    const countries = new Map();
    for (const country of data.countries) {
      if (!country || !Number.isInteger(country.id) || typeof country.name !== 'string' ||
          !country.name.trim() || !Number.isInteger(country.count) || country.count < 1 ||
          countries.has(country.id)) throw new Error('País inválido');
      countries.set(country.id, {...country, actualCount: 0});
    }
    const ids = new Set();
    let totalPlayers = 0;
    for (const club of data.clubs) {
      const country = countries.get(club?.countryId);
      if (!club || typeof club.id !== 'string' || !club.id.trim() || ids.has(club.id) ||
          typeof club.name !== 'string' || !club.name.trim() || !country ||
          club.country !== country.name || typeof club.competition !== 'string' ||
          !Array.isArray(club.aliases) || club.aliases.some(alias => typeof alias !== 'string') ||
          !Object.hasOwn(coverageLabels, club.coverage) ||
          ![club.division, club.state].every(value => value === null || typeof value === 'string') ||
          !Array.isArray(club.players) || !Number.isInteger(club.playerCount) ||
          club.playerCount !== club.players.length || typeof club.teamFile !== 'string' ||
          ![club.sourceUrl, club.observedAt].every(value => value === null || typeof value === 'string')) {
        throw new Error('Clube inválido');
      }
      for (const player of club.players) {
        if (!player || typeof player.name !== 'string' || !player.name.trim() ||
            !Number.isInteger(player.position) || player.position < 0 || player.position > 4 ||
            !['Direito', 'Esquerdo'].includes(player.side) || !Array.isArray(player.traits) ||
            player.traits.length !== 2 || player.traits.some(trait => typeof trait !== 'string')) {
          throw new Error('Jogador inválido');
        }
      }
      ids.add(club.id);
      country.actualCount++;
      totalPlayers += club.playerCount;
    }
    if (totalPlayers !== data.totalPlayers || [...countries.values()].some(c => c.count !== c.actualCount)) {
      throw new Error('Contagem do catálogo inconsistente');
    }
    return data;
  }

  function indexCatalog(data) {
    records = data.clubs.map(club => {
      const metadata = normalize([club.name, ...club.aliases, club.country, club.competition,
        club.division, club.state].join(' '));
      const players = club.players.map(player => normalize(player.name));
      return {club, metadata, players, searchText: metadata + ' ' + players.join(' ')};
    });
    recordsById = new Map(records.map(record => [record.club.id, record]));
  }

  function populateCountries() {
    const fragment = document.createDocumentFragment();
    const all = textElement('option', 'Todos os países');
    all.value = '';
    fragment.appendChild(all);
    for (const country of [...catalog.countries].sort((a, b) => collator.compare(a.name, b.name))) {
      const option = textElement('option', country.name + ' (' + number(country.count) + ')');
      option.value = String(country.id);
      fragment.appendChild(option);
    }
    elements.country.replaceChildren(fragment);
  }

  function populateCompetitions() {
    const selected = elements.competition.value;
    const countryId = elements.country.value;
    const values = new Map();
    for (const {club} of records) {
      if (countryId && String(club.countryId) !== countryId) continue;
      values.set(club.competition, competitionLabel(club));
    }
    const fragment = document.createDocumentFragment();
    const all = textElement('option', 'Todas as competições');
    all.value = '';
    fragment.appendChild(all);
    // The empty value belongs to the all-competitions option; unknown competitions
    // remain visible in results without being presented as a named competition.
    for (const [value, label] of [...values].filter(([value]) => value !== '')
      .sort((a, b) => collator.compare(a[1], b[1]))) {
      const option = textElement('option', label);
      option.value = value;
      fragment.appendChild(option);
    }
    elements.competition.replaceChildren(fragment);
    if (selected && values.has(selected)) elements.competition.value = selected;
  }

  function searchTokens() {
    return normalize(elements.search.value).split(/\s+/).filter(Boolean);
  }

  function matchingPlayers(record, tokens) {
    if (!tokens.length) return [];
    const playerTerms = tokens.filter(token => !record.metadata.includes(token));
    if (!playerTerms.length) return [];
    return record.club.players.filter((_, index) => playerTerms.every(token => record.players[index].includes(token)));
  }

  function compareRecords(a, b) {
    const left = a.club;
    const right = b.club;
    let result;
    if (sortKey === 'playerCount') result = left.playerCount - right.playerCount;
    else if (sortKey === 'coverage') result = coverageOrder[left.coverage] - coverageOrder[right.coverage];
    else result = collator.compare(sortKey === 'competition' ? competitionLabel(left) : left[sortKey],
      sortKey === 'competition' ? competitionLabel(right) : right[sortKey]);
    return result * (sortDirection === 'desc' ? -1 : 1) ||
      collator.compare(left.name, right.name) || collator.compare(left.country, right.country) ||
      collator.compare(left.id, right.id);
  }

  function badge(club) {
    const element = textElement('span', coverageLabels[club.coverage], 'coverage-badge roster-badge');
    element.dataset.coverage = club.coverage;
    return element;
  }

  function updateSortLabels() {
    for (const heading of table?.querySelectorAll('thead th') || []) {
      const key = heading.dataset.sort || heading.querySelector('[data-sort]')?.dataset.sort ||
        heading.id.replace('clubs-heading-', '');
      if (!sortKeys.includes(key)) continue;
      const active = key === sortKey;
      heading.setAttribute('aria-sort', active ? (sortDirection === 'desc' ? 'descending' : 'ascending') : 'none');
      const indicator = heading.querySelector('.sort-indicator');
      if (indicator) indicator.textContent = active ? (sortDirection === 'desc' ? '↓' : '↑') : '↕';
    }
  }

  function renderActiveFilters() {
    const parts = [];
    if (elements.search.value.trim()) parts.push('Busca: ' + elements.search.value.trim());
    if (elements.country.value) {
      parts.push('País: ' + catalog.countries.find(c => String(c.id) === elements.country.value)?.name);
    }
    if (elements.competition.value) parts.push('Competição: ' + elements.competition.value);
    if (elements.coverage.value) parts.push('Elenco: ' + coverageLabels[elements.coverage.value]);
    if (elements.activeFilters) elements.activeFilters.textContent = parts.length ? parts.join(' · ') : 'Todos os clubes do pacote';
    if (elements.reset) elements.reset.disabled = !parts.length;
    for (const button of quickFilters) {
      const country = button.dataset.countryFilter;
      const active = country !== undefined ? catalog.countries.some(c =>
        String(c.id) === elements.country.value && (String(c.id) === country || normalize(c.name) === normalize(country)))
        : elements.coverage.value === button.dataset.coverageFilter;
      button.setAttribute('aria-pressed', String(active));
    }
  }

  function statusRow(message) {
    const row = document.createElement('tr');
    const cell = textElement('td', message, 'clubs-empty');
    cell.colSpan = 6;
    row.appendChild(cell);
    elements.grid.replaceChildren(row);
  }

  function render() {
    if (!catalog) return;
    const tokens = searchTokens();
    const country = elements.country.value;
    const competition = elements.competition.value;
    const coverage = elements.coverage.value;
    const filtered = records.filter(record => {
      const {club, searchText, metadata, players} = record;
      if ((country && String(club.countryId) !== country) ||
          (competition && club.competition !== competition) ||
          (coverage && club.coverage !== coverage) || !tokens.every(token => searchText.includes(token))) return false;
      const playerTerms = tokens.filter(token => !metadata.includes(token));
      return !playerTerms.length || players.some(name => playerTerms.every(token => name.includes(token)));
    }).sort(compareRecords);
    const selectedSize = Number(elements.pageSize.value);
    const size = [25, 50, 100].includes(selectedSize) ? selectedSize : 25;
    const pages = Math.max(1, Math.ceil(filtered.length / size));
    page = Math.max(1, Math.min(page, pages));
    const start = (page - 1) * size;
    const visible = filtered.slice(start, start + size);
    const fragment = document.createDocumentFragment();
    for (const record of visible) {
      const {club} = record;
      const row = document.createElement('tr');
      row.className = 'club-clickable-row';
      row.dataset.clubId = club.id;
      const nameCell = textElement('td', '', 'club-name');
      nameCell.appendChild(textElement('strong', club.name));
      const found = matchingPlayers(record, tokens);
      if (found.length) {
        row.classList.add('club-search-match');
        const names = found.slice(0, 2).map(player => player.name).join(', ');
        nameCell.appendChild(textElement('small', 'Jogador: ' + names + (found.length > 2 ? ' +' + (found.length - 2) : ''), 'club-search-context'));
      }
      row.appendChild(nameCell);
      row.appendChild(textElement('td', club.country, 'club-country'));
      row.appendChild(textElement('td', competitionLabel(club), 'club-competition'));
      const status = textElement('td', '', 'club-roster-state');
      status.appendChild(badge(club));
      row.appendChild(status);
      row.appendChild(textElement('td', number(club.playerCount), 'club-player-count'));
      const action = document.createElement('td');
      const button = textElement('button', 'Ver elenco', 'club-row-button club-detail-trigger');
      button.type = 'button';
      button.dataset.clubId = club.id;
      button.setAttribute('aria-label', 'Ver elenco de ' + club.name + ', ' + club.country);
      action.appendChild(button);
      row.appendChild(action);
      fragment.appendChild(row);
    }
    elements.grid.replaceChildren(fragment);
    if (!visible.length) statusRow('Nenhum clube encontrado. Altere a busca ou limpe os filtros.');
    const from = filtered.length ? start + 1 : 0;
    const to = filtered.length ? start + visible.length : 0;
    elements.summary.textContent = number(filtered.length) + ' clubes encontrados · exibindo ' + number(from) + '–' + number(to) +
      ' de ' + number(catalog.totalClubs) + ' no pacote';
    elements.pageLabel.textContent = 'Página ' + page + ' de ' + pages;
    elements.previous.disabled = page <= 1;
    elements.next.disabled = page >= pages;
    renderActiveFilters();
    updateSortLabels();
  }

  function resetPage() {
    page = 1;
    render();
  }

  function observedDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}(?:T|$)/.test(value)) return '';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? '' : new Intl.DateTimeFormat('pt-BR', {timeZone: 'UTC'}).format(date);
  }

  function openClub(record) {
    const {club} = record;
    lastFocus = document.activeElement;
    lastClubId = club.id;
    elements.modalTitle.textContent = club.name;
    elements.modalCompetition.textContent = competitionLabel(club) + ' · versão ' + catalog.version;
    elements.modalCountry.textContent = club.country;
    elements.modalStatus.replaceChildren(badge(club));
    elements.modalCount.textContent = number(club.playerCount);
    elements.modalDescription.textContent = 'Elenco incluído no pacote publicado. ' +
      (club.division ? 'Divisão: ' + club.division + '. ' : '') + (club.state ? 'Estado: ' + club.state + '.' : '');
    elements.modalRosterTitle.textContent = 'Jogadores do pacote';
    const notices = {
      updated: 'Elenco substituído na atualização. As características do jogo podem incluir valores derivados da função do atleta.',
      partial: 'Atualização parcial: o elenco anterior foi preservado com correções pontuais. A fonte não confirmou um elenco completo.',
      preserved: 'Elenco anterior preservado nesta versão. A presença no pacote não indica atualização completa para 2026.'
    };
    elements.modalNotice.textContent = notices[club.coverage] + ' Lado indica a posição de atuação no jogo.';
    const source = safeSource(club.sourceUrl);
    if (elements.sourceBox) elements.sourceBox.hidden = !source;
    if (elements.sourceLink) {
      elements.sourceLink.removeAttribute('href');
      elements.sourceLink.textContent = '';
      if (source) {
        elements.sourceLink.href = source.href;
        elements.sourceLink.textContent = source.hostname + ' ↗';
        elements.sourceLink.target = '_blank';
        elements.sourceLink.rel = 'noopener noreferrer';
      }
    }
    if (elements.sourceReviewed) {
      const date = observedDate(club.observedAt);
      elements.sourceReviewed.textContent = source ? (date ? '· consultada em ' + date : '· data da consulta não informada') : '';
    }
    if (elements.supplementary) {
      elements.supplementary.hidden = true;
      elements.supplementary.removeAttribute('href');
    }
    const matched = new Set(matchingPlayers(record, searchTokens()));
    const fragment = document.createDocumentFragment();
    for (const player of club.players) {
      const item = document.createElement('li');
      item.className = 'club-player-row';
      const name = textElement(matched.has(player) ? 'mark' : 'strong', player.name, 'club-player-name');
      item.appendChild(name);
      const traits = player.traits.filter(trait => trait.trim());
      item.appendChild(textElement('span', roleLabels[player.position] + ' · Lado ' + player.side.toLocaleLowerCase('pt-BR'), 'club-player-role'));
      item.appendChild(textElement('span', 'Características: ' + (traits.length ? traits.join(' / ') : 'não informadas'), 'club-player-traits'));
      fragment.appendChild(item);
    }
    if (!club.players.length) fragment.appendChild(textElement('li', 'Nenhum jogador registrado neste pacote.'));
    elements.modalPlayers.replaceChildren(fragment);
    if (!elements.dialog.open) elements.dialog.showModal();
    elements.dialog.scrollTop = 0;
    elements.close.focus();
  }

  function setLoading(isLoading) {
    controls.forEach(control => {control.disabled = isLoading;});
    quickFilters.forEach(button => {button.disabled = isLoading;});
    if (table) table.setAttribute('aria-busy', String(isLoading));
    if (elements.retry) elements.retry.hidden = true;
  }

  async function loadCatalog() {
    if (catalog || loading) return loading;
    setLoading(true);
    elements.summary.textContent = 'Carregando os clubes e jogadores do pacote…';
    elements.pageLabel.textContent = 'Carregando…';
    elements.previous.disabled = true;
    elements.next.disabled = true;
    statusRow('Carregando o catálogo…');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 25000);
    loading = (async () => {
      try {
        const response = await fetch('./data/patch-clubs.json', {signal: controller.signal});
        if (!response.ok) throw new Error('Catálogo indisponível');
        const data = validateCatalog(await response.json());
        indexCatalog(data);
        catalog = data;
        populateCountries();
        populateCompetitions();
        setLoading(false);
        render();
      } catch (_) {
        catalog = null;
        records = [];
        recordsById.clear();
        if (table) table.setAttribute('aria-busy', 'false');
        elements.summary.textContent = 'Não foi possível carregar o catálogo de clubes.';
        elements.pageLabel.textContent = 'Catálogo indisponível';
        statusRow('Falha ao carregar os dados. Use “Tentar novamente” para recarregar o catálogo.');
        if (elements.retry) elements.retry.hidden = false;
      } finally {
        clearTimeout(timeout);
        loading = null;
      }
    })();
    return loading;
  }

  elements.search.addEventListener('input', resetPage);
  elements.country.addEventListener('change', () => {populateCompetitions(); resetPage();});
  elements.competition.addEventListener('change', resetPage);
  elements.coverage.addEventListener('change', resetPage);
  elements.pageSize.addEventListener('change', resetPage);
  elements.sort.addEventListener('change', () => {
    sortKey = sortKeys.includes(elements.sort.value) ? elements.sort.value : 'name';
    sortDirection = sortKey === 'playerCount' ? 'desc' : 'asc';
    resetPage();
  });
  for (const button of table?.querySelectorAll('button[data-sort]') || []) {
    button.addEventListener('click', () => {
      const key = button.dataset.sort;
      if (!sortKeys.includes(key)) return;
      sortDirection = key === sortKey ? (sortDirection === 'asc' ? 'desc' : 'asc') : key === 'playerCount' ? 'desc' : 'asc';
      sortKey = key;
      elements.sort.value = key;
      resetPage();
    });
  }
  elements.previous.addEventListener('click', () => {if (page > 1) {page--; render();}});
  elements.next.addEventListener('click', () => {page++; render();});
  if (elements.reset) elements.reset.addEventListener('click', () => {
    elements.search.value = '';
    elements.country.value = '';
    elements.competition.value = '';
    elements.coverage.value = '';
    populateCompetitions();
    resetPage();
    elements.search.focus();
  });
  if (elements.retry) elements.retry.addEventListener('click', loadCatalog);
  for (const button of quickFilters) button.addEventListener('click', () => {
    if (!catalog) return;
    if (button.dataset.countryFilter !== undefined) {
      const value = button.dataset.countryFilter;
      const country = catalog.countries.find(country => String(country.id) === value || normalize(country.name) === normalize(value));
      if (!country) return;
      elements.country.value = String(country.id);
      elements.competition.value = '';
      populateCompetitions();
    }
    if (Object.hasOwn(coverageLabels, button.dataset.coverageFilter)) elements.coverage.value = button.dataset.coverageFilter;
    resetPage();
  });
  elements.grid.addEventListener('click', event => {
    const row = event.target.closest('tr[data-club-id]');
    if (!row || !elements.grid.contains(row) || window.getSelection()?.toString()) return;
    const record = recordsById.get(row.dataset.clubId);
    if (record) {
      // A mouse click on a cell is represented by the row's keyboard-accessible button.
      if (!event.target.closest('button')) row.querySelector('button')?.focus();
      openClub(record);
    }
  });
  elements.close.addEventListener('click', () => elements.dialog.close());
  elements.dialog.addEventListener('click', event => {
    if (event.target !== elements.dialog) return;
    const bounds = elements.dialog.getBoundingClientRect();
    if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) {
      elements.dialog.close();
    }
  });
  // Native <dialog> handles Escape and focus containment; close covers every exit path.
  elements.dialog.addEventListener('close', () => {
    const fallback = [...elements.grid.querySelectorAll('button[data-club-id]')]
      .find(button => button.dataset.clubId === lastClubId);
    const target = lastFocus?.isConnected ? lastFocus : fallback || elements.search;
    target?.focus();
    lastFocus = null;
    lastClubId = null;
  });
  loadCatalog();
})();
