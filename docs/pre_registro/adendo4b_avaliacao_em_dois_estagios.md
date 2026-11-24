# Adendo 4b — Avaliação do teste em dois estágios, análises de sensibilidade e limites da atribuição

Complementa o adendo 4 (lacrado em 22/11/2026, D52). Onde este texto e o adendo 4 divergirem, vale este, e só nos pontos listados na seção 1. Nenhum resultado de teste foi visto até a redação deste adendo.

## 1. O que este adendo muda no adendo 4

| Ponto | Adendo 4 | Este adendo |
|---|---|---|
| Avaliação do teste (seção 5) | Uma única avaliação, depois de todos os braços incluídos terminarem | Dois estágios, com regras abaixo (seção 3 e 4). Cada modelo é avaliado no teste uma única vez |
| Avaliador | `scripts/avaliar_teste.py` | `scripts/avaliar_teste_v3.py`, que cobre os dois estágios e importa o v2 e o v1 sem alterá-los |
| Controle C | 10 sementes do plano principal (5 na A100, 5 na L4) | Mantém-se como primário. Soma-se uma réplica de hardware: as 5 sementes treinadas na A100 são treinadas de novo na L4 (plano `principalL4`) |
| Análise | Descrita em texto (seção 7) | Implementada em `scripts/analisar_principal_v2.py`, com hash registrado |
| Métricas secundárias (seção 6) | Sem teste de hipótese | Inalterado. Fica explícito que o Holm vale só entre contrastes entre braços (seção 7 do adendo 4) |

O restante do adendo 4 (braços, orçamento de treino, sementes, métrica primária, regra de decisão R contra C, critério de descarte) continua valendo sem alteração.

## 2. Instrumentos fixados (hashes em `docs/pre_registro/hashes.json`)

- Avaliador: `scripts/avaliar_teste_v3.py` (hash em `hashes.json`), que importa `scripts/avaliar_teste_v2.py` (sha256 `fa2e38ea10d2675b93c195ac6d606169bb004dc24217dcdfc5f465c1910cfa4c`) e `scripts/avaliar_teste.py` (sha256 `49d231259bdab4f66e7294c3ed1056d2958c69627d625e5aa85e56b7df6c7a84`) para as medidas, as condições e o lacre. Cobre os dois estágios (`--etapa 1` e `--etapa 2`) e, no split de teste, roda sozinho a verificação das condições do estágio 1 e não avalia se ela falhar. Grava, por modelo, as predições e o gabarito por imagem em `.npz` (no Drive, fora do repositório público) e o SHA-256 delas no CSV de saída.
- Analisador: `scripts/analisar_principal_v2.py`, sha256 `2ef73d55d5e58a9efcc4aad19ae29100afa485fe876b94fe93fde41682e598c1`. Importa as funções estatísticas de `scripts/analisar_principal.py` (sha256 `41a7d577bf96f11c943f48a604c17e3ef3f6a47b2a51e1910a96a0fa019aef0f`).
- **Instrumentos adicionais, escritos, testados e com hash registrado antes do estágio 1** (não podem ser escritos depois de conhecido o resultado de C e R): (i) `verificar_condicoes_etapa1.py`, que confere por código as condições da seção 3 (adendos lacrados, instrumentos com hash, etiquetas, código limpo) e cuja saída é arquivada; (ii) `avaliar_teste_v3.py`, que inclui o estágio 2 (seção 4), ensaiado na validação com lacres de ensaio; (iii) `analisar_hardware.py`, para a sensibilidade da seção 5.2; (iv) `bootstrap_imagens.py`, para a seção 5.7.
- Os instrumentos foram ensaiados na validação: avaliador e analisador v2 com os 20 modelos de C e R (D56, D58, D59; arquivos em `runs/ensaios/`), e o avaliador v3, o analisador de hardware, o bootstrap e o analisador v2 com os 25 modelos (D61; arquivos no Drive). O verificador de condições foi rodado de verdade e lista as pendências.
- Procedimento de medida (adendo 4, seção 5) inalterado: Ultralytics 8.4.165, 640 px, `conf` 0,001, `iou` 0,7, `max_det` 300, lote 16, classe única, modelo `last.pt`.
- A medida primária é o mAP50 da API do Ultralytics. O log de treino não é uma medida: na validação, o mAP50 reavaliado difere do log em até 0,53 pp (D56, D57), e o artigo dirá isso.

## 3. Estágio 1: C e R

