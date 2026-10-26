/* Pix voluntário: o payload e a matriz QR são constantes, gerados localmente.
   Sem bibliotecas remotas, cookies, analytics ou chamadas a provedores financeiros. */
(() => {
  'use strict';
  const PIX = '00020126970014BR.GOV.BCB.PIX0136dd20e247-c861-44a1-9a21-2ddb827465e90235Ajude seu amiguinho a tomar um café5204000053039865802BR5925Pedro Henrique Pessoa Cru6009SAO PAULO62140510WP4lJ5p0Ib630482B0';
  // Matriz 61x61 com quiet zone 4, QR Code em nível M. Cada bit é um módulo.
  const QR_SIZE = 65;
  const QR_BITS = 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/nxQBs+LP4BBN0iVlFiQQC66k79BRsugF1igWAilpdALrCrL8CbS6AQXgC0QjjEEA/qqqqqqqv4AAWrixFoJAAC+eHS+Y1y+AH4pXAjelmZAAq7QknBvZIAZsHDw16dDUAE2vSl0l0eQBijP6wPN8hADv6PA2SGwpABybEbtY6YsAK4zgR7F2MIANDrMqDkzD4A2pvs/diehQBWXa9GZDapwByUNoArR6yAHjfoXogJ0kAK9WcwutNLIAJH+FPxT2fYA1vbgudnqkoAMTgyAfFLPABvu0m/1R/+AHRJjJGmAsQABqLaioLYqkAHEd0EWZSR0AL6hRv4og+gBAaP7FFOnRABS8Qu/UQwjgFKW5k3wbP1ABfCkeLQLawABtdCQVDkSUAB0KMkVrkmIAgLppVcDI1QCfOuCZ7LyEgFxh91U7sjUAFM8hmp6kvsAJFQwa0fGicAhm6FN0iWEwAcjfRskDiFwB7+fZiDbzCAGgQqmOUWqtAKeT39oltrWAfDD0g1aQWYAAsQOP2OE+YAAdodRkd7GAD+SZQrQmGogEFeCPEM2ERALrWfP/p6vsAXVrBjwyeMIAus9YMUjsPABBOmqqB3WrwD+u8DISLQFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA==';
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
  svg.setAttribute('viewBox', '0 0 65 65');
  svg.setAttribute('width', '260');
  svg.setAttribute('height', '260');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', 'QR Code Pix voluntário para apoiar o projeto');
  const background = document.createElementNS(ns, 'rect');
  background.setAttribute('width', '65');
  background.setAttribute('height', '65');
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
