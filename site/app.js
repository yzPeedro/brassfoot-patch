(() => {
  'use strict';
  const byId=id=>document.getElementById(id);
  const version=byId('release-version'),status=byId('release-status'),badge=byId('release-badge'),detail=byId('release-detail'),disclaimer=byId('release-status-text');
  const buttons=[byId('download-hero'),byId('download-panel')];
  if(!version||!status||!badge||!detail||!disclaimer||buttons.some(x=>!x))return;
  const base='https://github.com/yzPeedro/brassfoot-patch/releases/download/';
  fetch('./data/release.json',{cache:'no-store'}).then(async response=>{
    if(!response.ok)throw Error('Metadados indisponíveis');
    const metadata=await response.json();
    if(metadata.schemaVersion!==1||!/^[0-9]{4}\.[0-9]+\.[0-9]+$/.test(metadata.publishedVersion||''))throw Error('Metadados inconsistentes');
    version.textContent=metadata.publishedVersion;
    if(metadata.status!=='published'){
      status.textContent='PREPARANDO';badge.textContent='EM PUBLICAÇÃO';
      detail.textContent='O download estará disponível após conferir o arquivo publicado no GitHub Releases.';
      return;
    }
    if(metadata.compatibilityVerifiedInGame!==true||!/^[a-f0-9]{64}$/i.test(metadata.sha256||'')||
       !Number.isInteger(metadata.fileSizeBytes)||metadata.fileSizeBytes<=0)throw Error('Integridade incompleta');
    const expected=base+'v'+metadata.publishedVersion+'/'+metadata.assetName;
    if(metadata.downloadUrl!==expected||!/^Brasfoot-2026-[A-Za-z0-9._-]+\.zip$/.test(metadata.assetName||''))throw Error('Link não autorizado');
    detail.textContent='Verificando hash e tamanho no GitHub…';
    const responseGithub=await fetch('https://api.github.com/repos/yzPeedro/brassfoot-patch/releases/tags/v'+metadata.publishedVersion,{cache:'no-store',headers:{Accept:'application/vnd.github+json'}});
    if(!responseGithub.ok)throw Error('Release ainda não disponível');
    const release=await responseGithub.json();
    if(release.draft||release.tag_name!=='v'+metadata.publishedVersion)throw Error('Release não publicada');
    const asset=(release.assets||[]).find(item=>item.name===metadata.assetName&&item.state==='uploaded'&&item.browser_download_url===expected&&item.size===metadata.fileSizeBytes&&item.digest==='sha256:'+metadata.sha256);
    if(!asset)throw Error('Arquivo público não passou na verificação SHA-256 e tamanho');
    status.textContent='DISPONÍVEL';badge.textContent='PUBLICADO';badge.style.color='#c5ff69';
    detail.textContent='SHA-256: '+metadata.sha256+'. Confirme a integridade após baixar.';
    disclaimer.textContent='Versão '+metadata.publishedVersion+' · ano 2026 e 60 clubes nas Séries A/B/C · B/C ainda com elencos históricos.';
    for(const button of buttons){button.disabled=false;button.textContent='BAIXAR VERSÃO '+metadata.publishedVersion+' ↗';button.addEventListener('click',()=>window.location.assign(expected));}
  }).catch(error=>{status.textContent='INDISPONÍVEL';badge.textContent='NÃO VERIFICADO';detail.textContent='Download bloqueado: '+error.message+'. Consulte a página da release no GitHub.';});
})();