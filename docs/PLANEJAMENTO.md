# Planejamento — experimento de atribuição com fontes reais, renderizadas e generativas

2026-11-10

## Pergunta e escopo

O experimento quer responder, com passos de otimização igualados, duas perguntas em sequência:

1. **Que tipo de fonte ajuda?** Adicionar ao treino do CITRA-3D-Real imagens reais públicas, imagens renderizadas por simulador ou imagens editadas por IA generativa melhora, piora ou não altera a detecção no CITRA?
2. **Que características explicam a diferença?** Dentro de cada fonte que passar pela primeira pergunta, quais características das imagens determinam o ganho ou a perda?

A segunda pergunta só é executada se a primeira encontrar alguma fonte com efeito detectável. Um resultado negativo na primeira já é uma entrega publicável.

**Fora do escopo:** composição por recorte-e-colagem (encerrada nas Fases 3 a 5), detecção multiclasse e outras arquiteturas além da YOLO11n. Um segundo domínio-alvo (UA-DETRAC) fica como extensão, não como parte deste plano.

Este documento é um plano de trabalho. Não é o pré-registro: o adendo lacrado será escrito depois das respostas das equipes do Genship 3D e do iflens.

## O que as Fases 0–5 já estabeleceram

Nenhuma fonte externa testada até agora superou o CITRA puro, e os efeitos observados são do tamanho do ruído entre seeds. Essas duas constatações definem o desenho abaixo.

| Achado | Evidência | Consequência para este plano |
| --- | --- | --- |
| Composição por recorte-e-colagem não melhora a detecção | Fase 3: −1,75 pp no teste, 12/12 pares. Fase 5, passos igualados: +0,3 pp (val) e −0,4 pp (teste), inconclusivo | Linha encerrada; não entra como braço |
| Ranking observacional sobre um proxy não prevê utilidade de treino | Contraste: melhor preditor de detectabilidade no Estágio A, efeito nulo como fator de treino no Estágio B | Características só contam se manipuladas ou sorteadas, com treino |
| Épocas fixas confundem dado com passos | Fase 3: células com ~2× os passos do controle | Passos de otimização iguais em todos os braços |
| "Mais dado real ajuda" não está demonstrado | real×2 > real×1 em +1,18 pp no teste, confundido com 2× passos | Não há hipótese positiva estabelecida; o portão inicial é obrigatório |
| O recall da última época é um desfecho ruidoso | Fase 5: desvio das diferenças pareadas de 1,37 pp, contra 0,29 pp na área sob a curva | A métrica primária precisa ser escolhida pela variância (ver Dimensionamento) |
| A validação engana em efeitos pequenos | Efeito de escala (Fase 3) e equivalências secundárias (Fase 5) não replicaram no teste | Decisões por regra pré-registrada; teste avaliado uma vez |
| Contrastes lacrados podem ser redundantes ou não orçados | P6' (adendo 2) exigia 36 treinos não orçados; P12 = P11/2 (adendo 3) | Cada previsão lista as execuções que a testam; contrastes verificados antes de lacrar |

Fontes: `docs/resultados_fase5.md`, `docs/LICOES_para_projeto_imagens_reais.md` e o relatório de atividades de setembro de 2026. Os resultados do Estágio A e da Fase 3 foram lidos por esses resumos, não nos documentos originais.

## Fontes de dados

O alvo é o CITRA-3D-Real (train 1.348 imagens e 4.489 caixas; val 332 e 1.267; teste 401 e 1.247; 82,2% das caixas são small a 640 px). As fontes candidatas a aumento são seis, de três tipos.

