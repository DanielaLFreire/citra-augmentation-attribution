# Registro de decisões

Uma entrada por decisão. Estado: **aberta**, **tomada** ou **adiada**. Decisões tomadas depois do lacre do adendo vão também para `docs/DESVIOS.md`.

## Tomadas

| # | Data | Decisão | Alternativas | Motivo |
| --- | --- | --- | --- | --- |
| D01 | 2026-11-10 | Excluir o pacote `iflens.rar` do experimento | Usar como fonte generativa | Segundo a equipe, são imagens coletadas da internet por outro colaborador, sem relação com o CITRA-3D e sem proveniência documentada. Não vem da ferramenta iflens |
| D02 | 2026-11-10 | Rótulos das imagens geradas são herdados da original; nenhuma caixa é criada por detector treinado no CITRA | Pseudo-rótulos do detector do CITRA | Pseudo-rótulos tornariam a avaliação circular |
| D03 | 2026-11-10 | Medir desloc. de caixas por inspeção visual, não por correlação de bordas | Filtro automático por correlação | A correlação indicou deslocamento ~0 onde a inspeção via objetos fora da caixa; descartada como filtro |
| D04 | 2026-11-10 | Desenho em etapas com portões; as perguntas de tipo de fonte e de característica são separadas | Atribuição direta de características | Nenhuma fonte superou o CITRA nas Fases 0–5; atribuição sem efeito detectável não tem o que atribuir |
| D05 | 2026-11-11 | Repositório novo, separado do das Fases 0–5, que fica como arquivo fechado referenciado por tag | Fase 6 no repositório antigo | O documento de abertura do projeto já previa repositório novo; escopo, fontes e adendos são outros |

## Abertas (resolver antes do adendo)

| # | Decisão | Opções | O que pesa |
| --- | --- | --- | --- |
| A01 | Métrica primária | Recall no máximo-F1; recall em limiar fixo; mAP50; AP small | Relevância operacional contra variância; decide o piloto de métrica (etapa 2) |
| A02 | Orçamento de passos | S1 (10.110) ou S2 (25.275) | S2 custa 2,5× mais |
| A03 | Fração externa na lista de treino | 25%, 50% ou as duas | Duas frações dobram o custo do portão |
| A04 | Reutilizar modelos de controle da Fase 5 ou retreinar | Reutilizar; retreinar | Reuso poupa GPU; retreino mantém o pré-registro limpo |
| A05 | Genship 3D: usar as 444 imagens ou renderizar conjunto novo | Existentes; novo | Com 25%, o braço precisa de 1.348 imagens |
| A06 | Manter o braço generativo (E) | Manter se o piloto novo passar; excluir desde já | Ganho esperado baixo no teste atual; custo de API pequeno, auditoria manual grande |
| A07 | Condições do iflens | Conjunto restrito; manter adversas como fator | Noite e neblina densa invalidam rótulos; restringir reduz diversidade |
| A08 | Avaliação em condições adversas | Verificar se existem imagens reais de noite, chuva ou neblina para teste próprio | Sem isso, o benefício plausível do braço generativo não é mensurável |
