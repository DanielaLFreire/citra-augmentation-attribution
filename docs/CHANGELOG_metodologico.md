# Diário metodológico

Entradas cronológicas, mais recente no fim. Formato: data, o que foi feito, o que foi decidido, o que mudou nas conclusões. Não apagar entradas; corrigir com nova entrada.

## 2026-11-10 — Abertura do experimento de fontes de aumento

- Pergunta posta: que características das imagens (reais públicas, renderizadas, geradas) importam para escolher imagens que aumentam o CITRA-3D-Real. Parecer: viável e publicável, mas só como comparação de tipos de fonte com passos igualados, seguida de atribuição dentro das fontes que passarem.
- Inventário dos pacotes `Genship_3D.zip` e `iflens.rar` rodado no Colab. Questionário às equipes elaborado (`docs/QUESTIONARIO_equipes.md`).
- Respostas da equipe do iflens: o SAM 3 só detectou alucinação e deslocamento; rótulos herdados das originais; Gemini 3.1 flash lite; sem splits no teste preliminar.
- Piloto do iflens recebido (60 originais, 53 edições, 7 falhas de classificação). Auditoria visual de 98 caixas em 36 imagens do CITRA: 22% inválidas (C+D). Detalhes em `docs/PLANEJAMENTO.md` e `data/auditoria_piloto_iflens/`.
- `iflens.rar` excluído do experimento (D01).
- Dimensionamento calculado com os dados da Fase 5 (`scripts/dimensionamento_fase5.py`).

## 2026-11-11 — Repositório criado

- Estrutura criada (D05). Planejamento e questionário migrados para Markdown. Scripts de apoio, dados herdados da Fase 5 com proveniência, auditoria do piloto, ficha de cada fonte, livro de alegações e esboço do artigo.
- Nenhum treino executado neste repositório. Nenhum adendo lacrado.

## 2026-11-11 (tarde) — Inventário de `_zips` e construtor de manifestos

- Inventário rodado por Daniela (`docs/fontes/INVENTARIO_zips_2026-11-11.txt`). Resultado: as imagens inteiras das quatro fontes públicas existem; há três pacotes de SeaShips; `dataset_25k_v2.zip` é o InaTechShips com divisões internas e relatório de reconstrução; `genship3d-mirror.zip` traz relatórios de auditoria do Genship; os `synth_*.zip` são as composições da linha encerrada.
- Correção ao planejamento: a definição de "fração externa" não estava escrita. Pela definição do adendo 3 da Fase 5 (fração do fluxo de amostras; CITRA repetido 3 vezes; lista de 5.392 entradas), 25% dá 1.348 imagens externas distintas, como o plano já dizia. Uma leitura minha de que o número estaria errado (25% de 1.348 = 337) usava outra definição e estava errada. A definição foi acrescentada ao texto.
- `scripts/manifesto_fonte.py`: lê direto do pacote, calcula hash de conteúdo, dHash, caixas e small a 640, marca duplicatas e colisões com o CITRA. Testado com pacotes fictícios (11 testes passam); **não rodado em dado real**.
- Decisões D06, D07; abertas A09 a A11.

## 2026-11-12 — Primeiros manifestos de ABOShips e InaTechShips; SeaShips falhou

- SeaShips parou em arquivo ilegível; script corrigido (registra e continua, hash do pacote opcional em qualquer tamanho, subcomando `colisoes` para inspeção visual). 14 testes passam. Reexecução pendente.
- ABOShips: 9.880 imagens, 839 sem caixa, 70,7% small. InaTechShips: 27.796 imagens, 1 caixa por imagem, 0% small, 20,3% de cópias exatas internas. Colisões por quase-cópia com o CITRA: 3 e 62, a inspecionar. Detalhes e ressalvas em `docs/fontes/FICHA_publicas.md`.
- Abertas A12 (papel do InaTechShips) e A13 (quase-cópias do CITRA).

## 2026-11-12 (tarde) — Manifestos das quatro fontes públicas