| Fonte | Tipo | Imagens | Rótulos | Estado | Pendência |
| --- | --- | --- | --- | --- | --- |
| Singapore Maritime Dataset (on-shore) | Real pública | 914 | YOLO, 7.043 caixas | Imagens inteiras em `smd_clean.zip` (tudo sob `test/`, nomes Roboflow) | Construir manifesto; quadros de 36 vídeos, quase-duplicatas |
| SeaShips | Real pública | 6.979 | VOC XML | Imagens inteiras em `SeaShips_voc.zip` (13.105 JPG, exportação Roboflow com cópias aumentadas; a regra da Fase 0–5 por nome-base resulta em 6.979). Outros dois pacotes: `seaship.zip` (7.000 JPG, CSV) e `SeaShips_voc_incompleto_6509.zip` | Escolher o pacote canônico (decisão A09); objetos grandes |
| ABOShips | Real pública | 9.880 | CSV | Imagens inteiras em `ABOships.zip` (9.880 PNG, 8,2 GB, `Labels/Vesibussi_Labels.csv`) | Construir manifesto; a mais próxima do CITRA em escala |
| InaTechShips | Real pública | 27.796 | YOLO | Imagens inteiras em `dataset_25k_v2.zip` (27.796 JPG, 10,7 GB, divisões internas train/test/val, `reconstrucao_report.json`) | Construir manifesto; ler o relatório de reconstrução; fotos próximas, objetos grandes |
| Genship 3D | Renderizada (simulador GenShip) | 444 | YOLO, 433 arquivos | Pacote inventariado | Perfil estrutural; renderização nova com parâmetros gravados (questionário) |
| Edições iflens do CITRA | Edição generativa de imagens reais (Gemini 3.1 flash lite) | 36 no piloto; nenhuma utilizável | Herdados da imagem original | Piloto auditado: 22% das caixas inválidas | Gerar conjunto novo a partir do treino, se o piloto restrito passar (ver seção do braço generativo) |

O inventário de `_zips` (2026-11-11, `docs/fontes/INVENTARIO_zips_2026-11-11.txt`) mostra três coisas que mudam o plano:

- **As imagens inteiras das quatro fontes públicas existem**; não é preciso procurá-las. O que falta é o manifesto com hash de conteúdo e a checagem de colisão com o CITRA (`scripts/manifesto_fonte.py`).
- **Há um `genship3d-mirror.zip`** com relatórios de auditoria, pasta `quarantine` e arquivos de segmentação. Ele parece ser uma versão já auditada do Genship. Seus relatórios podem responder parte das perguntas 9 a 12 do questionário e precisam ser lidos antes de o Genship ser perfilado.
- **Os pacotes `synth_*.zip` (21.840 imagens cada) são as composições sintéticas das Fases 3–5**, com nomes de imagem do CITRA e sufixo `_vN`. Pertencem à linha encerrada e não podem entrar em nenhum braço nem na lista de fontes externas.

Três observações sobre o iflens condicionam o desenho:

- **Não é uma fonte independente.** Cada imagem editada herda a geometria, a escala e os rótulos de uma imagem real. Aplicado ao treino do CITRA, ele é um aumento de aparência do próprio alvo, e o controle correto é o CITRA repetido.
- **Só entram edições de imagens do split de treino.** Uma edição de imagem de val ou de teste no treino seria vazamento direto. O piloto existente não controlou splits.
- **Não existe um conjunto pronto.** O que há é um piloto de 60 originais e 53 edições, das quais 36 são de imagens reais do CITRA. O braço precisa ser gerado para o experimento.

O pacote `iflens.rar` (34.557 JPG, 21 classes) não é saída da ferramenta. Segundo a equipe, são imagens coletadas da internet por outro colaborador, sem relação com o CITRA-3D. Ele fica fora do experimento: a proveniência não está documentada, e o relatório de 28/05/2026 prevê anotação automática de imagens coletadas com o detector treinado no CITRA.

## Desenho em etapas

O experimento avança por seis etapas, e cada uma só começa se a anterior passar pelo seu portão. Tudo aqui é proposta; os valores finais vão para o adendo lacrado.

