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
  'clubs-page-size','clubs-previous','clubs-next','clubs-page-label','club-dialog',
  'club-dialog-close','club-dialog-title','club-dialog-division',
  'club-dialog-description','club-dialog-state','club-dialog-roster-status',
  'club-dialog-player-count','club-dialog-roster-title','club-dialog-notice','club-dialog-players'
];
const nodes=Object.fromEntries(ids.map(id=>[id,new Node()]));
nodes['clubs-page-size'].value='10';
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
const rosters=JSON.parse(fs.readFileSync(path.join(root,'data/published-rosters-2026-0-2.json'),'utf8'));
const requests=[];
async function fetchMock(url){
  requests.push(url);
  const data=url.includes('target-abc-2026')?catalog: url.includes('published-rosters')?rosters:null;
  return {ok:!!data,status:data?200:404,json:async()=>data};
}
const script=fs.readFileSync(path.join(root,'divisions.js'),'utf8');
vm.runInNewContext(script,{document:doc,fetch:fetchMock,console},{timeout:3000});

const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  for(let i=0;i<5;i++)await tick();
  const get=id=>nodes[id];
  assert.deepEqual(requests, ['./data/target-abc-2026.json','./data/published-rosters-2026-0-2.json']);
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
  assert.equal(get('club-dialog-player-count').textContent,'—');
  assert.equal(get('club-dialog-players').children.length,0);
  assert.match(get('club-dialog-notice').textContent,/Nenhum elenco real de 2026/);
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

  assert.equal(counters[0].textContent,'20');
  assert.equal(counters[1].textContent,'20');
  assert.equal(counters[2].textContent,'20');
  console.log('PASS: real table pagination, pagination reset, filters, accents, roster modal 36 names, missing B/C and focus restore.');
})().catch(e=>{console.error(e);process.exitCode=1;});
