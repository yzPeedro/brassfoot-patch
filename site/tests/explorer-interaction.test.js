const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');

class Node {
  constructor(tag='div', rooted=false) {
    this.tag=tag;
    this.rooted=rooted;
    this.children=[];
    this.listeners={};
    this.dataset={};
    this.value='';
    this.textContent='';
    this.className='';
    this.disabled=false;
    this.hidden=false;
    this.attributes={};
    this.parent=null;
    this.open=false;
    this.scrollTop=0;
    const node=this;
    this.classList={
      add:name=>{const set=new Set(node.className.split(' ').filter(Boolean));set.add(name);node.className=[...set].join(' ');},
      contains:name=>node.className.split(' ').includes(name)
    };
  }
  get isConnected(){
    let node=this;
    while(node){if(node.rooted)return true;node=node.parent;}
    return false;
  }
  get selectedOptions(){return this.children.filter(child=>child.tag==='option'&&child.value===this.value);}
  setAttribute(name,value){this.attributes[name]=String(value);}
  getAttribute(name){return this.attributes[name]??null;}
  removeAttribute(name){delete this.attributes[name];if(name==='href')delete this.href;}
  descendants(){return this.children.flatMap(child=>[child,...child.descendants()]);}
  querySelector(selector){
    if(selector==='button')return this.descendants().find(node=>node.tag==='button')||null;
    return null;
  }
  querySelectorAll(selector){
    if(selector==='thead th')return this.headings||[];
    if(selector==='button[data-club-id]')return this.descendants().filter(node=>node.tag==='button'&&node.dataset.clubId);
    return [];
  }
  appendChild(node){
    if(node.tag==='fragment'){for(const child of [...node.children])this.appendChild(child);node.children=[];}
    else {node.parent=this;this.children.push(node);}
    return node;
  }
  replaceChildren(fragment){
    for(const child of this.children)child.parent=null;
    this.children=[];
    if(fragment)this.appendChild(fragment);
  }
  contains(node){
    while(node){if(node===this)return true;node=node.parent;}
    return false;
  }
  addEventListener(name,handler){(this.listeners[name]||=[]).push(handler);}
  dispatch(name,detail){for(const handler of this.listeners[name]||[])handler(detail||{target:this});}
  closest(selector){
    let node=this;
    while(node){
      if(selector==='tr[data-club-id]' && node.tag==='tr' && node.dataset.clubId)return node;
      if(selector==='button' && node.tag==='button')return node;
      if(selector==='table' && node.tag==='table')return node;
      node=node.parent;
    }
    return null;
  }
  focus(){doc.activeElement=this;}
  showModal(){this.open=true;}
  close(){if(!this.open)return;this.open=false;this.dispatch('close');}
  getBoundingClientRect(){return {left:0,right:100,top:0,bottom:100};}
}

const ids=[
  'clubs-grid','clubs-search','clubs-country','clubs-competition','clubs-roster-filter','clubs-sort',
  'clubs-count','clubs-active-filters','clubs-reset','clubs-retry','clubs-page-size','clubs-previous',
  'clubs-next','clubs-page-label','club-dialog','club-dialog-close','club-dialog-title','club-dialog-division',
  'club-dialog-description','club-dialog-state','club-dialog-roster-status','club-dialog-player-count',
  'club-dialog-roster-title','club-dialog-notice','club-dialog-players','club-dialog-source-box',
  'club-dialog-source','club-dialog-reviewed','club-dialog-365scores'
];
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
for(const id of ids)assert.match(html,new RegExp('id="'+id+'"'),'index.html lacks #'+id);
const sortKeys=['name','country','competition','coverage','playerCount'];
let doc;
function createPage(fetchImpl){
  const nodes=Object.fromEntries(ids.map(id=>[id,new Node(id==='club-dialog'?'dialog':'div',true)]));
  nodes['clubs-page-size'].value='25';
  nodes['clubs-sort'].value='name';
  nodes['clubs-retry'].hidden=true;
  const table=new Node('table',true);
  table.headings=sortKeys.map(key=>{
    const heading=new Node('th',true);
    heading.id='clubs-heading-'+key;
    return heading;
  });
  table.headings.push(Object.assign(new Node('th',true),{id:''}));
  table.appendChild(nodes['clubs-grid']);
  doc={
    activeElement:null,
    getElementById:id=>nodes[id]||null,
    querySelectorAll:()=>[],
    createElement:tag=>new Node(tag),
    createDocumentFragment:()=>new Node('fragment')
  };
  const window={getSelection:()=>({toString:()=>''})};
  const script=fs.readFileSync(path.join(root,'divisions.js'),'utf8');
  vm.runInNewContext(script,{document:doc,window,fetch:fetchImpl,console,AbortController,URL,setTimeout,clearTimeout},{timeout:3000});
  return {nodes,table,get:id=>nodes[id],heading:key=>table.headings.find(h=>h.id==='clubs-heading-'+key)};
}

