(() => {
  'use strict';
  const grid = document.getElementById('clubs-grid');
  const division = document.getElementById('clubs-division');
  const search = document.getElementById('clubs-search');
  const summary = document.getElementById('clubs-count');
  if (!grid || !division || !search || !summary) return;
  const normalized = value => String(value ?? '').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').trim();
  let entries = [];
  const description = {A:'Prévia experimental disponível',B:'Elenco 2026 aguardando validação',C:'Elenco 2026 aguardando validação'};
  function draw() {
    const term = normalized(search.value), selected = division.value;
    const visible = entries.filter(c => (!selected || selected === c.division) &&
      (!term || normalized([c.name,c.state,'serie '+c.division].join(' ')).includes(term)));
    const fragment = document.createDocumentFragment();
    for (const club of visible) {
      const row = document.createElement('tr');
      for (const [value,css] of [[club.name,'club-name'],[club.state,''],['Série '+club.division,''],
                                 [description[club.division],'']]) {
        const td = document.createElement('td');
        td.textContent = value; if(css)td.className=css;
        row.appendChild(td);
      }
      fragment.appendChild(row);
    }
    grid.replaceChildren(fragment);
    summary.textContent = visible.length + ' de 60 clubes' +
      (term ? ' correspondentes à pesquisa' : ' previstos nas Séries A, B e C');
  }
  fetch('./data/target-abc-2026.json',{cache:'no-store'})
    .then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json();})
    .then(data=>{
      const expected={A:20,B:20,C:20};
      if(data.schemaVersion!==1||data.targetClubs!==60||!Array.isArray(data.clubs)||
        data.clubs.length!==60||data.serieD?.policy!=='untouched'||
        new Set(data.clubs.map(c=>c.id)).size!==60||
        Object.entries(expected).some(([d,n])=>data.clubs.filter(c=>c.division===d).length!==n))
        throw new Error('Invalid catalogue');
      entries=data.clubs;
      for(const x of document.querySelectorAll('[data-division-count]')) {
        x.textContent=String(expected[x.dataset.divisionCount]??'—');
      }
      division.disabled=false;search.disabled=false;
      division.addEventListener('change',draw);
      search.addEventListener('input',draw);
      draw();
    })
    .catch(()=>{summary.textContent='Não foi possível carregar os clubes. Atualize a página.';grid.replaceChildren();});
})();