1. **Preparação (CPU, sem GPU).** Materializar imagens inteiras e rótulos das quatro fontes públicas; perfilar o Genship 3D no referencial letterbox 640. *Portão:* cada fonte tem imagens suficientes na faixa de escala do alvo para compor o seu braço. Fonte que não tiver sai do desenho, com registro.
2. **Piloto de métrica (quase sem GPU).** Reavaliar os 10 modelos de controle da Fase 5 (CITRA puro, orçamentos S1 e S2, 5 seeds) com desfechos alternativos: recall em limiar de confiança fixo, mAP50, AP do estrato small e média das últimas épocas. *Portão:* escolher como primária a métrica operacionalmente relevante de menor variância entre seeds, antes de ver qualquer braço novo.
3. **Piloto do braço generativo (sem GPU de treino).** Gerar cerca de 100 edições de imagens do treino com condições restritas e auditar todas as caixas. *Portão:* pelo menos 90% das caixas válidas. Abaixo disso o braço E sai do desenho, e o resultado da auditoria é relatado.
4. **Portão por tipo de fonte (GPU).** Até quatro braços com a mesma lista de treino de comprimento fixo e os mesmos passos: C (CITRA repetido), R (CITRA + amostra aleatória das fontes reais públicas, balanceada por fonte), G (CITRA + renderizações do GenShip) e E (CITRA + edições iflens verificadas de imagens do treino). Fração externa única, a definir (proposta: 25%). **Definição, herdada do adendo 3 da Fase 5:** a fração é a proporção de amostras externas no fluxo de treino. Cada imagem do CITRA entra `repeat_real` vezes na lista e cada imagem externa exatamente 1 vez. Com 1.348 imagens do CITRA repetidas 3 vezes (4.044) e fração 0,25, a lista tem 5.392 entradas (= 337 passos × lote 16) e **1.348 imagens externas distintas**. É daí que vem o número de imagens externas por braço. Todos os braços externos usam o mesmo número de imagens externas distintas; fontes com menos imagens distintas que isso precisam repeti-las, o que mistura tipo de fonte com diversidade (decisão A05). Os braços C, R e G não dependem do E. *Portão:* regra de decisão do adendo 3 (IC 95% para diferença, equivalência por TOST com margem de ±1 pp). Se nenhum braço diferir de C, o experimento termina aqui com resultado negativo publicável.
5. **Atribuição dentro das fontes que passaram (GPU).** O método depende da fonte:
   - *GenShip:* renderização com parâmetros sorteados por um plano e gravados por imagem. É intervenção direta.
   - *iflens:* as condições sorteadas e gravadas por imagem são o fator de atribuição.
   - *Reais públicas:* 60 a 100 treinos com subconjuntos sorteados de forma estratificada, e regressão da métrica sobre as características médias de cada subconjunto.
6. **Avaliação única no teste.** Lista fixa de modelos, marcador próprio, verificações de isolamento, como nas Fases 4 e 5.

Regras herdadas sem rediscussão: pré-registro lacrado por SHA-256 antes de qualquer treino, checkpoint fixo (`last.pt`), bloco por seed, geometria sempre em letterbox 640, e separação entre veredito pela letra, leitura substantiva e exploratório.

## Braço generativo: piloto auditado e protocolo de verificação

No piloto existente, 22 das 98 caixas herdadas (22%) não correspondem a um objeto visível no lugar, e 12 das 36 imagens têm pelo menos uma caixa inválida. O braço só entra no experimento se um piloto novo, com condições restritas, passar na auditoria.

### O que o piloto existente mostrou

O piloto tem 60 imagens originais e 53 edições (7 falharam na classificação de condições). Das 53, 36 são de imagens reais do CITRA, 8 do simulador e 9 de origem não identificada. A auditoria abaixo cobre as 98 caixas das 36 imagens do CITRA, classificadas visualmente em recortes ampliados, original e edição lado a lado.

