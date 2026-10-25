(() => {
  'use strict';

  const byId = id => document.getElementById(id);
  const elements = {
    grid: byId('clubs-grid'),
    division: byId('clubs-division'),
    search: byId('clubs-search'),
    rosterFilter: byId('clubs-roster-filter'),
    summary: byId('clubs-count'),
    pageSize: byId('clubs-page-size'),
    previous: byId('clubs-previous'),
    next: byId('clubs-next'),
    pageLabel: byId('clubs-page-label'),
    dialog: byId('club-dialog'),
    close: byId('club-dialog-close'),
    modalTitle: byId('club-dialog-title'),
    modalDivision: byId('club-dialog-division'),
    modalDescription: byId('club-dialog-description'),
    modalState: byId('club-dialog-state'),
    modalStatus: byId('club-dialog-roster-status'),
    modalCount: byId('club-dialog-player-count'),
    modalRosterTitle: byId('club-dialog-roster-title'),
    modalNotice: byId('club-dialog-notice'),
    modalPlayers: byId('club-dialog-players')
  };
  if (Object.values(elements).some(x => !x)) return;

  const normalized = input => String(input ?? '').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim();

  const collator = new Intl.Collator('pt-BR', {sensitivity:'base', numeric:true});
  const labels = {
    A: 'Prévia publicada (2026.0.2)',
    B: 'Aguardando elenco 2026',
    C: 'Aguardando elenco 2026'
  };

  let clubs = [];
  let rosters = {};
  let rostersReady = false;
  let page = 1;
  let lastFocus = null;

  async function getJson(relativePath) {
    const response = await fetch(relativePath, {cache:'no-store'});
    if (!response.ok) throw new Error('HTTP ' + response.status + ' em ' + relativePath);
    return response.json();
  }

  function validateCatalog(data) {
    const counts = {A:20, B:20, C:20};
    if (data?.schemaVersion !== 1 || data.targetClubs !== 60 ||
        data.serieD?.policy !== 'untouched' || !Array.isArray(data.clubs) ||
        data.clubs.length !== 60 ||
        new Set(data.clubs.map(c => c.id)).size !== 60 ||
        data.clubs.some(c => !c.id || typeof c.name !== 'string' ||
          typeof c.state !== 'string' || !counts[c.division]) ||
        Object.entries(counts).some(([d,n]) =>
          data.clubs.filter(c => c.division === d).length !== n)) {
      throw new Error('Catálogo A/B/C inconsistente');
    }
  }

  function validatePublishedRosters(data) {
    if (data?.schemaVersion !== 1 || data.sourceRelease !== '2026.0.2' ||
        data.totalClubs !== 20 || data.totalPlayers !== 730 ||
        !data.clubs || Object.keys(data.clubs).length !== 20) {
      throw new Error('Dados dos jogadores publicados incompletos');
    }
    const publishedIds = new Set(clubs.filter(c => c.division === 'A').map(c => c.id));
    if (Object.keys(data.clubs).some(id => !publishedIds.has(id)) ||
        [...publishedIds].some(id => !Object.hasOwn(data.clubs, id))) {
      throw new Error('Elencos atribuídos a clubes incorretos');
    }
    let count = 0;
    for (const club of Object.values(data.clubs)) {
      if (!/^teams\/[a-z0-9_-]+\.ban$/.test(club.teamFile) ||
          !Array.isArray(club.players) || club.players.length < 16 ||
          club.players.length > 40 ||
          club.players.some(name => typeof name !== 'string' || !name.trim())) {
        throw new Error('Lista de jogadores inválida');
      }
      count += club.players.length;
    }
    if (count !== 730) throw new Error('Quantidade de jogadores não confere com a release');
    return data.clubs;
  }

  function matchingClubs() {
    const searched = normalized(elements.search.value);
    const chosenDivision = elements.division.value;
    const chosenRoster = elements.rosterFilter.value;
    return clubs.filter(club => {
      if (chosenDivision && club.division !== chosenDivision) return false;
      if (chosenRoster === 'published' && club.division !== 'A') return false;
      if (chosenRoster === 'pending' && club.division === 'A') return false;
      return !searched || normalized([club.name, club.state, 'Série ' + club.division].join(' ')).includes(searched);
    });
  }

  function render() {
    const filtered = matchingClubs();
    const size = Number(elements.pageSize.value);
    const totalPages = Math.max(1, Math.ceil(filtered.length / size));
    page = Math.max(1, Math.min(page, totalPages));
    const start = (page - 1) * size;
    const visible = filtered.slice(start, start + size);
    const fragment = document.createDocumentFragment();

    for (const club of visible) {
      const row = document.createElement('tr');
      row.dataset.clubId = club.id;
      row.className = 'club-clickable-row';
      const nameCell = document.createElement('td');
      nameCell.className = 'club-name';
      const trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = 'club-detail-trigger';
      trigger.dataset.clubId = club.id;
      trigger.setAttribute('aria-label', 'Ver clube ' + club.name + ', ' + club.state + ', Série ' + club.division);
      trigger.textContent = club.name;
      nameCell.appendChild(trigger);
      row.appendChild(nameCell);
      for (const [cellValue, cellClass] of [
        [club.state, ''], ['Série ' + club.division, ''],
        [labels[club.division], 'club-roster-state']
      ]) {
        const td = document.createElement('td');
        if (cellClass) td.className = cellClass;
        td.textContent = cellValue;
        row.appendChild(td);
      }
      fragment.appendChild(row);
    }

    if (!visible.length) {
      const row = document.createElement('tr');
      const cell = document.createElement('td');
      cell.colSpan = 4;
      cell.className = 'clubs-empty';
      cell.textContent = 'Nenhum clube encontrado. Experimente outro nome, UF ou divisão.';
      row.appendChild(cell);
      fragment.appendChild(row);
    }

    elements.grid.replaceChildren(fragment);
    const from = filtered.length ? start + 1 : 0;
    const to = filtered.length ? start + visible.length : 0;
    elements.summary.textContent = 'Exibindo ' + from + '–' + to +
      ' de ' + filtered.length + ' clubes encontrados (60 no total)';
    elements.pageLabel.textContent = 'Página ' + page + ' de ' + totalPages;
    elements.previous.disabled = page <= 1;
    elements.next.disabled = page >= totalPages;
  }

  function clearPageAndRender() {
    page = 1;
    render();
  }

  function openClub(club) {
    lastFocus = document.activeElement;
    const published = club.division === 'A';
    const roster = rostersReady ? rosters[club.id] : undefined;
    elements.modalTitle.textContent = club.name;
    elements.modalDivision.textContent = 'Série ' + club.division + ' · Temporada 2026';
    elements.modalDescription.textContent = published
      ? 'Nomes dos jogadores efetivamente incluídos na prévia v2026.0.2.'
      : 'Elenco atualizado de 2026 ainda não publicado para este clube.';
    elements.modalState.textContent = club.state;
    elements.modalStatus.textContent = labels[club.division];
    elements.modalCount.textContent = roster ? String(roster.players.length) : '—';
    elements.modalRosterTitle.textContent = published ? 'Jogadores no patch v2026.0.2' : 'Elenco de 2026';
    const fragment = document.createDocumentFragment();
    if (roster) {
      elements.modalNotice.textContent =
        'Lista conferida diretamente nos arquivos .ban distribuídos na v2026.0.2. Alguns atributos são estimados; não representa necessariamente o plantel atual do clube.';
      for (const name of roster.players) {
        const item = document.createElement('li');
        item.textContent = name;
        fragment.appendChild(item);
      }
    } else if (published && !rostersReady) {
      elements.modalNotice.textContent =
        'Não foi possível carregar a lista de jogadores do patch. Tente recarregar a página.';
    } else {
      elements.modalNotice.textContent =
        'Nenhum elenco real de 2026 foi publicado para este clube nas Séries B/C. A lista aparecerá depois da coleta, da conferência e da integração ao patch; não exibimos jogadores fictícios.';
    }
    elements.modalPlayers.replaceChildren(fragment);
    elements.dialog.showModal();
    elements.close.focus();
  }

  elements.grid.addEventListener('click', event => {
    const row = event.target.closest('tr[data-club-id]');
    if (!row) return;
    const club = clubs.find(c => c.id === row.dataset.clubId);
    if (club) openClub(club);
  });
  elements.dialog.addEventListener('click', event => {
    if (event.target === elements.dialog) elements.dialog.close();
  });
  elements.close.addEventListener('click', () => elements.dialog.close());
  elements.dialog.addEventListener('close', () => {
    if (lastFocus && lastFocus.isConnected && typeof lastFocus.focus === 'function') lastFocus.focus();
    lastFocus = null;
  });
  elements.previous.addEventListener('click', () => {if (page > 1) {page--;render();}});
  elements.next.addEventListener('click', () => {page++;render();});
  elements.pageSize.addEventListener('change', clearPageAndRender);
  elements.division.addEventListener('change', clearPageAndRender);
  elements.rosterFilter.addEventListener('change', clearPageAndRender);
  elements.search.addEventListener('input', clearPageAndRender);

  getJson('./data/target-abc-2026.json')
    .then(data => {
      validateCatalog(data);
      clubs = data.clubs.sort((a,b) =>
        'ABC'.indexOf(a.division) - 'ABC'.indexOf(b.division) ||
        collator.compare(a.name,b.name) || collator.compare(a.state,b.state));
      for (const counter of document.querySelectorAll('[data-division-count]')) {
        counter.textContent = String(data.clubs.filter(c => c.division === counter.dataset.divisionCount).length);
      }
      for (const field of [elements.division,elements.search,elements.rosterFilter,elements.pageSize]) {
        field.disabled = false;
      }
      render();
      return getJson('./data/published-rosters-2026-0-2.json')
        .then(published => {
          rosters = validatePublishedRosters(published);
          rostersReady = true;
        })
        .catch(error => {
          console.warn('Detalhes de elencos indisponíveis:',error.message);
        });
    })
    .catch(error => {
      elements.summary.textContent = 'Falha ao carregar a listagem. Atualize a página.';
      elements.pageLabel.textContent = 'Indisponível';
      console.warn('Não foi possível validar o catálogo:',error.message);
    });
})();
