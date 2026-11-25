# Revisão crítica 2 (2026-11-25)

Estado revisto: adendos 4 e 4a lacrados; 4b e 4c em rascunho; C, R e réplicas treinados; teste não avaliado; 150 edições geradas, auditoria humana em curso; filtro congelado. Segue a de 23/11 (`REVISAO_CRITICA_2026-11-23.md`), cujos itens A1, A2, A3, A5, B1, B2, B3, B5 e B6 foram tratados no 4b (ainda não lacrado). Gravidade: **A** pode derrubar ou esvaziar a conclusão; **B** será cobrado por revisor; **C** credibilidade. Nada aqui altera texto lacrado; o que exigir regra nova entra por adendo antes do estágio 1.

## A — o que mais pesa para um periódico

**A1. Falta o controle que isola o que o braço E mede.** O E é o CITRA de treino reeditado (mesmas cenas, mesmas caixas). Se E diferir de C, o revisor pergunta: é a edição generativa ou qualquer perturbação fotométrica faria o mesmo? Além disso, o próprio código do iflens anota que a saída tem resolução diferente da entrada (por exemplo, altura 768), então E também difere de C em resolução e nitidez. Sem um braço de aumento clássico (chuva, neblina, brilho e reescala sintéticos sobre as mesmas 1.370 fontes, mesmo orçamento), um efeito de E não é atribuível à IA generativa, e um efeito nulo de E não distingue "edição inútil" de "artefato anula o ganho". *Ação:* braço A (aumento clássico), 10 sementes na L4 (cerca de 6,5 h), protocolo fixado por adendo antes do estágio 1, contraste E−A secundário na família de Holm. É a adição de melhor custo-benefício do projeto.

**A2. O resultado mais provável é nulo, e o desenho atual não diz por quê.** Na validação, R−C é −0,13 pp. Com 1.370 imagens reais do próprio alvo e teste do mesmo sensor, o treino pode estar saturado: fonte externa ajuda sobretudo com escassez ou mudança de domínio. Um nulo em um único ponto de volume é pouco para uma boa revista. *Ação (exploratória, só na validação, como o 4b §6 já permite):* curva de escassez, C e R com 25% e 50% do CITRA de treino, declarada posterior ao desenho e sem uso do teste. Transforma "não ajudou" em "ajuda ou não em função do volume de dado do alvo", que é o resultado útil para quem opera.

**A3. O filtro R4 pode enviesar o E contra embarcações pequenas.** R4 sinaliza toda folha em que o modelo não consegue verificar uma caixa; no desenvolvimento, as perdas e os casos de `nao_avaliavel` eram alvos minúsculos (D69). Logo o E tende a perder justamente as imagens com embarcações pequenas, e o título do artigo fala de embarcações pequenas. *Ação:* pré-especificar agora, antes de aplicar o filtro, a comparação descritiva da distribuição de área das caixas e de caixas por imagem entre lista elegível, edições sinalizadas e E final; declarar o viés de seleção nas limitações; interpretar recall small do E com essa ressalva.

**A4. O classificador de condições não mede a hora do dia.** Nas 150 originais, todas tiradas entre 8h e 16h (nome do arquivo), o `qwen` devolveu `dusk` ou `dawn` em 52 (35%) e `morning` em 4; com um mapa generoso (manhã até 11h, meio-dia 11–13h, tarde depois), acerta cerca de 1/3. `atmosphere` saiu `haze` em 138 de 150. Consequências: (i) "a variação exclui o valor original" não garante mudança real; (ii) qualquer atribuição por "condição original → nova" é inválida. Não afeta a fidelidade de rótulos nem a regra de uso do E. *Ação:* relatar essa concordância (o carimbo de hora é verdade de graça), usar na atribuição só a condição-alvo e a hora do arquivo, e não descrever o E como "mudança de condição verificada".