| Situação da caixa na imagem editada | Caixas | % | Das quais small a 640 px |
| --- | --- | --- | --- |
| Objeto visível e alinhado | 46 | 47% | 38 |
| Objeto no lugar, mas muito apagado | 29 | 30% | 22 |
| Nada visível dentro da caixa | 16 | 16% | 15 |
| Objeto deslocado ou substituído | 6 | 6% | 4 |
| Não avaliável (caixa de poucos pixels) | 1 | 1% | 1 |

- **Os desaparecimentos vêm das condições pedidas.** Ocorrem nas edições de noite e de neblina densa. O arquivo de condições define `foggy` como neblina "with object occlusion".
- **Os deslocamentos estão em duas imagens** (`18.04.2022-14-20-13` e `25.04.2022-16-13-26`); a segunda também ganhou uma embarcação que não existia.
- **A geometria global é preservada.** O desvio máximo de proporção nos 53 pares foi de 0,034%. A saída tem sempre 768 px de altura, o que não perde informação para treino a 640 px.
- **O piloto não é reaproveitável.** Não houve controle de split, as condições sorteadas não foram gravadas, e uma das originais (`29.04.2022-14-59-27`) é a imagem de treino posta em quarentena por anotação corrompida.

Limitações da auditoria: um avaliador só, e a fronteira entre "apagado" e "invisível" é subjetiva. Uma medida automática por correlação de bordas indicou deslocamento zero nos casos em que a inspeção visual mostrou objetos fora da caixa, e por isso foi descartada como filtro.

### Por que a expectativa de ganho é baixa

O teste do CITRA é do mesmo domínio do treino. Nos trabalhos abertos na passada de literatura, os ganhos grandes de edição generativa aparecem quando a edição simula uma condição presente no teste e ausente no treino. O que a edição poderia trazer aqui (robustez a noite, chuva e neblina) o teste atual não mede. Um conjunto real de avaliação em condições adversas, se a Marinha tiver, tornaria este o braço mais interessante.

### Geração do conjunto novo

- **Origem:** só imagens do split de treino, lidas de `labels_final`, com lista fixa e hash.
- **Condições:** conjunto restrito. Saem as que invalidam rótulos por construção (neblina com oclusão, noite sem iluminação) e as que estão fora do domínio do teste (neve, nevasca, câmera térmica).
- **Prompt:** instrução explícita de não mover, remover nem adicionar objetos.
- **Registro:** condição original, variação sorteada, semente, modelo e data, gravados por imagem.
- **Volume:** 1.348 imagens para uma fração de 25%, mais cerca de 30% de folga para o descarte. Ao custo relatado de R$ 0,15 por imagem, fica na ordem de R$ 260.

### Verificação dos rótulos

Os rótulos são herdados e verificados; nenhuma caixa é criada por detector.

1. **Triagem automática com SAM 3.** Para cada caixa herdada, segmentar a imagem editada com a caixa como prompt e comparar a máscara com a caixa (`SegmentadorSAM3`, já no repositório). Um prompt de texto aponta embarcações sem caixa, que são as alucinações.
2. **Auditoria manual de todas as caixas.** São cerca de 2.900 caixas; com grades de recortes pareados, de uma a duas horas de um avaliador. Um segundo avaliador em uma amostra dá a concordância entre avaliadores.
3. **Validação da triagem.** A triagem automática só substitui a manual em rodadas futuras se concordar com ela nesta.
4. **Regra de descarte.** Imagem com qualquer caixa reprovada, ou com objeto novo, sai inteira. Nenhuma caixa é corrigida à mão.

O filtro enviesa o conjunto final para objetos maiores e edições suaves. A taxa de descarte por condição e por tamanho de objeto entra no pré-registro e no artigo.

## Dimensionamento

Com o recall no ponto de máximo-F1 como métrica primária, detectar 1 pp exige de 13 a 43 seeds por braço; com mAP50, de 3 a 11. A escolha da métrica pesa mais no custo do que qualquer outra decisão do desenho.

Os números vêm das 30 execuções da Fase 5 (`docs/fase5_resultados_val.json` e `docs/fase5_teste_metricas.csv`): 2 orçamentos × 3 braços × 5 seeds, em validação e teste.

