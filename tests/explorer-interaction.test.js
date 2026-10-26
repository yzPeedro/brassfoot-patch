// Browser-independent DOM simulation to exercise actual pagination, filters and dialog logic.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');

class Node {
  constructor(tag='div') {
    this.tag=tag;
    this.children=[];
    this.listeners={};
    this.dataset={};
    this.value='';
    this.textContent='';
    this.disabled=false;
    this.isConnected=true;
    this.attributes={};
    this.parent=null;
    this.open=false;
  }
  setAttribute(name,value){this.attributes[name]=String(value);}
  removeAttribute(name){delete this.attributes[name];}
  querySelector(selector){return selector==='.sort-indicator' ? this.indicator || null : null;}
  appendChild(node){
    if(node.tag==='fragment') for(const child of node.children)this.appendChild(child);
    else {node.parent=this;this.children.push(node);}
    return node;
  }
  replaceChildren(fragment){
    this.children=[];
    if(fragment)this.appendChild(fragment);
  }
  addEventListener(name,handler){this.listeners[name]=handler;}
  dispatch(name,detail){if(this.listeners[name])this.listeners[name](detail||{target:this});}
  closest(selector){
    let node=this;
    while(node){
      if(selector==='tr[data-club-id]' && node.tag==='tr' && node.dataset.clubId)return node;
      node=node.parent;
    }
    return null;
  }
  focus(){doc.activeElement=this;this.focused=true;}
  showModal(){this.open=true;}
  close(){this.open=false;this.dispatch('close');}
}

const ids=[
  'clubs-grid','clubs-division','clubs-search','clubs-roster-filter','clubs-count',
  'clubs-page-size','clubs-previous','clubs-next','clubs-page-label','clubs-group-by',
  'clubs-sort-name','clubs-sort-state','clubs-sort-division','clubs-sort-roster',
  'clubs-heading-name','clubs-heading-state','clubs-heading-division','clubs-heading-roster','club-dialog',
  'club-dialog-close','club-dialog-title','club-dialog-division','club-dialog-source-box','club-dialog-source','club-dialog-reviewed','club-dialog-365scores',
  'club-dialog-description','club-dialog-state','club-dialog-roster-status',
  'club-dialog-player-count','club-dialog-roster-title','club-dialog-notice','club-dialog-players'
];
const nodes=Object.fromEntries(ids.map(id=>[id,new Node()]));
nodes['clubs-page-size'].value='10';
nodes['clubs-group-by'].value='none';
for(const key of ['name','state','division','roster']){
  nodes['clubs-sort-'+key].dataset.sort=key;
  nodes['clubs-sort-'+key].indicator=new Node('span');
}
const counters=['A','B','C'].map(d=>{
  const element=new Node('strong');
  element.dataset.divisionCount=d;
  return element;
});
const doc={
  activeElement:null,
  getElementById:id=>nodes[id]||null,
  querySelectorAll:()=>counters,
  createElement:tag=>new Node(tag),
  createDocumentFragment:()=>new Node('fragment')
};
const catalog=JSON.parse(fs.readFileSync(path.join(root,'data/target-abc-2026.json'),'utf8'));
const modern=catalog.completedReal2026BAndCSquads===40;
const fullRosters=modern ? JSON.parse(fs.readFileSync(path.join(root,'data/published-rosters-2026.json'),'utf8')) : null;
const rosters=JSON.parse(fs.readFileSync(path.join(root,'data/published-rosters-2026-0-2.json'),'utf8'));
const researched=JSON.parse(fs.readFileSync(path.join(root,'data/researched-rosters-2026.json'),'utf8'));
const requests=[];
async function fetchMock(url){
  requests.push(url);
  const data=url.includes('target-abc-2026')?catalog:
    url.includes('published-rosters-2026.json')?fullRosters:
    url.includes('published-rosters')?rosters:
    url.includes('researched-rosters')?researched:null;
  return {ok:!!data,status:data?200:404,json:async()=>data};
}
const script=fs.readFileSync(path.join(root,'divisions.js'),'utf8');
vm.runInNewContext(script,{document:doc,fetch:fetchMock,console},{timeout:3000});

