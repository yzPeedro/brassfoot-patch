# Janelas oficiais e automação

Fonte CBF publicada em 04/10/2025: primeira janela 05/01–03/03/2026, segunda 20/07–11/09/2026. Sete dias corridos depois: 10/03/2026 e 18/09/2026. Fonte: https://www.cbf.com.br/a-cbf/por-dentro-da-cbf/comissao-dopagem/exame-antidoping-e-lbcd/cbf-oficializa-datas-do-calendario-do-futebol-do-brasil-profissional-masculino-de-2026

Uma janela extraordinária para transferências nacionais na Série A foi noticiada para 09–17/07/2026, mas exige confirmação documental oficial antes de qualquer gatilho de publicação; o cadastro está com `confirmed=false`.

`transfer_windows.py` roda offline e produz estados `not_due`, `completed`, `calendar_requires_official_confirmation` e `due_but_publication_blocked_until_release_validation`. A publicação está desabilitada. Datas de anos futuros **não** são extrapoladas.