| Métrica | Desvio entre seeds, mesmo braço (pp) | Desvio da diferença pareada M50 − C (pp) | Seeds por braço para detectar 1,0 pp | Para 1,5 pp |
| --- | --- | --- | --- | --- |
| Recall no máximo-F1, última época | 1,65 (val) / 1,61 (teste) | 1,16 a 2,26 | 13 a 43 | 7 a 20 |
| Recall small, confiança fixa 0,25 | 0,81 / 0,85 | 0,58 a 1,25 | 5 a 15 | 4 a 8 |
| mAP50 | 0,59 / 0,62 | 0,24 a 1,04 | 3 a 11 | 3 a 6 |
| Área sob a curva recall × passos (só val) | 0,43 | 0,29 a 0,75 | 3 a 7 | 3 a 5 |

As faixas cobrem os quatro casos medidos (S1 e S2, validação e teste). Seeds calculadas para teste t pareado bicaudal, α = 0,05, poder de 80%.

**Leituras**

- **O recall no máximo-F1 é a métrica mais cara.** O desvio entre seeds é cerca de duas vezes o do recall em limiar fixo e quase três vezes o do mAP50. Hipótese a testar no piloto: o ponto de máximo-F1 muda de limiar a cada modelo, e essa mudança entra como ruído.
- **A área sob a curva é a mais estável, mas mede outra coisa.** Ela resume a trajetória do treino, não o modelo final. Na Fase 5 ela detectou uma desvantagem que o recall final não mostrou. Serve como secundária.
- **Com 10 seeds por braço, o efeito mínimo detectável é aproximadamente igual ao desvio da diferença pareada:** cerca de 1,0 pp em mAP50 e 1,2 pp em recall small no pior caso medido.

**Custo do portão por tipo de fonte** (4 braços, orçamento S2 de 25.275 passos, 0,61 h por execução na A100, tempo medido na Fase 5)

| Seeds por braço | Execuções | Horas de GPU |
| --- | --- | --- |
| 5 | 20 | ~12 |
| 8 | 32 | ~20 |
| 10 | 40 | ~24 |

**Custo da atribuição por subconjuntos aleatórios** (efeito mínimo detectável por 1 desvio-padrão da característica, poder de 80%, aproximação normal)

| Treinos | mAP50 (pp) | Recall small (pp) | Recall máximo-F1 (pp) | Horas em S1 | Horas em S2 |
| --- | --- | --- | --- | --- | --- |
| 60 | 0,21 | 0,29 | 0,60 | ~14 | ~37 |
| 100 | 0,16 | 0,23 | 0,46 | ~24 | ~61 |

**Limitações destes números**

- Cada desvio foi estimado com 5 seeds. O intervalo de 95% de um desvio-padrão com 4 graus de liberdade vai de 0,6 a 2,9 vezes a estimativa.
- Os braços da Fase 5 eram de composição sintética. A variância com fontes reais, renderizadas ou editadas pode ser diferente.
- O piloto de métrica (etapa 2) existe para reduzir essas duas incertezas antes de fixar o número de seeds.

## Literatura e novidade

Primeira passada, não revisão sistemática: quatro buscas e seis trabalhos abertos, a maioria só pelo resumo. Ela já mostra que cada braço tem precedente e que a comparação controlada entre eles não apareceu.