const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  for(let i=0;i<5;i++)await tick();
  const get=id=>nodes[id];
  if(modern) {
    assert.deepEqual(requests,['./data/target-abc-2026.json','./data/published-rosters-2026.json']);
    assert.equal(fullRosters.sourceRelease,catalog.publishedRosterVersion);
    assert.equal(get('clubs-grid').children.filter(x=>x.dataset.clubId).length,10);
    get('clubs-roster-filter').value='published';
    get('clubs-roster-filter').dispatch('change');
    assert.match(get('clubs-count').textContent,/60 clubes encontrados/);
    get('clubs-division').value='B';
    get('clubs-division').dispatch('change');
    assert.match(get('clubs-count').textContent,/20 clubes encontrados/);
    get('clubs-search').value='Criciúma';
    get('clubs-search').dispatch('input');
    const row=get('clubs-grid').children.find(x=>x.dataset.clubId);
    assert.ok(row,'Criciúma from verified B roster should be selectable');
    get('clubs-grid').dispatch('click',{target:row});
    assert.equal(get('club-dialog-title').textContent,'Criciúma');
    assert.match(get('club-dialog-notice').textContent,/validado e publicado na versão/);
    assert.equal(get('club-dialog-source-box').hidden,false);
    assert.equal(get('club-dialog-player-count').textContent,
      String(fullRosters.clubs['br-criciuma-sc'].players.length));
    get('club-dialog').close();
    get('clubs-search').value='';
    get('clubs-group-by').value='roster';
    get('clubs-group-by').dispatch('change');
    get('clubs-sort-state').dispatch('click');
    assert.equal(get('clubs-heading-state').attributes['aria-sort'],'ascending');
    assert.equal(get('clubs-grid').children[0].className,'clubs-group-header');
    console.log('PASS: 60 verified A/B/C rosters, modern published filter, modal, grouping, sorting and pagination.');
    return;
  }
  assert.deepEqual(requests, ['./data/target-abc-2026.json','./data/published-rosters-2026-0-2.json','./data/researched-rosters-2026.json']);
  assert.equal(get('clubs-grid').children.length,10);
  assert.match(get('clubs-page-label').textContent,/Página 1 de 6/);
  assert.equal(get('clubs-previous').disabled,true);
  assert.equal(get('clubs-next').disabled,false);
  get('clubs-next').dispatch('click');
  assert.match(get('clubs-page-label').textContent,/Página 2 de 6/);
  get('clubs-page-size').value='20';
  get('clubs-page-size').dispatch('change');
  assert.match(get('clubs-page-label').textContent,/Página 1 de 3/);
  assert.equal(get('clubs-grid').children.length,20);

  // Accent insensitive search across the three divisions.
  get('clubs-search').value='Cruzeiro';
  get('clubs-search').dispatch('input');
  assert.equal(get('clubs-grid').children.length,1);
  const row=get('clubs-grid').children[0];
  const button=row.children[0].children[0];
  assert.equal(button.textContent,'Cruzeiro');
  button.focus();
  get('clubs-grid').dispatch('click',{target:button});
  assert.equal(get('club-dialog').open,true);
  assert.equal(get('club-dialog-title').textContent,'Cruzeiro');
  assert.equal(get('club-dialog-365scores').hidden,false);
  assert.equal(get('club-dialog-365scores').href,'https://www.365scores.com/pt-br/football/team/cruzeiro-1213/squad');
  assert.equal(get('club-dialog-player-count').textContent,'36');
  assert.equal(get('club-dialog-players').children.length,36);
  assert.ok(get('club-dialog-players').children.some(node=>node.textContent==='Cássio'));
  get('club-dialog-close').dispatch('click');
  assert.equal(get('club-dialog').open,false);
  assert.equal(doc.activeElement,button);

  get('clubs-search').value='Botafogo';
  get('clubs-division').value='B';
  get('clubs-division').dispatch('change');
  assert.equal(get('clubs-grid').children.length,1);
  get('clubs-grid').dispatch('click',{target:get('clubs-grid').children[0]});
  assert.ok(Number(get('club-dialog-player-count').textContent)>15);
  assert.ok(get('club-dialog-players').children.length>15);
  assert.match(get('club-dialog-notice').textContent,/PESQUISA EXTERNA, NÃO INSTALADA NO PATCH/);
  get('club-dialog').close();

  get('clubs-division').value='';
  get('clubs-roster-filter').value='pending';
  get('clubs-roster-filter').dispatch('change');
  assert.equal(get('clubs-grid').children.length,2);
  get('clubs-search').value='São Paulo';
  get('clubs-roster-filter').value='published';
  get('clubs-roster-filter').dispatch('change');
  assert.equal(get('clubs-grid').children.length,1);
  get('clubs-search').value='sao paulo';
  get('clubs-search').dispatch('input');
  assert.equal(get('clubs-grid').children.length,1);

  // Sorting and grouping must operate on all filtered rows before pagination.
  get('clubs-search').value='';
  get('clubs-division').value='';
  get('clubs-roster-filter').value='';
  get('clubs-page-size').value='10';
  get('clubs-page-size').dispatch('change');
  get('clubs-sort-state').dispatch('click');
  assert.equal(get('clubs-heading-state').attributes['aria-sort'],'ascending');
  assert.equal(get('clubs-heading-name').attributes['aria-sort'],'none');
  let visible = get('clubs-grid').children.filter(x=>x.dataset.clubId);
  let states=visible.map(x=>x.children[1].textContent);
  assert.deepEqual(states,[...states].sort((a,b)=>a.localeCompare(b,'pt-BR')));
  get('clubs-sort-state').dispatch('click');
  assert.equal(get('clubs-heading-state').attributes['aria-sort'],'descending');
  visible=get('clubs-grid').children.filter(x=>x.dataset.clubId);
  states=visible.map(x=>x.children[1].textContent);
  assert.deepEqual(states,[...states].sort((a,b)=>b.localeCompare(a,'pt-BR')));

  get('clubs-group-by').value='division';
  get('clubs-group-by').dispatch('change');
  assert.match(get('clubs-page-label').textContent,/Página 1/);
  assert.equal(get('clubs-grid').children[0].className,'clubs-group-header');
  assert.match(get('clubs-grid').children[0].children[0].textContent,/Série A · 20 clube/);
  assert.equal(get('clubs-grid').children.filter(x=>x.dataset.clubId).length,10);
  get('clubs-group-by').value='state';
  get('clubs-group-by').dispatch('change');
  assert.ok(get('clubs-grid').children.some(x=>x.className==='clubs-group-header'));
  get('clubs-group-by').value='roster';
  get('clubs-group-by').dispatch('change');
  assert.ok(get('clubs-grid').children[0].children[0].textContent.includes('clube(s) no filtro'));
  get('clubs-group-by').value='name';
  get('clubs-group-by').dispatch('change');
  assert.ok(get('clubs-grid').children[0].className==='clubs-group-header');
  get('clubs-group-by').value='none';
  get('clubs-group-by').dispatch('change');
  assert.equal(get('clubs-grid').children.filter(x=>x.className==='clubs-group-header').length,0);
  for(const sort of ['name','division','roster']){
    get('clubs-sort-'+sort).dispatch('click');
    assert.equal(get('clubs-heading-'+sort).attributes['aria-sort'],'ascending');
    get('clubs-sort-'+sort).dispatch('click');
    assert.equal(get('clubs-heading-'+sort).attributes['aria-sort'],'descending');
  }
  // Filter + grouping + pagination intersect correctly without leaking Serie D.
  get('clubs-group-by').value='state';
  get('clubs-division').value='B';
  get('clubs-search').value='MG';
  get('clubs-search').dispatch('input');
  assert.equal(get('clubs-grid').children.filter(x=>x.dataset.clubId).length,2);
  assert.equal(get('clubs-grid').children[0].className,'clubs-group-header');
  assert.match(get('clubs-count').textContent,/2 clubes encontrados/);

  // A B-team modal exposes a real source and named players, never claiming installation.
  get('clubs-search').value='Criciúma';
  get('clubs-division').value='B';
  get('clubs-division').dispatch('change');
  assert.equal(get('clubs-grid').children.filter(x=>x.dataset.clubId).length,1);
  get('clubs-grid').dispatch('click',{target:get('clubs-grid').children.find(x=>x.dataset.clubId)});
  assert.equal(get('club-dialog-title').textContent,'Criciúma');
  assert.equal(get('club-dialog-player-count').textContent,String(researched.clubs['br-criciuma-sc'].players.length));
  assert.match(get('club-dialog-notice').textContent,/NÃO INSTALADA NO PATCH/);
  assert.equal(get('club-dialog-source').href,researched.clubs['br-criciuma-sc'].sourceUrl);
  assert.equal(get('club-dialog-source-box').hidden,false);
  assert.ok(get('club-dialog-players').children.some(x=>x.textContent==='Marcelo Hermes'));
  get('club-dialog').close();
  get('clubs-search').value='';
  get('clubs-division').value='';
  get('clubs-division').dispatch('change');
  get('clubs-roster-filter').value='researched';
  get('clubs-roster-filter').dispatch('change');
  assert.equal(get('clubs-count').textContent.includes('40 clubes encontrados'),true);
  get('clubs-roster-filter').value='missing';
  get('clubs-roster-filter').dispatch('change');
  assert.equal(get('clubs-count').textContent.includes('0 clubes encontrados'),true);
  get('clubs-roster-filter').value='';
  get('clubs-roster-filter').dispatch('change');
  get('clubs-division').value='';
  get('clubs-division').dispatch('change');
  assert.equal(counters[0].textContent,'20');
  assert.equal(counters[1].textContent,'20');
  assert.equal(counters[2].textContent,'20');
  console.log('PASS: real table 4-column sorting asc/desc, all-column grouping, pagination, filters, accents, roster modal and focus restore.');
})().catch(e=>{console.error(e);process.exitCode=1;});
