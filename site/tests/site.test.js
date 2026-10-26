const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root,p),'utf8');

const html=read('index.html'),css=read('styles.css'),
      js=read('app.js'),clubsJs=read('divisions.js');
const release=JSON.parse(read('data/release.json'));
const target=JSON.parse(read('data/target-abc-2026.json'));
const historical=JSON.parse(read('data/competitions/2026-brazil.json'));
const rosters=JSON.parse(read('data/published-rosters-2026-0-2.json'));
const researched=JSON.parse(read('data/researched-rosters-2026.json'));


for(const id of ['inicio','cobertura','clubes-2026','recursos','como-funciona','instalador','versao','faq'])
  assert.match(html,new RegExp('id="'+id+'"'));
assert.ok(['published','awaiting_release'].includes(release.status));
assert.match(release.publishedVersion,/^2026\.\d+\.\d+$/);
assert.match(release.sha256,/^[a-f0-9]{64}$/);
assert.ok(Number.isInteger(release.fileSizeBytes)&&release.fileSizeBytes>0);
const activeAssetUrl = 'https://github.com/yzPeedro/brassfoot-patch/releases/download/v' +
  release.publishedVersion + '/' + release.assetName;
assert.equal(release.downloadUrl,activeAssetUrl);
assert.ok(/^(Brasfoot-2026-[A-Za-z0-9._-]+\.(zip|exe)|Brasfoot-Patch-2026-Setup\.exe)$/.test(release.assetName));
if(release.publishedVersion==='2026.2.0') {
  assert.equal(release.sha256,'25264615120dba5681c5238b331d5012c40b3ffea1c933f1d23bdfe755b2cbd3');
  assert.equal(release.fileSizeBytes,967095);
}
assert.equal(target.season,2026);
assert.equal(target.targetClubs,60);
assert.deepEqual(target.targetDivisions,['A','B','C']);
assert.equal(target.serieD.policy,'untouched');
assert.deepEqual(target.serieD.originalBRAcfgExpected,{nTimes:64,nGrupos:8});
assert.equal(target.clubs.length,60);
assert.equal(new Set(target.clubs.map(c=>c.id)).size,60);
for(const div of ['A','B','C']) assert.equal(target.clubs.filter(x=>x.division===div).length,20);
assert.ok(target.clubs.every(c=>c.division!=='D'));
assert.ok([0,40].includes(target.completedReal2026BAndCSquads));
if(target.completedReal2026BAndCSquads === 40) {
  assert.equal(target.publishedRosterVersion,release.publishedVersion);
  assert.equal(release.rostersBCStatus,'verified-2026');
  const complete = JSON.parse(read('data/published-rosters-2026.json'));
  assert.equal(complete.schemaVersion,2);
  assert.equal(complete.sourceRelease,release.publishedVersion);
  assert.equal(complete.totalClubs,60);
  assert.equal(complete.rostersBCVerified,40);
  assert.ok(complete.allRostersVerified);
  const identities = target.clubs.map(x=>x.id);
  assert.ok(identities.every(id=>Object.hasOwn(complete.clubs,id)));
} else {
  assert.notEqual(release.rostersBCStatus,'verified-2026');
}
assert.equal(historical.clubs.length,156);
assert.equal(historical.counts.D,96);
assert.match(html,/Série D/);
assert.match(html,/data-division-count="C"/);
assert.doesNotMatch(html,/data-division-count="D"/);
assert.doesNotMatch(html,/<option value="D">/);
assert.match(html,/<tbody id="clubs-grid">/);
assert.match(html,/v2026\.1\.1 anterior não atende/);
assert.equal(researched.schemaVersion,1);
assert.equal(researched.season,2026);
assert.equal(researched.researchedClubs,40);
const researchedIds=Object.keys(researched.clubs);
assert.equal(researchedIds.length,40);
const bcIds=target.clubs.filter(c=>c.division==='B'||c.division==='C').map(c=>c.id);
assert.ok(bcIds.every(id=>researchedIds.includes(id)));
const observedNames=Object.values(researched.clubs).reduce((sum,r)=>sum+r.players.length,0);
assert.equal(observedNames,researched.totalObservedPlayers??1302);
if (researched.totalObservedPlayers!==undefined){
  assert.equal(researched.totalObservedPlayers,1296);
  assert.ok(Object.values(researched.clubs).every(c=>
    c.positionCodes.length===c.players.length &&
    c.verifiedAges.length===c.players.length &&
    c.reportedCountries.length===c.players.length &&
    c.positionCodes.every(p=>Number.isInteger(p)&&p>=0&&p<=4) &&
    c.positionCodes.filter(p=>p===0).length>=2));
}
assert.ok(Object.entries(researched.clubs).every(([id,r])=>
  bcIds.includes(id) && r.scope==='internet-research-not-installed' &&
  r.completeSeason2026Verified===false && /^https:\/\//.test(r.sourceUrl) &&
  Array.isArray(r.players) && r.players.length>=16 && r.players.length<=60));