- Rodados no Colab com gravação no Drive (`EXPERIMENTO_ATRIBUICAO_CAUSAL/manifestos/`). SHA-256 dos quatro pacotes registrados em `docs/fontes/FICHA_publicas.md`. CITRA: 2.083 imagens (2 em quarentena).
- SeaShips: 13.105 imagens, 6.125 cópias exatas por nome-base, 6.979 únicas (igual às Fases 0–5); 329 sem XML casado; 4,3% small. Tamanho small: ABOShips 70,7%, SMD 57,4%, SeaShips 4,3%, InaTechShips 0%.
- Quase-cópias com o CITRA: SeaShips 542, ABOShips 3, InaTechShips 62. Nada foi concluído; adicionada a correlação 64×64 (`ncc_64`) ao subcomando `colisoes` para separar cópia de coincidência. A12 reescrita (composição do braço R).
- Premissa informada por Daniela: o CITRA-3D-Real é um dataset operacional privado da Marinha, não pode estar entre as imagens públicas. As quase-cópias marcadas (607 no total) são tratadas como falsos positivos prováveis; a checagem por hash exato e NCC continua para documentar a ausência de vazamento.
- NCC das colisões: nenhum par ≥ 0,95 (máximos 0,892 / 0,444 / 0,938). 29 pares em 0,80–0,95 para inspeção visual. Imagem uniforme no treino do CITRA (`11.05.2022-14-13-13.png`) identificada pelos pares com NCC 0. Proposta A13 (excluir tudo que o dHash marcar) e aberta A14.
- `11.05.2022-14-13-13.png` (train) é um quadro preto com 3 caixas herdadas em todas as versões de rótulo (`labels_final` inclusive). Provável falha de exportação do quadro com rótulo do quadro verdadeiro. Novo `scripts/auditar_degeneradas.py` para varrer CITRA e fontes públicas atrás de quadros pretos/estourados/uniformes (limites não calibrados). A14 atualizada.
- Varredura de quadros degenerados (limites não calibrados): CITRA 4 de 2.083 (train 3, test 1); SeaShips, ABOShips e InaTechShips 0 (SeaShips: 1 arquivo ilegível, já registrado). Candidatos extras no CITRA, todos diurnos: `07.07.2022-09-39-44`, `07.07.2022-09-40-32` (train), `11.07.2022-10-56-15` (test). Verificar rótulos e imagem. A14 ampliada.
- Calibração da varredura (`--todas`): lacuna de brilho entre 16,1 e 67,3. Seis quadros diurnos subexpostos no CITRA (train 4, test 2), dois deles acima dos limites originais (médias 9,1 e 16,1, desvio ~30). As imagens inspecionadas não são pretas puras (exceto `11.05.2022-14-13-13`): têm horizonte e ruído com sinal ínfimo. Novo `scripts/inspecionar_escuras.py` (contraste esticado + caixas). A14 reescrita.