**O que é avaliado.** Os 20 modelos de C e R (10 sementes cada) e as 5 réplicas de C na L4 (seção 5.2), 25 modelos numa única execução de `avaliar_teste_v3.py --etapa 1 --split test`. O arquivo de lacre `runs/AVALIACAO_TESTE_LACRE.json` é gravado ao final e impede qualquer segunda avaliação por esse caminho.

**Condições, todas verificadas e registradas em decisão própria antes da execução:**
1. Este adendo (4b) lacrado.
2. O adendo 4a (E) e o adendo do G lacrados, de modo que as regras de E e G estejam fixadas antes de se conhecer o resultado de R no teste. Se um deles não estiver lacrado em 30/12/2026 (Brasília), esse braço sai deste experimento, o estágio 1 prossegue com decisão registrada que dispensa o adendo ausente (como na seção 5 do adendo 4), e o braço só entra por adendo posterior, rotulado como posterior ao resultado de R.
   Consequência de calendário: se o adendo do G não estiver lacrado até 30/12/2026, o estágio 1 só pode rodar a partir de 31/12/2026. Se o 4a e o adendo do G forem lacrados antes, o estágio 1 pode rodar assim que as demais condições valerem.
3. Hashes de todos os instrumentos da seção 2 (avaliadores, analisadores, verificador, bootstrap) registrados e conferidos contra os arquivos do commit avaliado; código sem alterações não commitadas.
4. Todas as execuções de C e R, e as 5 réplicas de C na L4 (confirmadas na L4 pelo registro), registradas em `runs/REGISTRO_EXECUCOES.csv`, com SHA-256 dos pesos conferido e ainda não avaliadas no teste.
5. Etiqueta (tag) de git `lacre-<adendo>` em cada adendo lacrado, apontando para a versão com o hash do lacre, **publicada no GitHub**. O verificador confere a etiqueta no clone local, e a publicação é conferida à mão com `git ls-remote --tags origin`, cuja saída é arquivada na decisão que registra a verificação.

As condições 1 a 5 são conferidas por código (`verificar_condicoes_etapa1.py` e as condições do v1, chamados pelo `avaliar_teste_v3.py`) e a saída da verificação é arquivada em decisão antes do estágio 1. A dispensa de um adendo ausente (condição 2) só é aceita depois de 30/12/2026 (Brasília) e com decisão existente em `DECISOES.md`. O depósito com DOI (Zenodo) dos adendos lacrados é buscado antes do estágio 1; se não for feito, a ausência é declarada no relato. 

**Falha técnica durante o estágio 1.** O CSV é gravado modelo a modelo, e o lacre só ao final. Se a sessão cair no meio, a execução é repetida do início, com os mesmos 25 modelos e o mesmo procedimento. O CSV parcial é guardado, e nada é decidido ou alterado a partir de números de uma execução interrompida. Repetir uma avaliação idêntica por queda técnica não conta como segunda avaliação.

**Análise do estágio 1.** `analisar_principal_v2.py` sobre o CSV do estágio 1, exatamente como no adendo 4: contraste primário R−C no mAP50 da API, t pareado com IC95% (9 gl), TOST/IC90 com margem ±1 pp, Welch e permutação como robustez, e a conclusão pela regra da seção 7 do adendo 4. O pareamento por semente é nominal: no ensaio, a mesma semente treinada em duas máquinas diferiu em média 0,67 pp (dp da diferença), tanto quanto sementes diferentes. O t pareado continua válido (as diferenças por semente são tratadas como independentes), e o t de Welch, sem pareamento, é reportado como robustez.

## 4. Estágio 2: E e G

- Os modelos de E e G (10 sementes cada, se entrarem) são avaliados no mesmo teste, depois de treinados, pelo mesmo `avaliar_teste_v3.py`, com `--etapa 2`, que já está registrado **antes do estágio 1** (seção 2). Ele usa o mesmo procedimento de medida e as mesmas funções, e difere só no arquivo de lacre (`runs/AVALIACAO_TESTE_LACRE_ETAPA2.json`), que exige a existência do lacre do estágio 1.
- **Hardware de E e G.** Os modelos de E e G são treinados na L4, como R e as réplicas de C, e a GPU de cada execução é conferida no registro. Treinar em outra GPU é desvio, registrado em decisão e declarado, e leva a uma sensibilidade análoga à da seção 5.2.
- O resultado do estágio 1 (C e R) é conhecido nessa altura. Para que isso não influencie E e G, valem: (a) o protocolo de geração, seleção, validade e treino de E e G está fixado nos adendos 4a e do G antes do estágio 1; (b) nenhum desses protocolos, nenhuma semente e nenhuma regra de exclusão muda depois do estágio 1; (c) a decisão de um braço entrar ou sair depende só das condições dos seus adendos (contagem e validade das imagens, prazo), nunca de métricas do teste.
- Contrastes do estágio 2: E−C, G−C, E−R, G−R (os que existirem), no mAP50 da API, secundários, com correção de Holm entre eles. A família de Holm é o conjunto de contrastes existentes ao final do estágio 2. O contraste primário continua sendo só R−C.
- **Abandono de braço.** Quem decide se E ou G continuam sabe o resultado de R. Por isso, um braço que satisfaça as condições do seu adendo é treinado e avaliado, e seu resultado é relatado qualquer que seja. Abandonar um braço por motivo que não conste no adendo dele é desvio, registrado em decisão com a data do estágio 1 e declarado no relato.
- Qualquer texto que apresente os resultados de E e G declara que foram avaliados depois de conhecido o resultado de C e R.

