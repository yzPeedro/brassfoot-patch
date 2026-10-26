const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const site=path.resolve(__dirname,'..');
const read=(p)=>fs.readFileSync(path.join(site,p),'utf8');
const html=read('index.html'),js=read('pix.js'),styles=read('styles.css');
const sitemap=read('sitemap.xml');

assert.match(html,/<html lang="pt-BR">/);
assert.match(html,/<link rel="canonical" href="https:\/\/yzpeedro.github.io\/brassfoot-patch\/"/);
for(const tag of ['og:title','og:description','og:type','og:url','og:image','og:locale','og:site_name'])
  assert.ok(html.includes('property="'+tag+'"'), 'missing '+tag);
for(const tag of ['twitter:card','twitter:title','twitter:description','twitter:image'])
  assert.ok(html.includes('name="'+tag+'"'), 'missing '+tag);
const structured=html.match(/<script type="application\/ld\+json">([\s\S]+?)<\/script>/);
assert.ok(structured);
const schema=JSON.parse(structured[1]);
assert.equal(schema['@context'],'https://schema.org');
assert.ok(schema['@graph'].some(x=>x['@type']==='WebSite'));
const app=schema['@graph'].find(x=>x['@type']==='SoftwareApplication');
assert.equal(app.offers.price,'0');
assert.equal(app.offers.priceCurrency,'BRL');
assert.equal(app.softwareVersion,'2026.2.0');

const target='https://yzpeedro.github.io/brassfoot-patch/';
for(const page of ['como-instalar','compatibilidade','versoes']) {
  const document=read(page+'/index.html');
  assert.match(document,/<main/);
  assert.match(document,new RegExp('rel="canonical" href="'+target+page+'/'));
  assert.ok(sitemap.includes(target+page+'/'));
  assert.ok(html.includes('href="./'+page+'/"'));
}
assert.ok(sitemap.includes(target+'</loc>'));
assert.ok(html.includes('id="pix-open"'));
assert.ok(html.includes('id="pix-dialog"'));
assert.ok(html.includes('id="pix-qr"'));
assert.ok(html.includes('id="pix-code"'));
assert.ok(html.includes('id="pix-copy"'));
assert.ok(styles.includes('.pix-dialog'));
assert.ok(!/window\.open|fetch\(|XMLHttpRequest|sendBeacon/.test(js),'Pix cannot send payload to remote sites');
const match=js.match(/const PIX = '([^']+)'/);
assert.ok(match,'missing canonical Pix payload');
const payload=match[1];
assert.ok(payload.endsWith('630482B0'),'unexpected Pix ending');
assert.equal(payload.includes('540'),false,'Pix must not define a fixed donation value');
const crc16=(bytes)=>{
  let crc=0xffff;
  for(const byte of bytes){crc^=byte<<8;for(let j=0;j<8;j++)crc=(crc&0x8000)?((crc<<1)^0x1021)&0xffff:(crc<<1)&0xffff;}
  return crc;
};
assert.equal(crc16(Buffer.from(payload.slice(0,-4),'utf8')).toString(16).toUpperCase().padStart(4,'0'),'82B0');
const qr=js.match(/const QR_BITS = '([^']+)'/);
assert.ok(qr);
const packed=Buffer.from(qr[1],'base64');
assert.equal(packed.length,Math.ceil(61*61/8));
const bit=(x,y)=>{const idx=y*61+x;return !!(packed[idx>>3] & (1<<(7-(idx&7))))};
for(let i=0;i<61;i++) for(let j=0;j<4;j++)
  assert.ok(!bit(i,j)&&!bit(j,i)&&!bit(i,60-j)&&!bit(60-j,i),'QR missing quiet zone');
assert.match(html,/100% gratuito/);
console.log('SEO + Pix: canonical, JSON-LD, sitemap, 3 pages, CRC/QR and optional donation OK');
