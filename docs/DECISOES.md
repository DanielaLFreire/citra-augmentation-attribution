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
| D06 | 2026-11-11 | Manifesto primeiro: hashes e métricas de cada fonte são calculados lendo direto do pacote (sem extrair); as imagens só são copiadas depois, para listas de treino já fixadas | Extrair e copiar tudo (dezenas de GB) | O pré-registro precisa de manifesto com hash, não das imagens |
| D07 | 2026-11-11 | O manifesto marca duplicatas (nome-base Roboflow, conteúdo exato, quase-duplicata por dHash, colisão com CITRA) mas não remove nada; a exclusão é decidida no adendo | Remover ao construir | Mantém o manifesto auditável e a regra de exclusão pré-registrada |

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
| A09 | Pacote canônico do SeaShips | `SeaShips_voc.zip` com dedup Roboflow (6.979, como nas Fases 0–5); `seaship.zip` (7.000 originais, CSV) | Manter continuidade com as fases anteriores contra partir do pacote sem cópias aumentadas; comparar os dois por hash de conteúdo antes de decidir |
| A10 | Tratamento de quase-duplicatas (quadros de vídeo) | Excluir por cluster; manter e amostrar por cluster; ignorar | Sequências de quadros reduzem a diversidade real de cada fonte e inflam o número aparente de imagens |
| A11 | Papel do `genship3d-mirror.zip` | Usar como Genship oficial; usar só como auditoria; ignorar | Depende do que seus relatórios dizem (pedir `audit_report.json`, `confirmation_report.csv`, `detection_report.csv`) |
| A12 | Composição do braço R (fontes quase sem objetos small) | Balanceada por fonte; balanceada por fonte só com imagens que tenham caixa small; só ABOShips e SMD | Small a 640: ABOShips 70,7%, SMD 57,4%, SeaShips 4,3%, InaTechShips 0%. Balanceado por fonte, metade das amostras viria de fontes sem objetos no regime do CITRA, e o InaTechShips ainda tem 20% de cópias internas |
| A13 | Tratamento das imagens com quase-cópia do CITRA | (proposta) excluir do pool todas as marcadas (dHash ≤ 4): 288 imagens-base do SeaShips, 3 do ABOShips, 62 do InaTechShips; custo desprezível; inspeção visual dos 29 pares com NCC ≥ 0,80 só para documentar. Alternativa: excluir só as confirmadas visualmente | Sem nenhum par ≥ 0,95 e com o CITRA privado, cópia real é improvável. Excluir tudo é mais simples de defender e quase não reduz o pool |
| A14 | Quadro preto com rótulo no treino do CITRA (`11.05.2022-14-13-13.png`, split train): imagem preta de 1.920×1.061 com 3 caixas (classe 2) herdadas em `labels`, `labels_cleaned`, `labels_single_class` e `labels_final` | (recomendação) mover para quarentena: treino passa a 1.347 imagens e 4.486 caixas; varrer val e teste atrás de outros quadros degenerados antes do adendo; manter só se a varredura mostrar que o problema é isolado e a comparabilidade com a Fase 5 for prioridade | Rótulo sobre imagem preta é ruído de rótulo (3 de 4.489 caixas, 0,07%). O custo de remover é perder o reuso dos controles da Fase 5 (A04); o novo experimento treina o braço C de qualquer forma e precisa de bem mais seeds que as 5 da Fase 5. Se existir quadro assim em val/teste, afeta a avaliação |