## 5. Análises de sensibilidade pré-especificadas (todas sobre as predições gravadas, sem nova avaliação do teste)

Todas são rotuladas sensibilidade. Nenhuma substitui nem muda a conclusão primária, que vale a do conjunto completo de 383 imagens e 10 pares de sementes.

1. **Sobreposição com o histórico do projeto (A1).** Das 383 imagens do teste novo, 72 foram validação e 80 foram teste na divisão antiga (40%) e as decisões das fases anteriores se apoiaram em resultados nelas; as outras 231 eram treino na divisão antiga e nunca foram avaliadas. Reporta-se R−C restrito a essas 231 imagens, com AP50 própria sobre as predições gravadas, pela mesma regra de decisão. A AP50 própria difere da API (no ensaio da validação, em 0,11 pp na diferença R−C), então essa análise é descritiva quanto ao valor absoluto. Esse subconjunto não é uma amostra aleatória do teste: é o que sobrou depois de tirar o que já foi avaliado, e pode diferir em dias e condições. Há **discordância** só quando as duas conclusões forem diferentes entre melhora, piora e equivalente. "Inconclusivo" no subconjunto, por ter menos imagens e mais ruído, é relatado como "sem resolução", não como contradição. Havendo discordância, relatam-se as duas e o artigo não afirma robustez a esse ponto.
2. **Hardware misto (B1).** Cinco sementes de C foram treinadas na A100 e cinco na L4 (D48, D53), e todo o R na L4. As 5 sementes de C da A100 (7, 42, 123, 2024, 31415) são treinadas de novo na L4, com a mesma lista, a mesma configuração e as mesmas sementes (plano `principalL4`, 5 execuções), e as 5 réplicas entram no estágio 1. O contraste primário continua sendo R−C com o C original (10 pares). `analisar_hardware.py` reporta (a) R−C com o controle todo na L4, isto é, a réplica L4 nas 5 sementes replicadas e o C original nas outras 5 (10 pares), e (b) o efeito do hardware em si, réplica L4 menos C original, pareado nas 5 sementes. Se a conclusão com C na L4 diferir da primária, relatam-se as duas. A escolha do contraste primário não muda por causa dessa sensibilidade.
3. **Margem (B2).** A margem de equivalência de ±1 pp foi escolhida como cerca de 1,5 vez o desvio entre sementes observado nos controles (0,6 a 0,7 pp). Não há aqui um valor de efeito mínimo de interesse derivado de uma consequência prática para a Marinha, e isso é uma limitação declarada: a margem foi escolhida conhecendo a variância da validação, e a conclusão de equivalência vale só nessa margem. Mostra-se a conclusão com ±0,5 pp e ±1,5 pp. Na validação, o desvio da diferença pareada foi 0,77 pp, o que dá meia-largura do IC95% de cerca de 0,55 pp com 10 pares: com ±0,5 pp só se concluiria equivalência se a diferença média estimada ficasse abaixo de cerca de 0,05 pp, na prática improvável. Já com ±1 pp, "equivalente" exige diferença média estimada abaixo de cerca de 0,55 pp. Pelo mesmo desvio, com 10 pares o menor efeito detectável com 80% de poder é de cerca de 0,8 pp (estimativa a partir da validação, com incerteza). Diferenças menores que isso podem sair "inconclusivo" ou "equivalente" sem que haja prova de ausência de efeito. Tudo isso é dito no relato, e o resultado com ±0,5 pp pode sair inconclusivo.
4. **Por dia (A2).** R−C descritivo por dia de teste (148, 121 e 114 imagens). Sem IC de generalização. O texto não usa "generaliza".
5. **Secundárias (B5).** Recall de embarcações pequenas (conf 0,25) e AP50 small: diferença e IC95%, sem teste e sem veredito, relatadas mesmo se desfavoráveis a R. A AP50 própria é só verificação de consistência com o mAP50 da API.
6. **Por caixa e por característica.** Análise exploratória das predições dos modelos do estágio 1 (por tamanho, dia, sobreposição com o histórico), rotulada exploratória, sem hipótese pré-especificada e sem efeito sobre a conclusão primária.

