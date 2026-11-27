# Adendo 4d (RASCUNHO, NÃO LACRADO): braço A, aumento clássico offline, e contabilidade de recursos

Estado: rascunho de 2026-11-27, para revisão de Daniela e da orientação. Os pontos em aberto estão marcados com o marcador de pendência, e `scripts/lacrar_adendo.py` recusa lacrar enquanto houver algum. Pelo adendo 4b, este adendo só vale se for lacrado, com etiqueta publicada, **antes do estágio 1** (antes de qualquer avaliação no teste).

## 0. Origem e transparência
- O braço de aumento clássico foi proposto na revisão crítica de 25/11/2026, inicialmente como **controle do E** (separar o efeito do conteúdo gerado do efeito de variar as mesmas fontes).
- Em 27/11/2026 o E não atendeu à regra de uso do 4a §9 (D99) e saiu do experimento principal. **O papel do braço A foi redefinido depois disso**: ele passa a ser o contraste da hipótese barata ("variar as próprias imagens do CITRA com transformações clássicas"), comparada com as fontes caras (R, G e, se voltar, o E).
- Nada nesta redefinição usa o conjunto de teste. Os resultados de validação de C e R (ensaio descritivo, D53 a D60) eram conhecidos quando este texto foi escrito; nenhuma escolha deste adendo (transformações, intensidades, contrastes) é feita a partir deles.

## 1. O braço A
| Braço | Composição | Situação |
|---|---|---|
| A | CITRA ×3 + 1.370 versões transformadas do CITRA de treino, uma por imagem de treino | Secundário, mesmo estatuto do G |

- Mesma composição e mesmo cronograma de treino dos braços com externas do adendo 4 (25% das linhas por época-lista, CITRA ×3 por ciclo, 2 ciclos por época, 25.345 passos), mesmas 10 sementes (adendo 4, seção 4), mesmo YOLO11n, mesma configuração (`configs/treino_yolo11n_d43.yaml`), Ultralytics 8.4.165.
- O aumento online do YOLO (mosaico, HSV, espelhamento, translação, escala) continua ligado, igual em todos os braços. O braço A acrescenta transformações **offline** que o aumento online não faz.
- Fontes: as 1.370 imagens únicas de treino do CITRA (`data/divisao_citra_blocos_dias/divisao_blocos_dias.csv`, D31), uma versão transformada de cada.

## 2. Que transformação cada imagem recebe
- **Condição-alvo de cada fonte = a variação sorteada para ela na produção do E** (`variation_conditions` do registro `AUG_<fonte>.json` da passagem 1, D97), na taxonomia `conditions-citra.yaml` (sha256 `5b6fdf22…8355`): hora do dia (dawn, morning, noon, afternoon, dusk), céu (clear, partly_cloudy, overcast) e atmosfera (clean, haze, light_rain). Para as 274 fontes do estrato de risco vale a mesma regra com `conditions-citra-risk.yaml`.
- Justificativa: a condição de cada fonte já foi sorteada por semente pré-registrada (20261202) antes de qualquer resultado; reusá-la faz o A perseguir **exatamente a mesma variação** que o E perseguiu, de forma barata, e não deixa nenhum grau de liberdade na escolha das condições.
- Só transformações **fotométricas** (cor, brilho, contraste, neblina, chuva, ruído). Nenhuma transformação geométrica: os rótulos do CITRA ficam idênticos, por construção, e o braço A não passa por auditoria de rótulos.
- Tabela de implementação (uma linha por valor da taxonomia, parâmetros fixos, biblioteca e versão fixadas):
  - hora do dia → gama, brilho e temperatura de cor;
  - céu → contraste global e saturação (transformações clássicas não trocam o céu; a limitação é declarada);
  - atmosfera → `clean` sem efeito; `haze` neblina sintética leve; `light_rain` chuva sintética leve; risco: chuva forte e neblina densa.
  - Valores dos parâmetros: DECISÃO PENDENTE (tabela fechada antes de gerar, a partir dos padrões documentados da biblioteca; uma única checagem visual em 20 imagens de treino para confirmar que as embarcações continuam visíveis, sem nenhuma métrica de detecção).
  - Biblioteca e versão: DECISÃO PENDENTE (proposta: Albumentations, versão fixada no `requirements`).
- Semente da parte aleatória das transformações: DECISÃO PENDENTE (proposta: 20261203).
- Script de geração registrado com hash antes de gerar; manifesto com SHA-256 de cada imagem gerada.

## 3. Contrastes
- Primário: **R − C**, inalterado (adendo 4).
- Secundários novos: **A − C** (o aumento barato ajuda?), **R − A** e **G − A** (a fonte cara supera a barata?). Se o E voltar por adendo próprio, **E − A** entra na mesma família.
- Mesma estatística do adendo 4 (mAP50 de teste, diferença pareada por semente, margem de equivalência de ±1,0 pp por TOST com IC90%, IC95% para melhora) e correção de Holm sobre a família inteira de contrastes secundários que existirem (os do adendo 4 mais estes).
- Bootstrap em dois níveis (sementes e imagens do teste), como planejado, para a incerteza do conjunto de teste (383 imagens, 3 dias).

## 4. Regra de recomendação por custo (pré-registrada)
Entre os braços cujo contraste com o melhor braço é equivalente na margem de ±1 pp, recomenda-se o de **menor custo marginal por imagem utilizável** (seção 5). Se nenhum par for equivalente, a recomendação segue o desempenho e o custo é reportado ao lado. A regra só ordena recomendações; não muda nenhum teste.

## 5. Contabilidade de recursos
- Unidades físicas, com o valor em moeda e a data do preço ao lado: GPU-h de treino (registrado em `runs/REGISTRO_EXECUCOES.csv`), tempo de produção dos dados, chamadas e tokens de API (painéis de faturamento do Gemini e do Groq, por modelo e por dia), pessoa-h (auditoria, curadoria, execução).
- Separados: custo fixo (desenvolvimento do pipeline, piloto, filtro) e custo marginal (por imagem produzida e por imagem utilizável).
- Cada número marcado como **medido** ou **estimado** (por exemplo: tempo de auditoria do José, D94, estimado pelo avaliador; o da Daniela, retrospectivo).
- Rendimento por fonte: utilizáveis / produzidas (E: 1.370 devolvidas, utilizáveis 0 no experimento principal, D99).

## 6. YOLO26n (estágio 2)
- Detector secundário, verificado com Ultralytics 8.4.165 (D79). Entra só no estágio 2, com contraste descritivo R − C. DECISÃO PENDENTE (número de sementes e quais braços, e se A − C também entra).

## 7. O que este adendo não muda
Divisão, conjunto de teste, métrica primária, contraste primário, margem de equivalência, as regras dos adendos 4, 4a e 4b e a saída do E do experimento principal (D99).
