# Revisão crítica do experimento (2026-11-23)

Feita como um revisor de periódico faria, sobre o estado do repositório em 23/11/2026 (adendo 4 lacrado; C e R treinados; teste não avaliado). Cada item diz o que um revisor questionaria, o que existe hoje e o que fazer. Gravidade: **A** pode derrubar a conclusão se não for tratado; **B** será questionado e precisa de resposta escrita; **C** melhora a credibilidade.

## A — Gravidade alta

**A1. O teste não é independente da história do projeto.** Nenhum modelo deste experimento treinou em imagem do teste (divisão em blocos de dias, D31). Mas das 383 imagens do teste novo, **72 foram validação e 80 foram teste na divisão antiga** (40%), e as decisões das Fases 0 a 5 (configuração herdada na D43, a hipótese de que fontes externas pouco ajudam, a escolha de orçamento) se apoiaram em resultados nessas imagens. As outras 231 (60%) eram treino na divisão antiga e nunca foram avaliadas antes. *Ação:* análise de sensibilidade pré-registrada restrita às 231 imagens nunca avaliadas, e declaração do fato no adendo e no artigo.

**A2. Um único conjunto, um único local, 3 dias de teste.** O IC do adendo 4 mede só a variação de treino (10 sementes). Não inclui a incerteza do conjunto de teste (383 imagens correlacionadas em 3 dias). O resultado vale para esses dias e esse sensor. *Ação:* relatar o resultado por dia (descritivo) e dizer no texto que não há IC de generalização; não usar "generaliza".

**A3. Lacuna entre o portão e a atribuição.** O planejamento põe a atribuição (etapa 5: 60 a 100 treinos de R com subconjuntos) entre o portão e o teste único (etapa 6), mas o portão ("o braço difere do controle") só pode ser decidido na validação, já que o teste é de uso único. Isso não está dito no adendo 4. Na validação reavaliada (D56), R−C no mAP50 é −0,13 pp, e o plano diz que, sem diferença, a atribuição não roda. *Ação:* definir por escrito, antes do teste, (a) qual dado decide o portão, (b) que a atribuição sem treino novo (análise por caixa dos 20 modelos já existentes) roda em qualquer caso como exploratória, (c) que qualquer treino novo de atribuição é declarado posterior ao teste.

**A4. A prova de data é fraca.** O lacre é um commit num repositório que o autor controla (histórico reescrevível). *Ação:* etiqueta (tag) de git e depósito com DOI (Zenodo) do estado de cada adendo lacrado; citar o hash e o DOI no artigo.

**A5. A regra de decisão ainda não é código.** O adendo 4 descreve IC95%, TOST, Welch, permutação e Holm, mas não existe `scripts/analisar_principal.py`. Sem ele registrado antes do teste, o revisor pode alegar flexibilidade analítica. *Ação:* escrever, testar com os dados de validação (D56) e registrar o hash antes do teste.

## B — Gravidade média

**B1. Hardware misto.** As 5 primeiras sementes de C rodaram na A100 e as 15 restantes na L4 (D53). A diferença média é +0,26 pp (dentro do desvio), mas a análise de sensibilidade não está pré-especificada. *Ação:* pré-especificar R−C usando só o C da L4 (5 pares) e o C completo (10 pares); relatar os dois.

**B2. Margem de equivalência de ±1 pp sem justificativa escrita.** *Ação:* justificar (cerca de 1,5 vez o desvio entre sementes de 0,6 a 0,7 pp; ganho relatado na literatura de ordem de 3%) e mostrar a conclusão com ±0,5 e ±1,5 pp.

**B3. Medida dependente do procedimento de avaliação.** O mAP50 do `last.pt` reavaliado difere do log de treino em até 0,53 pp (D56, D57); o lote muda 0,18 pp em um modelo. A medida primária é a da API com lote 16, idêntica para todos os modelos, mas o artigo precisa dizer que o log do treino não é a medida.

**B4. Qualidade dos rótulos.** Não há estimativa de erro de rótulo do teste (quem rotulou, concordância, convenção de caixa em embarcação pequena). O mAP50 de objetos pequenos é sensível a isso. *Ação:* auditoria cega de uma amostra de rótulos do teste (só rótulos; não corrigir depois do lacre, só relatar a taxa).

**B5. Métricas secundárias e multiplicidade.** Na validação, o recall small de R ficou 1,09 pp abaixo de C (IC95% ±0,88), com 4 medidas olhadas. *Ação:* declarar que as secundárias não decidem nada, aplicar Holm entre contrastes secundários e relatar o recall small de qualquer forma, também se não favorecer R.

**B6. Atribuição não é causal com 3 braços.** Comparar R, E e G confunde domínio, contagem de imagens únicas, convenção de caixa e outros fatores. A atribuição causal só vem de intervenção dentro de uma fonte (subconjuntos sorteados, parâmetros de geração sorteados). *Ação:* no texto, limitar as afirmações a "esta fonte, neste orçamento" e reservar "causal" à etapa de intervenção.

**B7. Um único detector principal.** YOLO11n, a partir de pesos pré-treinados no COCO (que tem a classe barco). YOLO26n é secundário e ainda não verificado. *Ação:* delimitar a conclusão ao YOLO11n pequeno; verificar o YOLO26n ou retirá-lo do texto.

## C — Credibilidade

**C1. Braços E e G.** O E depende de API fechada (versão do modelo pode mudar; guardar saída e hash), com 22% das caixas inválidas no piloto antigo; o G tem convenção de caixa diferente (A19) e é gerado por terceiro. O 4a e um adendo do G precisam estar lacrados antes de qualquer treino com eles.

**C2. Divulgações.** Já escritas no adendo 4 (seção 10): C visto na validação antes do lacre; A01 sem piloto novo; lacre por etapas. Falta acrescentar A1, B1 e o fato de o teste ter 3 dias.

**C3. Reprodutibilidade com dados privados.** Publicar scripts, hashes, listas de imagens (identificadores), métricas por modelo e regras; as imagens da Marinha só saem por canais que cumprem a D21.

## O que se pode fazer sem esperar o 30/12

1. Escrever e registrar `scripts/analisar_principal.py` (A5) e ensaiar nos dados de validação.
2. Redigir o adendo 4b (A1, A3, B1, B2, B5, estágios do teste) e lacrar.
3. Etiqueta de git e depósito com DOI dos adendos lacrados (A4).
4. Fechar as pendências do 4a (8 itens) e redigir o adendo do G: com os dois lacrados, o teste de C e R pode ser avaliado sem esperar a geração do E e a entrega do G, que passam a ser etapa 2 com regras já fixadas.
5. Auditoria cega dos rótulos do teste (B4).
6. Rascunho de Métodos e de Resultados da validação do artigo, sem números do teste.