assert.match(html,/id="clubs-group-by"/);
assert.match(html,/id="club-dialog-source"/);
assert.match(html,/option value="researched"/);
assert.match(clubsJs,/getJson\('\.\/data\/researched-rosters-2026\.json'\)/);
assert.equal(rosters.schemaVersion,1);
assert.equal(rosters.sourceRelease,'2026.0.2');
assert.equal(rosters.totalClubs,20);
assert.equal(rosters.totalPlayers,730);
assert.equal(Object.keys(rosters.clubs).length,20);
const allNames=Object.values(rosters.clubs).flatMap(team=>team.players);
assert.equal(allNames.length,730);
assert.ok(allNames.every(name=>typeof name==='string'&&name.trim().length>0));
assert.ok(Object.keys(rosters.clubs).every(id=>target.clubs.some(club=>club.id===id&&club.division==='A')));
assert.ok(rosters.clubs['br-cruzeiro-mg'].players.includes('Cássio'));
assert.ok(rosters.clubs['br-santos-sp'].players.includes('Neymar'));
assert.ok(!Object.keys(rosters.clubs).some(id=>target.clubs.find(c=>c.id===id)?.division==='D'));
for(const id of ['clubs-pagination','clubs-page-size','clubs-previous','clubs-next','clubs-page-label',
  'clubs-roster-filter','club-dialog','club-dialog-title','club-dialog-players','club-dialog-close']) {
  assert.match(html,new RegExp('id="'+id+'"'));
}
for(const key of ['name','state','division','roster']){
  assert.match(html,new RegExp('id="clubs-sort-'+key+'"'));
  assert.match(html,new RegExp('id="clubs-heading-'+key+'"'));
}
assert.match(html,/id="clubs-group-by"/);
for(const group of ['name','state','division','roster']){
 assert.match(html,new RegExp('value="'+group+'"'));
}
assert.match(clubsJs,/groupCounts\.get\(group\)/);
assert.match(clubsJs,/updateSortLabels\(\)/);
assert.match(css,/\.clubs-sort\{/);
assert.match(css,/\.clubs-group-header th\{/);
assert.match(html,/<dialog class="club-dialog"/);
assert.match(html,/aria-labelledby="club-dialog-title"/);
assert.match(html,/option value="10" selected/);
assert.match(html,/option value="20"/);
assert.match(html,/option value="50"/);
assert.match(clubsJs,/published-rosters-2026-0-2\.json/);
assert.match(clubsJs,/published-rosters-2026\.json/); 
assert.match(clubsJs,/showModal\(\)/);
assert.match(clubsJs,/elements\.dialog\.close\(\)/);
assert.match(clubsJs,/lastFocus\.focus\(\)/);
assert.match(clubsJs,/pageSize\.addEventListener\('change'/);
assert.match(clubsJs,/rosterFilter\.addEventListener\('change'/);
assert.match(clubsJs,/search\.addEventListener\('input'/);
assert.match(clubsJs,/slice\(start, start \+ size\)/);
assert.match(clubsJs,/replaceChildren\(fragment\)/);
assert.match(clubsJs,/item\.textContent = name/);
assert.doesNotMatch(clubsJs,/innerHTML|eval\(/);
assert.match(css,/\.clubs-pagination\{/);
assert.match(css,/\.club-dialog\{/);
assert.match(css,/\.club-dialog::backdrop\{/);
assert.match(clubsJs,/getJson\('\.\/data\/target-abc-2026\.json'\)/);
assert.match(clubsJs,/addEventListener\('input', clearPageAndRender\)/);
assert.match(clubsJs,/\.normalize\('NFD'\)/);
assert.match(clubsJs,/replaceChildren\(fragment\)/);
assert.doesNotMatch(clubsJs,/innerHTML|API_FOOTBALL_KEY|x-apisports-key/);
assert.match(css,/\.clubs-table\{/);
assert.match(css,/\.edition-counts\{/);
assert.match(js,/api\.github\.com\/repos\/yzPeedro/);
assert.match(js,/item\.digest==='sha256:'/);
assert.match(js,/compatibilityVerifiedInGame!==true/);
assert.doesNotMatch(html,/id="alfa-156"|class="ball"/);
assert.doesNotMatch(html+js+clubsJs,/BEGIN PRIVATE KEY|x-apisports-key/);
console.log('PASS: sortable/groupable A/B/C, 730 installed A player names plus researched B/C names kept separate, Série D untouched.');
