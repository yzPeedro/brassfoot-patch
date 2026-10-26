/* Pix voluntário: o payload e a matriz QR são constantes, gerados localmente.
   Sem bibliotecas remotas, cookies, analytics ou chamadas a provedores financeiros. */
(() => {
  'use strict';
  const PIX = '00020126970014BR.GOV.BCB.PIX0136dd20e247-c861-44a1-9a21-2ddb827465e90235Ajude seu amiguinho a tomar um café5204000053039865802BR5925Pedro Henrique Pessoa Cru6009SAO PAULO62140510WP4lJ5p0Ib630482B0';
  // Matriz 61x61 com quiet zone 4, QR Code em nível M. Cada bit é um módulo.
  const QR_SIZE = 61;
  const QR_BITS = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAP44kHkaY/gEEDJ0lxOQQC6rCNo79LoBdWtZKB7V0Auo1Q+/6i6AQW8vRT6xBAP6qqqqqq/gABaMMQkmAAC+bb38HyPgBQHXIYICaYAtkl00cuk0AOHaiUizH6AKNX3NqneDAH770tnpS9gAHEsZ243xQB0OgxtqddAA9oFFXCfDGAXEoibdyySAK/qTDALu5ADQA1tUgt0wAKn+eX2IPwA6J94Yq/CsAz0Cm/sJkOAahPcUGGxRAH+6Qv0G/5gHRTUsV+jEgBq0a2sLUqYBUVZHEpLRAAz9G//S9vkADMOcpbxbWAKouZHHlK1AGDNys00EFgDTUhWZL/ywBEP0pLygTMAomGMliem+AclDzYTzURAPbm/aYnTpAE40cNSteEQCa/1oejFDgBeWcb9SCdIA7uoNJls+8AaM2W3Mix3AN8671bQ1hADA6IX9swyQASeo74jS/4AARZBFdDRkA/kl0r37KmAQUUCRDi8QALrXpP69f5AF1ScsFLPgAC6wIlSadXQBBFqTYocicA/oqier5mMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==';
  const qrTarget = document.getElementById('pix-qr');
  const openButton = document.getElementById('pix-open');
  const dialog = document.getElementById('pix-dialog');
  const closeButton = document.getElementById('pix-close');
  const copyButton = document.getElementById('pix-copy');
  const code = document.getElementById('pix-code');
  const copyStatus = document.getElementById('pix-copy-status');
  if (!qrTarget || !dialog || !openButton || !closeButton || !copyButton || !code || !copyStatus) return;

  // A mesma sequência fica legível para a pessoa, inclusive se o Clipboard API falhar.
  code.value = PIX;

  const bytes = Uint8Array.from(atob(QR_BITS), char => char.charCodeAt(0));
  if (bytes.length !== Math.ceil(QR_SIZE * QR_SIZE / 8)) return;
  const bit = (x, y) => {
    const index = y * QR_SIZE + x;
    return !!(bytes[index >> 3] & (1 << (7 - (index & 7))));
  };
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', '0 0 61 61');
  svg.setAttribute('width', '244');
  svg.setAttribute('height', '244');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', 'QR Code Pix voluntário para apoiar o projeto');
  const background = document.createElementNS(ns, 'rect');
  background.setAttribute('width', '61');
  background.setAttribute('height', '61');
  background.setAttribute('fill', '#ffffff');
  svg.appendChild(background);
  let paths = '';
  for (let y = 0; y < QR_SIZE; y++) {
    for (let x = 0; x < QR_SIZE;) {
      if (!bit(x, y)) { x++; continue; }
      const start = x;
      while (x < QR_SIZE && bit(x, y)) x++;
      paths += 'M' + start + ' ' + y + 'h' + (x - start) + 'v1h-' + (x - start) + 'z';
    }
  }
  const modules = document.createElementNS(ns, 'path');
  modules.setAttribute('d', paths);
  modules.setAttribute('fill', '#101010');
  svg.appendChild(modules);
  qrTarget.replaceChildren(svg);

  openButton.addEventListener('click', () => {
    copyStatus.textContent = '';
    if (typeof dialog.showModal === 'function') dialog.showModal();
    else dialog.setAttribute('open', '');
  });
  closeButton.addEventListener('click', () => {
    if (typeof dialog.close === 'function') dialog.close();
    else dialog.removeAttribute('open');
  });
  dialog.addEventListener('click', event => {
    if (event.target === dialog) {
      if (typeof dialog.close === 'function') dialog.close();
      else dialog.removeAttribute('open');
    }
  });
  copyButton.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(PIX);
      copyStatus.textContent = 'Código Pix copiado.';
    } catch {
      code.focus();
      code.select();
      copyStatus.textContent = 'Selecione e copie o código acima manualmente.';
    }
  });
})();