**A5. Um detector só.** YOLO11n pré-treinado no COCO. O YOLO26n está previsto e não verificado. *Ação:* decidir antes do estágio 1: verificar e rodar (3 sementes, C e R) ou retirar do texto; idealmente incluir um detector de família diferente como secundário. Se não houver, o título e o resumo dizem "YOLO11n".

## B — será cobrado

**B1. Prova de data.** Etiquetas no GitHub podem ser movidas. *Ação:* depósito com DOI (Zenodo ou OSF) dos adendos lacrados e de `hashes.json` antes do estágio 1. Pendente desde 23/11.

**B2. 4b ainda sem lacre.** Enquanto fica aberto, mais dados de validação e do 4a são vistos, e a errata do 4a só passa a valer como texto lacrado quando o 4b for lacrado. *Ação:* decidir A1 e A5 (entram no 4b ou em adendo próprio) e lacrar.

**B3. Cegueira da auditoria das 150 é parcial.** Há um prompt só, e a condição é visível na imagem; a cegueira real é entre avaliadores e em relação ao filtro. Daniela desenhou o estudo, viu os registros de geração e recebeu esclarecimentos durante a avaliação (25/11: diferença `apagada`/`sem_objeto_original`, caixas sobre o céu, tipo do objeto adicionado na observação), o último depois de ter avaliado dezenas de folhas. *Ação:* registrado em `DESVIOS.md`; o mesmo texto vai ao José; Daniela revê as folhas em que já marcou objeto adicionado para pôr o tipo; o artigo descreve a cegueira como ela é.

**B4. Decisão do E em estimativa pontual, com limiar posterior ao piloto.** Já declarado no 4a. *Ação:* acrescentar ao relato as características operacionais da regra (probabilidade de aprovar o E para taxas e sensibilidades verdadeiras plausíveis, por simulação), para o leitor ver o quanto a regra discrimina com cerca de 25 positivos.

**B5. Produção do E ainda sem script registrado.** É o caminho crítico (cerca de 1.900 a 2.740 gerações até 20/12). O procedimento do estrato de risco precisa ser o mesmo das 150 (D73, D74), e a lista de sementes das condições precisa de hash antes da primeira geração.

**B6. Rótulos do teste sem estimativa de erro** (B4 da revisão anterior, pendente). Auditoria cega de uma amostra, só relato, antes do estágio 1.

**B7. Título e métrica.** O título fala de embarcações pequenas; a primária é mAP50 global e as métricas de pequenas não têm teste. *Ação:* ajustar o título ou assumir no texto que pequenas é descritivo.

**B8. Braço G.** Terceiro gera, versão da ferramenta indefinida, licença dos modelos 3D pendente, seis decisões abertas, prazo 30/12. O mais provável é sair. *Ação:* não deixar o G segurar o estágio 1 além do que o 4b já prevê; se sair, o título perde "renderizadas".

## C — credibilidade

- Incerteza conjunta: bootstrap em dois níveis (sementes e imagens) sobre as predições gravadas, como sensibilidade pré-especificada; hoje as duas fontes de incerteza aparecem separadas.
- Tabela única de transparência no artigo: cada decisão, a data e que dado já tinha sido visto (lacre por etapas, errata do 4a, três versões do script de geração, R4 posterior a 3 casos).
- Busca sistemática de literatura ainda por fazer (`REGISTRO_BUSCA.md`); a "lacuna" do esboço depende dela.
- Dados privados: publicar código, hashes, listas, métricas por modelo, planilhas de auditoria preenchidas e saídas do filtro; guardar todas as edições (API mutável).
- Reinício do contador de tentativas na geração das 150 (25/11) registrado em `DESVIOS.md`.

## Ordem sugerida

1. Agora: script e sementes da produção do E (B5); desvios registrados (B3).
2. Até lacrar o 4b: decidir braço A (A1), detector secundário (A5), comparação de tamanhos do E (A3), bootstrap em dois níveis.
3. Antes do estágio 1: DOI (B1), auditoria dos rótulos do teste (B6).
4. Depois do estágio 1, exploratório: curva de escassez (A2), atribuição com hora do arquivo (A4).