const catalog=JSON.parse(fs.readFileSync(path.join(root,'data/patch-clubs.json'),'utf8'));
const extra=JSON.parse(fs.readFileSync(path.join(root,'data/explorer-cups.json'),'utf8'));
const responses={'./data/patch-clubs.json':catalog,'./data/explorer-cups.json':extra};
const requests=[];
let failing=false;
async function fetchMock(url,options){
  requests.push(url);
  assert.ok(options&&options.signal,'catalog requests must be abortable');
  const data=failing?null:responses[url];
  return {ok:!!data,status:data?200:404,json:async()=>data};
}

const pt=value=>value.toLocaleString('pt-BR');
const normalize=value=>String(value??'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLocaleLowerCase('pt-BR').trim();
const collator=new Intl.Collator('pt-BR',{sensitivity:'base',numeric:true});
const totalEntries=catalog.totalClubs+extra.nations.length;
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const settle=async()=>{for(let i=0;i<10;i++)await tick();};
const rowsOf=page=>page.get('clubs-grid').children.filter(row=>row.dataset.clubId);
const found=page=>Number(page.get('clubs-count').textContent.split(' ')[0].replace(/\./g,''));
const change=(page,id,value,event='change')=>{page.get(id).value=value;page.get(id).dispatch(event);};

(async()=>{
  failing=true;
  const broken=createPage(fetchMock);
  await settle();
  assert.deepEqual(requests,['./data/patch-clubs.json','./data/explorer-cups.json']);
  assert.match(broken.get('clubs-count').textContent,/Não foi possível carregar o catálogo/);
  assert.equal(broken.get('clubs-page-label').textContent,'Catálogo indisponível');
  assert.equal(broken.get('clubs-retry').hidden,false);
  failing=false;
  broken.get('clubs-retry').dispatch('click');
  await settle();
  assert.equal(broken.get('clubs-retry').hidden,true);
  assert.equal(rowsOf(broken).length,25);

  requests.length=0;
  const page=createPage(fetchMock);
  const get=page.get;
  await settle();
  assert.deepEqual(requests,['./data/patch-clubs.json','./data/explorer-cups.json']);
  assert.equal(get('clubs-search').disabled,false);
  assert.equal(page.table.attributes['aria-busy'],'false');
  assert.equal(get('clubs-country').children.length,1+new Set([...catalog.countries.map(c=>c.id),...extra.nations.map(n=>n.id)]).size);

  const pages=size=>Math.ceil(totalEntries/size);
  assert.equal(rowsOf(page).length,25);
  assert.equal(get('clubs-page-label').textContent,'Página 1 de '+pages(25));
  assert.equal(found(page),totalEntries);
  assert.equal(get('clubs-previous').disabled,true);
  assert.equal(get('clubs-next').disabled,false);
  get('clubs-next').dispatch('click');
  assert.equal(get('clubs-page-label').textContent,'Página 2 de '+pages(25));
  assert.equal(get('clubs-previous').disabled,false);
  change(page,'clubs-page-size','50');
  assert.equal(get('clubs-page-label').textContent,'Página 1 de '+pages(50));
  assert.equal(rowsOf(page).length,50);
  assert.equal(get('clubs-reset').disabled,true);

  const cruzeiro=catalog.clubs.find(c=>c.name==='Cruzeiro'&&c.country==='Brasil');
  assert.ok(cruzeiro&&cruzeiro.players.length>0);
  change(page,'clubs-search','cruzeiro','input');
  const cruzeiroRow=rowsOf(page).find(row=>row.dataset.clubId===cruzeiro.id);
  assert.ok(cruzeiroRow,'accent and case insensitive club search');
  assert.equal(get('clubs-reset').disabled,false);
  assert.match(get('clubs-active-filters').textContent,/Busca: cruzeiro/);
  const button=cruzeiroRow.querySelector('button');
  assert.equal(button.textContent,'Ver elenco');
  button.focus();
  get('clubs-grid').dispatch('click',{target:button});
  assert.equal(get('club-dialog').open,true);
  assert.equal(get('club-dialog-title').textContent,'Cruzeiro');
  assert.equal(get('club-dialog-state').textContent,'Brasil');
  assert.equal(get('club-dialog-player-count').textContent,pt(cruzeiro.playerCount));
  assert.deepEqual(get('club-dialog-players').children.map(item=>item.children[0].textContent),cruzeiro.players.map(p=>p.name));
  assert.equal(get('club-dialog-roster-status').children[0].dataset.coverage,cruzeiro.coverage);
  assert.equal(get('club-dialog-source-box').hidden,!cruzeiro.sourceUrl);
  if(cruzeiro.sourceUrl)assert.equal(get('club-dialog-source').href,new URL(cruzeiro.sourceUrl).href);
  assert.equal(get('club-dialog-365scores').hidden,true);
  assert.equal(doc.activeElement,get('club-dialog-close'));
  get('club-dialog-close').dispatch('click');
  assert.equal(get('club-dialog').open,false);
  assert.equal(doc.activeElement,button);

  const accented=catalog.clubs.find(c=>/[À-ſ]/.test(c.name)&&c.country==='Brasil');
  assert.ok(accented);
  change(page,'clubs-search',accented.name,'input');
  const withAccent=found(page);
  change(page,'clubs-search',normalize(accented.name),'input');
  assert.equal(found(page),withAccent);
  assert.ok(rowsOf(page).some(row=>row.dataset.clubId===accented.id));

  const player=cruzeiro.players[0];
  change(page,'clubs-country',String(cruzeiro.countryId));
  change(page,'clubs-search',normalize(player.name),'input');
  const playerRow=rowsOf(page).find(row=>row.dataset.clubId===cruzeiro.id);
  assert.ok(playerRow,'player search reaches the club');
  if(!normalize(player.name).split(/\s+/).every(token=>normalize(['Cruzeiro',...cruzeiro.aliases,cruzeiro.country,cruzeiro.competition,cruzeiro.division,cruzeiro.state].join(' ')).includes(token))){
    assert.ok(playerRow.classList.contains('club-search-match'));
    assert.match(playerRow.children[0].children[1].textContent,/^Jogador: /);
    get('clubs-grid').dispatch('click',{target:playerRow.children[1]});
    assert.ok(get('club-dialog-players').children.some(item=>item.children[0].tag==='mark'&&item.children[0].textContent===player.name));
    assert.equal(doc.activeElement,get('club-dialog-close'));
    get('club-dialog').close();
    assert.equal(doc.activeElement,playerRow.querySelector('button'));
  }

  get('clubs-reset').dispatch('click');
  assert.equal(get('clubs-search').value,'');
  assert.equal(get('clubs-country').value,'');
  assert.equal(found(page),totalEntries);
  assert.equal(get('clubs-active-filters').textContent,'Todos os clubes do pacote');

  const countryCount=id=>catalog.clubs.filter(c=>c.countryId===id).length+extra.nations.filter(n=>n.id===id).length;
  change(page,'clubs-country',String(cruzeiro.countryId));
  assert.equal(found(page),countryCount(cruzeiro.countryId));
  assert.ok(rowsOf(page).every(row=>row.children[1].textContent===cruzeiro.country));
  const brazilLeagues=[...new Set(catalog.clubs.filter(c=>c.countryId===cruzeiro.countryId&&c.competition).map(c=>c.competition))];
  for(const league of brazilLeagues)assert.ok(get('clubs-competition').children.some(o=>o.value===league));
  change(page,'clubs-competition',cruzeiro.competition);
  assert.equal(found(page),catalog.clubs.filter(c=>c.countryId===cruzeiro.countryId&&c.competition===cruzeiro.competition).length);
  assert.ok(rowsOf(page).every(row=>row.children[2].textContent===cruzeiro.competition));
  assert.match(get('clubs-active-filters').textContent,/País: Brasil · Competição: /);
  change(page,'clubs-country','');
  change(page,'clubs-competition','');

  for(const coverage of ['updated','partial','preserved']){
    change(page,'clubs-roster-filter',coverage);
    assert.equal(found(page),catalog.clubs.filter(c=>c.coverage===coverage).length);
    assert.ok(rowsOf(page).every(row=>row.children[3].children[0].dataset.coverage===coverage));
  }
  change(page,'clubs-roster-filter','unavailable');
  assert.equal(found(page),catalog.clubs.filter(c=>c.coverage==='unavailable').length+extra.nations.length);
  change(page,'clubs-roster-filter','');

  change(page,'clubs-competition','type:selection');
  assert.equal(found(page),extra.nations.length);
  const selectionRow=rowsOf(page)[0];
  assert.equal(selectionRow.children[4].textContent,'—');
  get('clubs-grid').dispatch('click',{target:selectionRow.children[0]});
  assert.equal(get('club-dialog-player-count').textContent,'Não catalogado');
  assert.equal(get('club-dialog-players').children.length,1);
  assert.match(get('club-dialog-players').children[0].textContent,/convocados não disponível/);
  get('club-dialog').close();
  const teamKey=file=>String(file).split('/').pop().replace(/\.ban$/i,'').toLowerCase();
  const clubCup=extra.cups.find(cup=>cup.kind==='club'&&catalog.clubs.some(c=>cup.teamKeys.some(k=>k.toLowerCase()===teamKey(c.teamFile))));
  assert.ok(clubCup);
  change(page,'clubs-competition','cup:'+clubCup.id);
  const keys=new Set(clubCup.teamKeys.map(k=>k.toLowerCase()));
  assert.equal(found(page),catalog.clubs.filter(c=>keys.has(teamKey(c.teamFile))).length);
  assert.ok(rowsOf(page).every(row=>row.children[2].textContent===clubCup.label));
  change(page,'clubs-competition','');

  change(page,'clubs-page-size','100');
  for(const key of ['name','country','competition']){
    change(page,'clubs-sort',key);
    assert.equal(page.heading(key).attributes['aria-sort'],'ascending');
    for(const other of sortKeys.filter(k=>k!==key))assert.equal(page.heading(other).attributes['aria-sort'],'none');
    const column={name:0,country:1,competition:2}[key];
    const values=rowsOf(page).map(row=>key==='name'?row.children[0].children[0].textContent:row.children[column].textContent);
    assert.deepEqual(values,[...values].sort((a,b)=>collator.compare(a,b)));
  }
  change(page,'clubs-sort','coverage');
  assert.equal(page.heading('coverage').attributes['aria-sort'],'ascending');
  const order={updated:0,partial:1,preserved:2,unavailable:3};
  const coverages=rowsOf(page).map(row=>order[row.children[3].children[0].dataset.coverage]);
  assert.deepEqual(coverages,[...coverages].sort((a,b)=>a-b));
  change(page,'clubs-sort','playerCount');
  assert.equal(page.heading('playerCount').attributes['aria-sort'],'descending');
  const counts=rowsOf(page).map(row=>Number(row.children[4].textContent.replace(/\./g,'')));
  assert.deepEqual(counts,[...counts].sort((a,b)=>b-a));
  assert.equal(counts[0],Math.max(...catalog.clubs.map(c=>c.playerCount)));

  change(page,'clubs-search','zzzz-sem-equipe','input');
  assert.equal(found(page),0);
  assert.equal(get('clubs-grid').children.length,1);
  assert.match(get('clubs-grid').children[0].children[0].textContent,/Nenhuma equipe encontrada/);
  assert.equal(get('clubs-page-label').textContent,'Página 1 de 1');
  assert.equal(get('clubs-next').disabled,true);
  console.log('PASS: '+pt(catalog.totalClubs)+' clubs and '+extra.nations.length+' national teams loaded with retry, pagination, accent-insensitive club and player search, country/competition/cup/coverage filters, sorting, dialogs and focus restore.');
})().catch(e=>{console.error(e);process.exitCode=1;});
