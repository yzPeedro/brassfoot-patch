# Gate de evidência da engine

`tools/engine_acceptance.py` valida um manifesto de evidência real antes de
qualquer promoção. O gate é deliberadamente fechado por padrão: testes
unitários, fixtures sintéticas, inspeção de bytecode e cross-build não contam
como gameplay.

O manifesto precisa declarar `synthetic: false`, plataforma Windows, commit e
SHA-256 do build testado, preservação por hash dos saves preexistentes e os
quatro checks `gameplay`, `calendar`, `save_roundtrip` e `rollback` como
`true`. A ausência de qualquer evidência falha; o utilitário não executa o
Brasfoot nem altera instalações, saves ou binários.
