# Deploy (ainda não executado)

A pasta `site/` contém HTML/CSS/JS estáticos e `data/release.json`. Pode ser hospedada em GitHub Pages após existir repositório público configurado. Nenhuma release ou domínio público foi criado neste ambiente; nenhuma URL de projeto foi inventada.

CI offline: `.github/workflows/quality.yml`. Verificação diária de janelas: `.github/workflows/calendar.yml`. Não há workflow habilitado para publicação por falta de patch validado e direitos de distribuição confirmados. Futuros workflows deverão usar GitHub Secrets e construir o download real **antes** de publicar o metadata da versão.
