const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = p => fs.readFileSync(path.join(root,p),'utf8');
const escapeRegExp = value => value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');

const html=read('index.html'),css=read('styles.css'),
      js=read('app.js'),clubsJs=read('divisions.js');
const release=JSON.parse(read('data/release.json'));
const distribution=JSON.parse(read('data/distribution.json'));
const target=JSON.parse(read('data/target-abc-2026.json'));
const historical=JSON.parse(read('data/competitions/2026-brazil.json'));
const rosters=JSON.parse(read('data/published-rosters-2026-0-2.json'));
const researched=JSON.parse(read('data/researched-rosters-2026.json'));
const patchClubs=JSON.parse(read('data/patch-clubs.json'));
const explorerCups=JSON.parse(read('data/explorer-cups.json'));
const rosterCoverage=JSON.parse(read('data/roster-coverage.json'));

for(const id of ['inicio','campo-ao-vivo','downloads','clubes-2026','atualizacoes','cobertura','faq'])
  assert.match(html,new RegExp('id="'+id+'"'));
for(const [,anchor] of html.matchAll(/href="#([^"]+)"/g))
  assert.match(html,new RegExp('id="'+escapeRegExp(anchor)+'"'),'broken anchor #'+anchor);
assert.ok(['published','awaiting_release'].includes(release.status));
assert.match(release.publishedVersion,/^2026\.\d+\.\d+$/);
if (release.publishedVersion==='2026.3.4') {
  assert.match(html,/id="roster-known-issue"/);
  assert.match(html,/não instala os novos jogadores/);
}

if (release.publishedVersion==='2026.3.5') {
  assert.doesNotMatch(html,/id="roster-known-issue"/);
  assert.equal(release.status,'published');
  assert.equal(release.editionStatus,'experimental');
  assert.equal(release.compatibilityVerifiedInGame,false);
  assert.equal(release.rosterTargetClubs,60);
  assert.equal(release.assetName,'Brasfoot-Patch-V4-Elencos-2026.3.5.exe');
  assert.equal(release.fileSizeBytes,5419520);
  assert.equal(release.sha256,'eb546eec17a6e7e20ffb65a32078bccfdea2e2b7f62f429688e698d5a458e45d');
}
assert.match(release.sha256,/^[a-f0-9]{64}$/);
assert.ok(Number.isInteger(release.fileSizeBytes)&&release.fileSizeBytes>0);
const releaseBase='https://github.com/yzPeedro/brassfoot-patch/releases/';
const permanentAsset=file=>releaseBase+'latest/download/Brasfoot-Mega-Patch-'+file;
const versionedAsset=name=>releaseBase+'download/v'+release.publishedVersion+'/'+name;
assert.ok([permanentAsset('windows-x64.exe'),versionedAsset(release.assetName)].includes(release.downloadUrl));
assert.equal(release.assetName,'Brasfoot-Mega-Patch-'+release.publishedVersion+'-windows-x64.exe');
assert.equal(release.compatibilityVerifiedInGame,false);
assert.equal(release.gameplayVerified,false);
if(release.publishedVersion==='2026.2.0') {
  assert.equal(release.sha256,'25264615120dba5681c5238b331d5012c40b3ffea1c933f1d23bdfe755b2cbd3');
  assert.equal(release.fileSizeBytes,967095);
}
assert.equal(distribution.version,release.publishedVersion);
assert.equal(distribution.status,'published');
assert.equal(distribution.channel,'stable');
const packageFiles={'windows-amd64':'windows-x64.exe','linux-amd64':'linux-x64.tar.gz','linux-arm64':'linux-arm64.tar.gz',
  'darwin-amd64':'macos-x64.tar.gz','darwin-arm64':'macos-arm64.tar.gz'};