| Trabalho | O que fez | O que significa para este plano |
| --- | --- | --- |
| [SimuShips](https://arxiv.org/abs/2211.05237v1) (Raza et al., OCEANS 2022) | 9.471 imagens simuladas 1920×1080; YOLOv5; relata ganho de 2,9% no recall ao somar simuladas às reais | Precedente direto do braço Genship. O ganho relatado é da ordem do nosso ruído entre seeds, e o resumo não menciona seeds nem teste estatístico |
| [Gurbindo et al., 2025](https://arxiv.org/abs/2505.08228) | Edição por InstructPix2Pix para variar o clima; Faster R-CNN e YOLOv10; BDD100K e ACDC | Mesma família do iflens, em direção autônoma. O resumo não traz números nem diz se o orçamento de treino foi igualado |
| [Stein et al., 2026](https://www.roboticscenter.ai/research/papers/domain-shift-robust-object-detection-with-genai-image-editing-2609) (arXiv 2609.02299) | Edição generativa (Qwen Image Edit, Flux.2) para adicionar camuflagem; GroundingDINO; +20,1 e +14,4 mAP nos domínios camuflados | Os ganhos grandes aparecem quando a edição simula um deslocamento de domínio presente no teste. No CITRA o teste é do mesmo domínio do treino, então a expectativa é de efeito menor |
| [MariData](https://arxiv.org/pdf/2606.03246) (Henriksson et al., 2026) | Tradução de imagens marítimas para neblina, pôr do sol e noite | Não treina detector: a utilidade para detecção fica sem teste. Relata alucinações e perda de embarcações distantes, os dois riscos do braço iflens |
| [DsDm](https://arxiv.org/html/2401.12926v1) (Engstrom et al., ICML 2024), sobre datamodels (Ilyas et al., 2022) | Seleção de dados modelando o desempenho como função do subconjunto de treino; relata que selecionar por semelhança com fontes de "alta qualidade" pode não superar a seleção aleatória | Base metodológica da etapa 5. O achado coincide com o do artigo anterior do grupo sobre similaridade visual |

**Lacuna provável.** Nesta passada não apareceu trabalho que compare fontes reais públicas, renderizadas e editadas por IA contra um mesmo alvo com passos de otimização igualados e várias seeds. Também não apareceu atribuição por subconjuntos aleatórios aplicada à detecção de objetos pequenos.

**O que isso não prova.** Não encontrar em quatro buscas não é evidência de novidade. Antes do pré-registro falta uma busca sistemática em três frentes: aumento generativo para detecção com avaliação de objetos pequenos, sim-to-real marítimo com controle de orçamento de treino, e valoração de dados em detecção. Um segundo trabalho de sim-to-real marítimo (SSDShips, Liao et al., 2025) apareceu na busca e ainda não foi aberto.

## Tarefas imediatas

Nenhuma destas tarefas consome GPU de treino, e as quatro bloqueadas ou a propor dependem das equipes do iflens e do GenShip.

| # | Tarefa | Quem | Depende de | Estado |
| --- | --- | --- | --- | --- |
| 1 | Dimensionamento com os dados da Fase 5 | Claude | Nada | Feito (seção Dimensionamento) |
| 2 | Primeira passada de literatura | Claude | Nada | Feito (seção Literatura) |
| 3 | Auditoria do piloto iflens existente (36 pares, 98 caixas) | Claude | Arquivos do piloto | Feito (seção do braço generativo) |
| 4 | Perfil estrutural do Genship 3D | Daniela, no Colab (CPU) | Nada | Célula pronta e testada com dados fictícios; falta rodar. A parte do `iflens.rar` deixou de ser necessária |
| 5 | Materializar imagens inteiras e rótulos YOLO das quatro fontes públicas, com deduplicação por conteúdo e perfil por imagem | Daniela, no Colab (CPU); Claude prepara o script | Nada | A fazer |
| 6 | Piloto de métrica: reavaliar os 10 modelos de controle da Fase 5 com desfechos alternativos | Daniela, no Colab (GPU leve, só inferência); Claude prepara o script | `last.pt` e `results.csv` da Fase 5 no Drive | A fazer |
| 7 | Busca sistemática de literatura nas três frentes | Claude | Nada | A fazer |
| 8 | Proposta de alteração no iflens: gravar condições e semente por imagem, prompt de preservação de objetos, arquivo de condições restrito | Claude redige; autor da ferramenta decide | Concordância do autor | Proposta redigida em 2026-11-13; falta envio e resposta |
| 9 | Piloto novo do braço generativo: cerca de 100 edições de imagens do treino, com auditoria de todas as caixas | Autor do iflens gera; Daniela e Claude auditam | Tarefa 8 | Bloqueada |
| 10 | Script de triagem com SAM 3 e de grades de recortes para a auditoria manual | Claude | Nada | A fazer |
| 11 | Plano de renderização do GenShip com parâmetros sorteados e gravados | Claude redige; equipe do GenShip executa | Respostas 1 a 3 do questionário do Genship | Bloqueada |
| 12 | Adendo de pré-registro (fatores, braços, seeds, métrica primária, previsões com lista de execuções) | Daniela e Claude | Tarefas 4, 5, 6 e 9 e respostas do questionário do Genship | Bloqueada |

## Decisões em aberto e riscos

### Decisões a tomar antes do adendo

| Decisão | Opções | O que pesa |
| --- | --- | --- |
| Métrica primária | Recall no máximo-F1; recall em limiar fixo; mAP50; AP small | Relevância operacional contra variância; o piloto de métrica decide |
| Orçamento de passos | S1 (10.110) ou S2 (25.275) | S2 custa 2,5× mais. Na Fase 5 o sintético pareceu pior em S1 e neutro em S2, sem confirmação; um orçamento curto pode penalizar fontes externas |
| Fração externa na lista de treino | 25%, 50% ou as duas | Duas frações dobram o custo do portão |
| Controle | Reusar os modelos C da Fase 5 ou treinar de novo | Reusar poupa GPU, mas são modelos já observados e com 5 seeds; treinar de novo mantém o pré-registro limpo |
| Genship 3D | Usar as 444 imagens existentes ou renderizar conjunto novo | Com 25% de fração, o braço precisa de 1.348 imagens: as 444 seriam repetidas cerca de 3 vezes, e parte delas são quadros da mesma sequência |
| Braço generativo | Incluir, se o piloto novo passar; ou deixar fora desde já | Expectativa de ganho baixa no teste atual; custo de API pequeno, mas exige auditoria manual e depende da equipe do iflens |
| Condições do iflens | Conjunto restrito proposto; ou manter as adversas como fator | Manter noite e neblina densa invalida rótulos; restringir reduz a diversidade que o braço poderia trazer |
| Avaliação em condições adversas | Verificar se existem imagens reais de noite, chuva ou neblina para um conjunto de teste próprio | Sem ele, o benefício plausível do braço generativo não é mensurável |
| Repositório | Fase 6 no repositório atual ou repositório novo | O documento de abertura previa repositório novo; a Fase 5 continuou no atual |

### Riscos

- **Nenhum braço diferir do controle.** É o desfecho que os resultados anteriores tornam mais provável. O plano trata isso como resultado, e a etapa de atribuição não roda.
- **Rótulos inválidos no braço generativo.** Medido no piloto existente: 22% das caixas, concentradas nos objetos pequenos. O protocolo de verificação reduz o risco, ao custo de um conjunto enviesado para objetos maiores.
- **Dependência da equipe do iflens.** O braço exige alterações na ferramenta e uma nova rodada de geração. Se não acontecerem, o experimento segue com os braços C, R e G.
- **Vazamento pelo iflens.** Edições de imagens de val ou teste do CITRA não podem entrar no treino.
- **Reprodutibilidade do iflens.** O modelo do Gemini é acessado por API e pode ser descontinuado; as imagens geradas precisam ser arquivadas com hash.
- **Terceira avaliação no teste.** O split de teste já foi avaliado nas Fases 4 e 5. Uma terceira passada só se sustenta com lista fixa pré-registrada e precisa ser declarada no artigo.
- **Validade externa.** Um alvo de cerca de 2 mil imagens e uma arquitetura. Um revisor vai pedir um segundo domínio ou um segundo detector.

## Scripts de apoio

Dois scripts e os arquivos da auditoria acompanham este plano e foram enviados na conversa. No primeiro script, os passos 3 e 4 tratam do iflens.rar e deixaram de ser necessários; os resultados deles podem ser ignorados.

**`perfil_sinteticos.py`**** (tarefa ****4****, Colab, CPU).** Colar o conteúdo em uma célula com o Drive montado. Ele faz quatro coisas:

1. Clona o repositório na tag `v1.1-fase5-fechada` e extrai os dois pacotes para `/content`, nunca para o Drive.
2. Perfila o Genship 3D por pasta de classe e condição com `perfilar_dataset`, o mesmo código letterbox 640 usado no CITRA.
3. Perfila o iflens em `dataset/consolidado` (por split) e em `input/` (por execução).
4. Inspeciona o `iflens.rar`: imagens por pasta e extensão, arquivos `AUG_`, pastas de saída, resolução dos PNG e nomes em comum com cada split do CITRA.

A saída é texto na tela e um JSON em `/content/perfil_sinteticos.json`. O script foi testado só com uma árvore fictícia pequena; a primeira execução real pode revelar casos não previstos.

**`dimensionamento_fase5.py`**** (tarefa 1).** Reproduz as tabelas da seção Dimensionamento a partir de `docs/fase5_resultados_val.json` e `docs/fase5_teste_metricas.csv`. Uso: `python dimensionamento_fase5.py <pasta docs do repositório>`.

**Auditoria do piloto iflens (tarefa 3).** As grades `audit_0.jpg` a `audit_3.jpg` mostram as 98 caixas, original à esquerda e edição à direita, e `auditoria_iflens_piloto.json` traz a classificação de cada caixa. Também foram enviados na conversa.

## Fontes

**Do projeto**

- Repositório [synth-detection-attribution](https://github.com/DanielaLFreire/synth-detection-attribution), commit `e23e0f0` (tag `v1.1-fase5-fechada`): `docs/resultados_fase5.md`, `docs/pre_registro/adendo3_fase5_passos_igualados.md`, `docs/LICOES_para_projeto_imagens_reais.md`, `docs/fase5_resultados_val.json`, `docs/fase5_teste_metricas.csv` e partes de `docs/CHANGELOG_metodologico.md`.
- Relatório de atividades de 18/08 a 16/09/2026 (documento do projeto).
- Repositório [iflens](https://github.com/Starblessed/iflens), commit `beb5e7d`.
- Inventário de `Genship_3D.zip` e `iflens.rar` gerado no Colab, recebido na conversa.
- Piloto do iflens de 11/08/2026: pacotes de entrada (60 imagens e rótulos) e de saída (53 edições), recebidos na conversa.
- Relatório de Atividades DMarSup, 3 a 17 de agosto de 2026 (ferramenta de aumento com IA generativa, arquivo de condições, uso de SAM 3, custo por imagem).
- Relatório de 28/05/2026, Pipeline de Melhoramento do Dataset e Modelo.
- Respostas da equipe do iflens por mensagem, em 10/11/2026.

**Literatura aberta nesta passada**

- Raza et al., [SimuShips](https://arxiv.org/abs/2211.05237v1), OCEANS 2022 (resumo).
- Gurbindo et al., [Object detection in adverse weather conditions for autonomous vehicles using Instruct Pix2Pix](https://arxiv.org/abs/2505.08228), 2025 (resumo).
- Stein et al., [Domain shift-robust object detection with GenAI image editing](https://www.roboticscenter.ai/research/papers/domain-shift-robust-object-detection-with-genai-image-editing-2609), arXiv 2609.02299, 2026 (página de índice, não o artigo).
- Henriksson et al., [MariData](https://arxiv.org/pdf/2606.03246), 2026 (artigo completo).
- Engstrom, Feldmann e Mądry, [DsDm: Model-Aware Dataset Selection with Datamodels](https://arxiv.org/html/2401.12926v1), ICML 2024 (trechos). Ilyas et al., 2022, citado por meio deste.