7. **Incerteza de amostragem do teste (A2).** Intervalo bootstrap por imagem da diferença R−C na AP50 própria (média sobre as sementes), 10.000 reamostragens das imagens do teste, semente 20261123, intervalo por percentis, por `bootstrap_imagens.py`. É descritivo. Subestima a incerteza, porque imagens do mesmo dia e da mesma sequência são correlacionadas, e com 3 dias não há como reamostrar por dia. Serve para mostrar que o IC por sementes não é toda a incerteza. Regra de leitura fixada agora: a conclusão "equivalente" é escrita sempre como equivalência em relação à variação de treino. Se o intervalo bootstrap não ficar inteiro dentro de ±1 pp, o texto declara que a equivalência não está estabelecida em relação à amostragem das imagens do teste. (Na validação, o intervalo foi de −1,03 a +0,51 pp, e já tocava a margem.)

## 6. Portão e atribuição (A3, B6)

- O teste é de uso único por modelo. A decisão de treinar novos modelos para atribuição (subconjuntos sorteados de R, intervenção nos parâmetros do GenShip, condições do iflens) é posterior ao estágio 1, pode ter sido informada pelo resultado dele, e isso é declarado. Os modelos assim treinados **não são avaliados no teste**. Eles são avaliados só na validação, e os resultados são exploratórios.
- A análise de atribuição que não precisa de treino novo (seção 5, item 6) pode ser feita depois do estágio 1 sobre as predições gravadas, rotulada exploratória.
- Entre os braços C, R, E e G, as diferenças entre fontes confundem domínio, convenção de caixa, contagem de imagens únicas e outros fatores. O texto limita as afirmações a "esta fonte, neste orçamento de treino". Só a intervenção dentro de uma fonte (subconjuntos sorteados, parâmetros sorteados) sustenta linguagem causal, e só como exploratória.
- Uma confirmação do que for achado exige um conjunto de dados novo, que não existe neste experimento.

## 7. O que sempre será relatado

O resultado de R−C no mAP50 qualquer que seja a conclusão (melhora, piora, equivalente, inconclusivo ou sobreposição); as sensibilidades das seções 5.1 a 5.4 mesmo quando contradizem a primária; as secundárias mesmo quando desfavoráveis; que o IC mede só a variação de treino e não a amostragem do teste; que o YOLO11n é o único detector principal, a partir de pesos pré-treinados no COCO (o YOLO26n só vale se verificado conforme o adendo 4); que a qualidade dos rótulos do teste não foi estimada, salvo auditoria posterior relatada sem correção de rótulos.

## 8. Divulgações adicionais (somam-se às da seção 10 do adendo 4)

- A validação das 20 execuções de C e R, e a das 5 réplicas de C na L4 (mAP50 do log e da reavaliação), foram vistas antes deste lacre e usadas para ensaiar avaliador e analisador. A decisão de replicar C na L4 foi tomada antes de se conhecer o resultado das réplicas (D60). Nela, R−C no mAP50 foi −0,13 pp (IC95% de −0,68 a +0,42 pp; "equivalente" com ±1 pp; "inconclusivo" com ±0,5 pp), e o recall small de R ficou 1,09 pp abaixo de C (IC95% de −1,97 a −0,20 pp). A validação foi só monitoramento no treino e não decide nada.
- Uma primeira versão do analisador (D58) tratava as secundárias com veredito e Holm. Foi substituída pela versão atual antes de qualquer avaliação do teste (D59).
- O avaliador v1 (D55) foi registrado antes de eu perceber que as análises por subconjunto exigiam predições por imagem; o v2 o substitui para o teste (D58).
- No ensaio, a mesma semente treinada na A100 e na L4 diferiu em média 0,67 pp, sem efeito médio detectável do hardware (+0,10 pp na reavaliação, IC95% de −0,63 a +0,84 pp, 5 pares). O pareamento por semente é nominal.
- Há 40% de sobreposição entre o teste novo e imagens usadas na história do projeto (seção 5.1), e o teste cobre 3 dias.

## 9. O que este adendo não decide

As regras de validade das edições do E (adendo 4a), as do G (adendo próprio), a seleção das 454 externas do plano reserva, a classificação das condições originais (A21), a calibração da convenção de caixa do G (A19) e o desenho da análise de atribuição com treino novo.