assert.deepEqual(distribution.artifacts.map(a=>a.platform+'-'+a.architecture).sort(),Object.keys(packageFiles).sort());
for(const artifact of distribution.artifacts){
  const key=artifact.platform+'-'+artifact.architecture;
  assert.equal(artifact.name,'Brasfoot-Mega-Patch-'+release.publishedVersion+'-'+packageFiles[key]);
  assert.ok([permanentAsset(packageFiles[key]),versionedAsset(artifact.name)].includes(artifact.downloadUrl));
  assert.match(artifact.sha256,/^[a-f0-9]{64}$/);
  assert.ok(Number.isSafeInteger(artifact.sizeBytes)&&artifact.sizeBytes>0);
  assert.match(html,new RegExp('data-download-platform="'+key+'" href="'+escapeRegExp(permanentAsset(packageFiles[key]))+'"'));
}
const windowsArtifact=distribution.artifacts.find(a=>a.platform==='windows');
assert.equal(windowsArtifact.name,release.assetName);
assert.equal(windowsArtifact.sha256,release.sha256);
assert.equal(windowsArtifact.sizeBytes,release.fileSizeBytes);
assert.equal(target.season,2026);
assert.equal(target.targetClubs,60);
assert.deepEqual(target.targetDivisions,['A','B','C']);
assert.ok(['untouched','configuration-preserved'].includes(target.serieD.policy));
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
assert.match(html,/Séries A, B, C e D/);
assert.match(html,/<select id="clubs-competition" disabled><option value="">Todas as competições<\/option><\/select>/);
assert.match(html,/<tbody id="clubs-grid">/);
assert.doesNotMatch(html,/releases\/download\/v/);
for(const [,file] of html.matchAll(/href="https:\/\/github\.com\/yzPeedro\/brassfoot-patch\/releases\/[^"]*Brasfoot-Mega-Patch-([^"]+)"/g))
  assert.ok(Object.values(packageFiles).includes(file),'unexpected download '+file);
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
assert.match(html,/id="clubs-sort"/);
assert.match(html,/id="club-dialog-source"/);
for(const coverage of ['updated','partial','preserved','unavailable'])
  assert.match(html,new RegExp('option value="'+coverage+'"'));
assert.match(clubsJs,/fetch\('\.\/data\/explorer-cups\.json'/);
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
  'clubs-roster-filter','club-dialog','club-dialog-title','club-dialog-players','club-dialog-close',
  'clubs-search','clubs-country','clubs-competition','clubs-sort','clubs-count','clubs-reset','clubs-retry']) {
  assert.match(html,new RegExp('id="'+id+'"'));
}
for(const [,id] of clubsJs.matchAll(/byId\('([^']+)'\)/g))
  assert.match(html,new RegExp('id="'+escapeRegExp(id)+'"'),'divisions.js expects #'+id);
const sortKeys=['name','country','competition','coverage','playerCount'];
for(const key of sortKeys){
  assert.match(html,new RegExp('<option value="'+key+'"'));
  assert.match(html,new RegExp('id="clubs-heading-'+key+'"'));
}
assert.match(clubsJs,new RegExp(escapeRegExp("const sortKeys = ['name', 'country', 'competition', 'coverage', 'playerCount'];")));
assert.match(clubsJs,/updateSortLabels\(\)/);
assert.match(css,/\.club-filters\{/);
for(const coverage of ['updated','partial','preserved','unavailable'])
  assert.match(css,new RegExp('\\.coverage-badge\\[data-coverage='+coverage+'\\]\\{'));
assert.match(html,/<dialog class="club-dialog"/);
assert.match(html,/aria-labelledby="club-dialog-title"/);
assert.match(html,/option value="25" selected/);
assert.match(html,/option value="50"/);
assert.match(html,/option value="100"/);
assert.match(clubsJs,/\[25, 50, 100\]\.includes\(selectedSize\)/);
assert.match(clubsJs,/fetch\('\.\/data\/patch-clubs\.json'/);
assert.match(clubsJs,/validateCatalog\(await response\.json\(\)\)/);
assert.match(clubsJs,/validateExtraCatalog\(await extraResponse\.json\(\)\)/);
assert.match(clubsJs,/showModal\(\)/);
assert.match(clubsJs,/elements\.dialog\.close\(\)/);
assert.match(clubsJs,/lastFocus\?\.isConnected \? lastFocus/);
assert.match(clubsJs,/target\?\.focus\(\)/);
assert.match(clubsJs,/pageSize\.addEventListener\('change'/);
assert.match(clubsJs,/elements\.coverage\.addEventListener\('change'/);
assert.match(clubsJs,/search\.addEventListener\('input'/);
assert.match(clubsJs,/slice\(start, start \+ size\)/);
assert.match(clubsJs,/replaceChildren\(fragment\)/);
assert.match(clubsJs,/element\.textContent = text/);
assert.match(clubsJs,/textElement\(matched\.has\(player\) \? 'mark' : 'strong', player\.name/);
assert.doesNotMatch(clubsJs,/innerHTML|eval\(/);
assert.match(css,/\.clubs-pagination\{/);
assert.match(css,/\.club-dialog\{/);
assert.match(css,/\.club-dialog::backdrop\{/);
assert.match(clubsJs,/elements\.search\.addEventListener\('input', resetPage\)/);
assert.match(clubsJs,/\.normalize\('NFD'\)/);
assert.match(clubsJs,/replaceChildren\(fragment\)/);
assert.doesNotMatch(clubsJs,/innerHTML|API_FOOTBALL_KEY|x-apisports-key/);
assert.match(css,/\.clubs-table\{/);
assert.match(css,/\.coverage-grid\{/);
const rosterCountKeys=[...html.matchAll(/data-roster-count="([^"]+)"/g)].map(m=>m[1]);
assert.ok(rosterCountKeys.length>0);
for(const key of rosterCountKeys)
  assert.ok(Number.isSafeInteger(rosterCoverage.counts[key])&&rosterCoverage.counts[key]>=0,'missing roster count '+key);
assert.match(js,/const releaseBase = 'https:\/\/github\.com\/yzPeedro\/brassfoot-patch\/releases\/'/);
assert.match(js,/fetch\(dataUrl\('distribution\.json'\)/);
assert.match(js,/!\/\^\[a-f0-9\]\{64\}\$\/\.test\(item\.sha256\)/);
assert.match(js,/releaseBase \+ 'latest\/download\/Brasfoot-Mega-Patch-' \+ item\.file/);
assert.match(js,/data\.status !== 'published'/);
assert.match(js,/\.catch\(\(\) =>/);
assert.match(html,new RegExp('id="download-hero" data-download-primary href="'+escapeRegExp(permanentAsset('windows-x64.exe'))+'"'));
assert.match(html,new RegExp('id="download-panel" data-download-primary href="'+escapeRegExp(permanentAsset('windows-x64.exe'))+'"'));
assert.doesNotMatch(html,/VERIFICANDO DOWNLOAD|id="roster-known-issue"/);
assert.doesNotMatch(html,/id="alfa-156"|class="ball"/);
assert.doesNotMatch(html+js+clubsJs,/BEGIN PRIVATE KEY|x-apisports-key/);
const versionParts=v=>v.split('.').map(Number);
const notNewer=(a,b)=>{const x=versionParts(a),y=versionParts(b);const i=x.findIndex((p,k)=>p!==y[k]);return i===-1||x[i]<y[i];};
assert.equal(patchClubs.schemaVersion,1);
assert.match(patchClubs.version,/^2026\.\d+\.\d+$/);
assert.equal(patchClubs.version,rosterCoverage.version);
const edition=JSON.parse(fs.readFileSync(path.join(root,'..','config','edition.json'),'utf8'));
assert.ok(notNewer(release.publishedVersion,edition.version));
assert.ok(notNewer(patchClubs.version,edition.version));
assert.equal(patchClubs.clubs.length,patchClubs.totalClubs);
assert.equal(new Set(patchClubs.clubs.map(c=>c.id)).size,patchClubs.totalClubs);
assert.equal(patchClubs.clubs.reduce((sum,c)=>sum+c.playerCount,0),patchClubs.totalPlayers);
assert.ok(patchClubs.clubs.every(c=>c.playerCount===c.players.length&&['updated','partial','preserved','unavailable'].includes(c.coverage)));
assert.ok(patchClubs.countries.every(country=>patchClubs.clubs.filter(c=>c.countryId===country.id).length===country.count));
assert.equal(rosterCoverage.counts.teamsTotal,patchClubs.totalClubs);
assert.equal(rosterCoverage.counts.playersTotal,patchClubs.totalPlayers);
assert.equal(explorerCups.schemaVersion,1);
assert.equal(explorerCups.season,2026);
assert.equal(explorerCups.nations.length,224);
assert.equal(explorerCups.cups.length,8);
console.log('PASS: page sections, published release and five download aliases, '+patchClubs.totalClubs+'-club explorer controls and catalog, legacy A/B/C data and Série D configuration preserved.');
