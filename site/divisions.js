(() => {
  'use strict';

  const byId = id => document.getElementById(id);
  const elements = {
    grid: byId('clubs-grid'),
    division: byId('clubs-division'),
    search: byId('clubs-search'),
    rosterFilter: byId('clubs-roster-filter'),
    groupBy: byId('clubs-group-by'),
    sortButtons: ['name','state','division','roster'].map(k => byId('clubs-sort-' + k)),
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
    modalPlayers: byId('club-dialog-players'),
    sourceBox: byId('club-dialog-source-box'),
    sourceLink: byId('club-dialog-source'),
    sourceReviewed: byId('club-dialog-reviewed')
  };
  if (Object.values(elements).some(x => !x || (Array.isArray(x) && x.some(i => !i)))) return;

  const normalized = input => String(input ?? '').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim();

  const collator = new Intl.Collator('pt-BR', {sensitivity:'base', numeric:true});
  const labels = {
    A: 'Série A 2026 · elenco original ou v2026.0.2',
    B: 'Série B 2026 · elenco histórico',
    C: 'Série C 2026 · elenco histórico (Maranhão experimental)'
  };

  let clubs = [];
  let rosters = {};
  let researchedRosters = {};
  let rostersReady = false;
  let fullRostersReady = false;
  let fullRosterVersion = "";
  let page = 1;
  let sortKey = 'name';
  let sortDirection = 'asc';
  let lastFocus = null;
  function rosterStatus(club) {
    if (fullRostersReady && Object.hasOwn(rosters,club.id)) return 'Elenco 2026 publicado · v' + fullRosterVersion;
    if (club.division === 'A') return labels.A;
    if (Object.hasOwn(researchedRosters,club.id)) return 'Pesquisa externa · não instalado';
    return 'Elenco aguardando pesquisa completa';
  }
  function validateResearch(data) {
    const known = new Set(clubs.filter(c => c.division !== 'A').map(c => c.id));
    if (data?.schemaVersion !== 1 || data.season !== 2026 || !data.clubs ||
        !Number.isInteger(data.researchedClubs) ||
        Object.keys(data.clubs).length !== data.researchedClubs) throw new Error('Metadados externos inválidos');
    for (const [id,entry] of Object.entries(data.clubs)) {
      if (!known.has(id) || entry.scope !== 'internet-research-not-installed' ||
          entry.completeSeason2026Verified !== false ||
          !/^https:\/\//.test(entry.sourceUrl) || !Array.isArray(entry.players) ||
          entry.players.length < 16 || entry.players.length > 60 ||
          entry.players.some(x => typeof x !== 'string' || !x.trim()) ||
          (entry.positionCodes !== undefined && (
            !Array.isArray(entry.positionCodes) ||
            entry.positionCodes.length !== entry.players.length ||
            entry.positionCodes.some(value => !Number.isInteger(value) || value < 0 || value > 4)))) {
        throw new Error('Pesquisa externa inválida: ' + id);
      }
    }
    return data.clubs;
  }

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

  function validateFullPublishedRosters(data, expectedVersion) {
    if (data?.schemaVersion !== 2 || data.season !== 2026 || data.sourceRelease !== expectedVersion ||
        data.totalClubs !== 60 || data.rostersBCVerified !== 40 || data.allRostersVerified !== true ||
        !data.clubs || Object.keys(data.clubs).length !== 60) {
      throw new Error('Release de elencos A/B/C incompleta');
    }
    let total = 0;
    for (const club of clubs) {
      const roster = data.clubs[club.id];
      if (!roster || roster.division !== club.division || !/^teams\/[a-z0-9_-]+\.ban$/i.test(roster.teamFile) ||
          roster.verified2026 !== true || !/^https:\/\//.test(roster.sourceUrl) ||
          !Array.isArray(roster.players) || roster.players.length < 16 || roster.players.length > 40 ||
          !Array.isArray(roster.positionCodes) || roster.positionCodes.length !== roster.players.length ||
          roster.players.some(name => typeof name !== 'string' || !name.trim()) ||
          roster.positionCodes.some(n => !Number.isInteger(n) || n < 0 || n > 4)) {
        throw new Error('Elenco da release não confere: ' + club.id);
      }
      total += roster.players.length;
    }
    if (total !== data.totalPlayers) throw new Error('Quantidade de jogadores da release diverge');
    return data.clubs;
  }

  function matchingClubs() {
    const searched = normalized(elements.search.value);
    const chosenDivision = elements.division.value;
    const chosenRoster = elements.rosterFilter.value;
    return clubs.filter(club => {
      if (chosenDivision && club.division !== chosenDivision) return false;
      const isPublished = fullRostersReady ? Object.hasOwn(rosters,club.id) : club.division === 'A';
      if (chosenRoster === 'published' && !isPublished) return false;
      if (chosenRoster === 'pending' && isPublished) return false;
      if (chosenRoster === 'researched' && (fullRostersReady || !Object.hasOwn(researchedRosters,club.id))) return false;
      if (chosenRoster === 'missing' && (isPublished || Object.hasOwn(researchedRosters,club.id))) return false;
      return !searched || normalized([club.name, club.state, 'Série ' + club.division].join(' ')).includes(searched);
    });
  }

  const sortValues = {
    name: club => club.name,
    state: club => club.state,
    division: club => club.division,
    roster: club => rosterStatus(club)
  };
  const grouping = {
    none: () => '',
    name: club => normalized(club.name).charAt(0).toLocaleUpperCase('pt-BR') || '#',
    state: club => club.state,
    division: club => 'Série ' + club.division,
    roster: club => rosterStatus(club)
  };

  function compare(a,b,key) {
    return collator.compare(sortValues[key](a),sortValues[key](b));
  }

  function order(items) {
    const mode = elements.groupBy.value;
    const group = grouping[mode] || grouping.none;
    return items.sort((a,b) => {
      const groupCompare = mode !== 'none' ? collator.compare(group(a),group(b)) : 0;
      if (groupCompare) return groupCompare;
      return (sortDirection === 'desc' ? -1 : 1) * compare(a,b,sortKey) ||
        compare(a,b,'name') || compare(a,b,'state') || collator.compare(a.id,b.id);
    });
  }

  function updateSortLabels() {
    for (const key of Object.keys(sortValues)) {
      const heading = byId('clubs-heading-' + key);
      const button = byId('clubs-sort-' + key);
      const active = key === sortKey;
      heading.setAttribute('aria-sort', active ? (sortDirection === 'asc' ? 'ascending' : 'descending') : 'none');
      const indicator = button.querySelector('.sort-indicator');
      if (indicator) indicator.textContent = active ? (sortDirection === 'asc' ? '↑' : '↓') : '↕';
    }
  }

  function render() {
    const filtered = order(matchingClubs());
    const size = Number(elements.pageSize.value);
    const totalPages = Math.max(1, Math.ceil(filtered.length / size));
    page = Math.max(1, Math.min(page, totalPages));
    const start = (page - 1) * size;
    const visible = filtered.slice(start, start + size);
    const fragment = document.createDocumentFragment();
    const groupMode = elements.groupBy.value;
    const groupOf = grouping[groupMode] || grouping.none;
    const groupCounts = new Map();
    if (groupMode !== 'none') {
      for (const club of filtered) {
        const value = groupOf(club);
        groupCounts.set(value,(groupCounts.get(value) || 0) + 1);
      }
    }
    let previousGroup = null;
    for (const club of visible) {
      if (groupMode !== 'none') {
        const group = groupOf(club);
        if (group !== previousGroup) {
          const tr = document.createElement('tr');
          tr.className = 'clubs-group-header';
          const cell = document.createElement('th');
          cell.scope = 'rowgroup';
          cell.colSpan = 4;
          cell.textContent = group + ' · ' + groupCounts.get(group) + ' clube(s) no filtro';
          tr.appendChild(cell);
          fragment.appendChild(tr);
          previousGroup = group;
        }
      }
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
        [rosterStatus(club), 'club-roster-state']
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
    updateSortLabels();
  }

  function clearPageAndRender() {
    page = 1;
    render();
  }

  function openClub(club) {
    lastFocus = document.activeElement;
    const verified = fullRostersReady && Object.hasOwn(rosters,club.id);
    const published = verified || club.division === 'A';
    const external = published ? undefined : researchedRosters[club.id];
    const roster = published ? (rostersReady ? rosters[club.id] : undefined) : external;
    elements.modalTitle.textContent = club.name;
    elements.modalDivision.textContent = 'Série ' + club.division + ' · Temporada 2026';
    elements.modalDescription.textContent = verified
      ? 'Jogadores de 2026 incluídos na versão ' + fullRosterVersion + ' do patch.'
      : published ? 'Jogadores da v2026.0.2: presentes apenas em instalações onde esse patch já foi aplicado.'
      : (external ? 'Jogadores de fonte externa pesquisada; ainda NÃO estão no patch.' : 'Elenco atualizado de 2026 ainda não publicado para este clube.');
    elements.modalState.textContent = club.state;
    elements.modalStatus.textContent = rosterStatus(club);
    elements.modalCount.textContent = roster ? String(roster.players.length) : '—';
    elements.modalRosterTitle.textContent = verified ? 'Jogadores da versão ' + fullRosterVersion
      : published ? 'Jogadores da antiga v2026.0.2 (se aplicada)' : 'Jogadores identificados em fonte externa';
    const provenance = verified ? roster : external;
    elements.sourceBox.hidden = !provenance;
    if (provenance) {
      elements.sourceLink.href = provenance.sourceUrl;
      elements.sourceLink.textContent = provenance.sourceUrl.split('/')[2];
      elements.sourceReviewed.textContent = '· consultada em ' + provenance.reviewedOn;
    } else {
      elements.sourceLink.removeAttribute('href');
      elements.sourceLink.textContent = '';
      elements.sourceReviewed.textContent = '';
    }
    const fragment = document.createDocumentFragment();
    if (roster) {
      elements.modalNotice.textContent = verified
        ? 'Elenco de 2026 validado e publicado na versão ' + fullRosterVersion + '.'
        : published ? 'Esses jogadores só são preservados na 2026.2.0 se a v2026.0.2 já estava instalada. A nova edição não instala elencos da Série A.'
        : 'PESQUISA EXTERNA, NÃO INSTALADA NO PATCH. ' + external.note + ' Antes da inclusão, faltam conferir vínculos/2026 e validar o arquivo .ban.';
      const roleLabels = ['Goleiro','Lateral','Zagueiro','Meio-campo','Atacante'];
      roster.players.forEach((name,index) => {
        const item = document.createElement('li');
        item.textContent = name;
        if (provenance && Array.isArray(provenance.positionCodes)) {
          const role = document.createElement('span');
          role.className = 'club-player-role';
          role.textContent = ' · ' + roleLabels[provenance.positionCodes[index]];
          item.appendChild(role);
        }
        fragment.appendChild(item);
      });
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
  elements.groupBy.addEventListener('change', clearPageAndRender);
  for (const button of elements.sortButtons) {
    button.addEventListener('click', () => {
      const selected = button.dataset.sort;
      if (!Object.hasOwn(sortValues,selected)) return;
      if (selected === sortKey) sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
      else {sortKey = selected;sortDirection = 'asc';}
      clearPageAndRender();
    });
  }

  getJson('./data/target-abc-2026.json')
    .then(data => {
      validateCatalog(data);
      clubs = data.clubs;
      for (const counter of document.querySelectorAll('[data-division-count]')) {
        counter.textContent = String(data.clubs.filter(c => c.division === counter.dataset.divisionCount).length);
      }
      for (const field of [elements.division,elements.search,elements.rosterFilter,elements.pageSize,elements.groupBy]) {
        field.disabled = false;
      }
      render();
      const hasNewRelease = data.completedReal2026BAndCSquads === 40 &&
        typeof data.publishedRosterVersion === 'string';
      const rosterPath = hasNewRelease ? './data/published-rosters-2026.json'
        : './data/published-rosters-2026-0-2.json';
      return getJson(rosterPath)
        .then(published => {
          rosters = hasNewRelease ? validateFullPublishedRosters(published,data.publishedRosterVersion)
            : validatePublishedRosters(published);
          fullRostersReady = hasNewRelease;
          fullRosterVersion = hasNewRelease ? data.publishedRosterVersion : '';
          rostersReady = true;
          if (fullRostersReady) {render();return;}
          return getJson('./data/researched-rosters-2026.json')
            .then(data => {researchedRosters = validateResearch(data);render();})
            .catch(error => console.warn('Fontes externas indisponíveis:',error.message));
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