- Inspeção visual das 5 quase-pretas com contraste esticado: nenhuma caixa cai sobre embarcação claramente visível (07.07 09-40-32 mostra traços difusos; 11.07 vazio/ruído de compressão). A14: proposta de quarentena dos 4 de treino; teste intacto; sensibilidade no adendo. Aguarda confirmação de Daniela.
- A14 decidida por Daniela: quarentena de 3 quadros de treino (11.05 14-13-13; 07.07 09-39-44; 11.07 09-43-17); 07.07 09-40-32 fica como incerto e entra na sensibilidade; teste intacto (sensibilidade sem 11.07 10-56-15 e 10-57-12). Regra registrada antes de qualquer treino.
- Manifestos completos das quatro fontes públicas e relatórios .json entram em manifests/ com SHA-256 registrado em hashes.json. Conferência CSV × relatório: imagens, caixas, small e colisões batem nas quatro fontes.
- Coleta de pendências (zips lidos sem extrair): ABOShips tem 9.041 nomes distintos no CSV, as 839 imagens sem caixa não têm linha no CSV (nome casa; natureza desconhecida). SeaShips: `seaship.zip` é só classificação (sem caixas); A09 resolvida a favor de `SeaShips_voc.zip` dedupado. Entre as 6.979 únicas, nenhuma sem caixa; 21 números originais ausentes. Corrigida coluna extra com hash errado (SMD) na linha SeaShips da tabela da FICHA_publicas.
- Decididas por Daniela (2026-11-12): D08 (A13, exclusão total pelo dHash, lista `manifests/exclusao_R_A13.csv`, 607 arquivos, hash registrado), D09 (A04, retreinar C com checagem de reprodutibilidade contra a Fase 5), D10 (A14), D11 (A09). Relatórios do genship3d-mirror e do InaTechShips copiados para `data/relatorios_fontes/` com proveniência.
- Relatório de qualidade das anotações (PDF) lido: Genship 3D tem 444 imagens (433 com rótulo, 1.772 caixas, classes 1 e 4, 87,79% de match SAM3); CITRA-mirror tem 2.082 pares, 7.012 caixas, 5 linhas com classe inválida em quarentena, e o relatório afirma que `11.05.2022-14-13-13` tem 41 bytes (divergente do quadro preto decodificável que temos). Abertas: A15 (versão dos rótulos do CITRA) e a conferência do arquivo.
- Conferido: `11.05.2022-14-13-13.png` na raiz do CITRA tem 6.003 bytes (não 41), SHA-256 9dcd4bf0…de9cda; o relatório de qualidade descreve outra versão. D10 atualizada. A15 (versão dos rótulos) segue aberta.
- `citra-mirror.zip` inspecionado: layout próprio (`navio/` sem split; rótulos `labels`, `labels_pass_1`, `labels_reviewed`; 2.077 imagens + 6 pares em quarentena = 2.083, total igual ao da raiz). O quadro `11.05.2022-14-13-13.png` do espelho tem 41 bytes (PNG truncado, 1920×1061) e a raiz tem um substituto preto de 6.003 bytes; D10 reescrita. Repositório antigo confirma `labels_final` (de `labels_single_class`, manifesto SHA-256, congelado em 2026-09-01) como rótulo oficial das Fases 0–5; A15 reformulada. Novo `scripts/comparar_rotulos_mirror.py`.
- Daniela confirma `labels_single_class` nas Fases 0–5 (= `labels_final`, cópia com manifesto). Comparação com o espelho: `labels` 1.980 iguais / 97 diferem / 4 ausentes (quarentena do espelho); `labels_pass_1` 928 iguais; `labels_reviewed` 991 iguais. A15 fechada como D12. O relatório SAM3 (6.988 anotações processadas, 60,73% de match) descreve `labels` do espelho, que difere de `labels_final` em 97 imagens: citar com essa ressalva. Corrigida linha de D10/D11 que uma edição anterior tinha fundido. Pendentes: manifests de `labels_final`, lista das 97 diferenças.
- Manifestos de `labels_final` (train/val/test) registrados com proveniência em `data/labels_final_citra/`; totais batem (2.081 arquivos, 7.003 caixas). Diferenças com o espelho `labels`: 94 imagens com 1–3 caixas de coordenadas diferentes (106 caixas) e 3 imagens com 1 caixa a menos na raiz; enriquecidas em status `shifted`/`orphan` do SAM3.
- Confirmadas por Daniela: D13 (A10: cota por sessão/vídeo), D14 (A11: espelho como auditoria), D15 (A12: R = ABOShips + SMD). Aberta A16: a divisão do CITRA parece aleatória por quadro (27 dias nos 3 splits; mediana de 55 s até o quadro de treino mais próximo de cada quadro de teste, medida por `scripts/analise_temporal_citra.py`). Perguntas ao responsável pela divisão em `docs/QUESTIONARIO_equipes.md`.
- D16 (Daniela): regra condicional para a divisão do CITRA fixada antes da resposta do responsável pelos splits (A16 fechada como regra). Decisões que sobram, só se a divisão for refeita: sorteio dos dias com semente pré-registrada e eventual estratificação por condição.
- Novo `scripts/gerar_lista_r.py` (D13, D15): lista do braço R por cota por sessão/vídeo, 1 imagem por cluster dentro da unidade, sem as 607 da A13, sem as 839 do ABOShips sem caixa. Execução de teste (seed 42, não registrada): ABOShips 7.788 elegíveis em 202 sessões, SMD 743 em 36 vídeos; R = 674 + 674; SMD usa 91% do que resta. Listas oficiais só depois da A16 e das sementes.
