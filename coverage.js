(() => {
  'use strict';
  const root = document.getElementById('coverage-2026');
  const rows = document.getElementById('coverage-rows');
  const summary = document.getElementById('coverage-summary');
  const counters = {
    catalog: document.getElementById('coverage-catalog'),
    identified: document.getElementById('coverage-identified'),
    released: document.getElementById('coverage-released'),
    pending: document.getElementById('coverage-pending')
  };
  if (!root || !rows || !summary || Object.values(counters).some(el => !el)) return;

  fetch('./data/coverage-2026.json', {cache:'no-store'})
    .then(response => {
      if (!response.ok) throw new Error('Coverage information unavailable');
      return response.json();
    })
    .then(data => {
      const expected = {A:20,B:20,C:20,D:96};
      const game = data.legacyGameBase;
      const divisions = Object.keys(expected);
      const recognized = game.matchedConfirmed + game.matchedCandidates;
      const complete = divisions.every(d => {
        const v = game.divisions[d];
        return v && Object.values(v).every(Number.isInteger) &&
          v.confirmed >= 0 && v.candidate >= 0 && v.absent >= 0 &&
          v.confirmed + v.candidate + v.absent === expected[d];
      });
      if (data.schemaVersion !== 1 || data.season !== 2026 ||
          data.catalog.total !== 156 || game.teamFilesAudited !== 703 ||
          recognized !== 110 || game.noCorrespondingTeamFile !== 46 ||
          recognized + game.noCorrespondingTeamFile !== 156 ||
          data.publishedRelease.version !== '2026.0.2' ||
          data.publishedRelease.clubsWithExperimentalRosters !== 20 ||
          data.full156PatchPublished !== false || !complete) {
        throw new Error('Unverified coverage data');
      }
      counters.catalog.textContent = String(data.catalog.total);
      counters.identified.textContent = String(recognized);
      counters.released.textContent = String(data.publishedRelease.clubsWithExperimentalRosters);
      counters.pending.textContent = String(game.noCorrespondingTeamFile);
      const fragment = document.createDocumentFragment();
      for (const division of divisions) {
        const values = game.divisions[division];
        const total = expected[division];
        const found = values.confirmed + values.candidate;
        const article = document.createElement('article');
        article.className = 'coverage-row';
        const heading = document.createElement('div');
        heading.className = 'coverage-row-head';
        const label = document.createElement('strong');
        label.textContent = 'Série ' + division;
        const amount = document.createElement('span');
        amount.textContent = found + ' de ' + total + ' com arquivo candidato na base antiga';
        heading.append(label, amount);
        const meter = document.createElement('div');
        meter.className = 'coverage-meter';
        meter.setAttribute('role','progressbar');
        meter.setAttribute('aria-valuemin','0');
        meter.setAttribute('aria-valuemax',String(total));
        meter.setAttribute('aria-valuenow',String(found));
        meter.setAttribute('aria-label','Arquivos históricos identificados na Série ' + division);
        const bar = document.createElement('span');
        bar.style.width = (found / total * 100) + '%';
        meter.append(bar);
        const detail = document.createElement('p');
        detail.textContent = values.confirmed + ' correspondências resolvidas · ' +
          values.candidate + ' sob revisão · ' + values.absent + ' ausentes';
        article.append(heading, meter, detail);
        fragment.append(article);
      }
      rows.replaceChildren(fragment);
      summary.textContent = 'Base histórica: ' + game.matchedConfirmed +
        ' correspondências resolvidas, ' + game.matchedCandidates +
        ' candidatas e ' + game.noCorrespondingTeamFile +
        ' sem arquivo. Isso não significa elenco de 2026 instalado.';
    })
    .catch(() => {
      summary.textContent = 'Não foi possível validar a cobertura detalhada agora. O download atual continua disponível mediante verificação no GitHub.';
      rows.replaceChildren();
    });
})();
