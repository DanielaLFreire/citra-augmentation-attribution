# Adendo 4d (RASCUNHO, NÃO LACRADO): braço A, aumento clássico offline, e contabilidade de recursos

Estado: rascunho de 2026-11-27, revisão 3 (correções da revisão crítica do mesmo dia e propostas das pendências, aceitas por Daniela; versões anteriores nos commits `c2360ff` e `ddc21c0`). Os pontos em aberto estão marcados com o marcador de pendência, e `scripts/lacrar_adendo.py` recusa lacrar enquanto houver algum. Pelo adendo 4b, este adendo só vale se for lacrado, com etiqueta publicada, **antes do estágio 1** (antes de qualquer avaliação no teste).

## 0. Origem e transparência
- O braço de aumento clássico foi proposto na revisão crítica de 25/11/2026, inicialmente como **controle do E** (separar o efeito do conteúdo gerado do efeito de variar as mesmas fontes).
- Em 27/11/2026 o E não atendeu à regra de uso do 4a §9 (D99) e saiu do experimento principal (D100). **O papel do braço A foi redefinido depois disso**: ele passa a ser o contraste da hipótese barata ("variar as próprias imagens do CITRA com transformações clássicas"), comparada com as fontes caras (R, G e, num estudo posterior, o E corrigido).
- Nada nesta redefinição usa o conjunto de teste. Os resultados de validação de C e R (ensaio descritivo, D53 a D60) eram conhecidos quando este texto foi escrito; nenhuma escolha deste adendo (transformações, intensidades, contrastes, regra de recomendação) é feita a partir deles, e nenhum treino do braço A acontece antes do lacre.

## 1. O braço A
| Braço | Composição | Situação |
|---|---|---|
| A | CITRA ×3 + 1.370 versões transformadas do CITRA de treino, uma por imagem de treino | Secundário, mesmo estatuto do G |

- Mesma composição e mesmo orçamento de treino dos braços com externas (adendo 4, seção 3: 25% das linhas por época-lista, CITRA ×3 por ciclo, 2 ciclos por época, 25.345 passos), mesmas 10 sementes (adendo 4, seção 4), mesmo YOLO11n e modelo inicial, mesma configuração (`configs/treino_yolo11n_d43.yaml`), Ultralytics 8.4.165.
- Fontes: as 1.370 imagens efetivas de treino do CITRA (D31), as mesmas da lista `manifests/lista_elegivel_4a.csv` (1.370 linhas), uma versão transformada de cada.
- Como C e A têm a mesma composição, **a única diferença entre os dois são as transformações offline em 25% das linhas**.
- **Sobreposição com o aumento online.** O aumento online do YOLO continua ligado e igual em todos os braços: brilho (`hsv_v` 0,4), saturação (`hsv_s` 0,7), matiz (`hsv_h` 0,015), espelhamento, translação, escala e mosaico. O braço A não repete essas operações: ele faz **tipos de operação** que o aumento online não faz, que são **balanço de branco por temperatura de cor (modelo de corpo negro), curva de gama (não linear, diferente do ganho linear de `hsv_v`), neblina e chuva sintéticas**. As intensidades da seção 2 são moderadas, porque o objetivo é imitar condições plausíveis do domínio, não deformar a imagem.
- GPU: todas as execuções do A em **L4**, a mesma GPU do R e das 10 sementes do C em L4 (D53, D60). O tipo de GPU de cada execução é registrado.

## 2. Que transformação cada imagem recebe
- Taxonomia: só a **padrão**, `conditions-citra.yaml` (sha256 `5b6fdf22…8355`). Condições de risco (`heavy_rain`, `dense_fog`) **não são usadas**, porque podem esconder embarcações pequenas e deixar caixas sem objeto visível; o A não reproduz o estrato de risco do E, e isso é relatado.
- Dimensões implementadas: **hora do dia** e **atmosfera**. A dimensão **céu** não é implementada: transformações clássicas não trocam céu limpo por encoberto, e qualquer mapeamento seria arbitrário. Limitação declarada.
- **Condição-alvo de cada fonte**, sem novo sorteio:
  - estrato padrão (1.096 fontes): a variação sorteada para ela na produção do E (`variation_conditions` do registro `AUG_<fonte>.json` da passagem 1, D97), campos `time_of_day` e `atmosphere`;
  - estrato de risco (274 fontes): `time_of_day` da variação do E (os valores de risco, `noon` e `afternoon`, já são da taxonomia padrão); `atmosphere` mapeada para o valor padrão mais próximo do mesmo tipo: `heavy_rain` → `light_rain`, `dense_fog` → `haze`.
  - Dependência declarada: a variação do E foi sorteada pela semente 20261202 entre as condições diferentes da condição original, que foi classificada pelo Groq/Qwen. A escolha foi fixada antes de qualquer resultado.
- **Manifesto de condições** (fonte → `time_of_day`, `atmosphere`), gerado dos `AUG_*.json` da passagem 1 e registrado com hash em `hashes.json` **antes** de gerar o A.
- Só transformações **fotométricas**. Nenhuma transformação geométrica: os rótulos do CITRA ficam idênticos. Como as condições de risco ficam de fora, a visibilidade dos objetos é preservada (ver a checagem abaixo), e o A não passa por auditoria de rótulos.
- Tabela de implementação, um conjunto de parâmetros fixo por valor:
  - hora do dia → balanço de branco (ganho por canal) e gama: `dawn` e `dusk` quentes e escuros, `morning` neutro e levemente escuro, `noon` neutro e claro, `afternoon` quente e claro;
  - atmosfera → `clean` sem efeito; `haze` neblina sintética leve; `light_rain` chuva sintética leve.
  - Valores dos parâmetros (Albumentations 2.0.8, todas as transformações com `p = 1`, aplicadas nesta ordem: temperatura de cor, gama, atmosfera):

    | Valor | Temperatura de cor (K; função `planckian_jitter`, `mode="blackbody"`) | Gama (`RandomGamma`, `gamma_limit`; gama = valor ÷ 100, acima de 100 escurece) |
    |---|---|---|
    | `dawn` | 4500 a 5000 | 120 a 140 |
    | `morning` | 5500 a 6000 | 105 a 115 |
    | `noon` | 6000 a 6500 | 80 a 90 |
    | `afternoon` | 5000 a 5500 | 90 a 100 |
    | `dusk` | 4000 a 4500 | 130 a 150 |

    | Valor | Atmosfera |
    |---|---|
    | `clean` | nenhum efeito |
    | `haze` | `RandomFog(fog_coef_range=(0.10, 0.20), alpha_coef=0.08)` (o padrão da biblioteca é 0,3 a 1, denso demais para "neblina leve") |
    | `light_rain` | `RandomRain(rain_type="drizzle", drop_width=1, blur_value=3, brightness_coefficient=0.9, slant_range=(-10, 10))` |

    Critério das faixas: a ordem das temperaturas segue a luz natural (mais quente no nascer e no pôr do sol, neutra ao meio-dia), mas as faixas são **atenuadas**, porque as câmeras do CITRA corrigem o balanço de branco e o modelo de corpo negro aplicado sem essa correção gera dominantes de cor fortes demais (na biblioteca, 3.000 K leva o cinza médio a laranja puro, com o canal azul zerado; o ponto neutro da biblioteca é 6.000 K). A temperatura de cada imagem é sorteada uniformemente na faixa pela semente da imagem e aplicada pela função `planckian_jitter` da biblioteca, porque a classe `PlanckianJitter` exige que a faixa contenha 6.000 K; gama dentro de ±50% do neutro; neblina e chuva no nível "leve" da própria taxonomia (`haze`: "slightly reduced contrast"; `light_rain`: "vessels remain fully visible"). As faixas foram escolhidas antes de qualquer treino do A e sem olhar nenhuma métrica.
  - **Degrau de redução** (único ajuste permitido pela checagem visual): a faixa do efeito em causa passa a ser a metade inferior da faixa original (por exemplo, `haze` de 0,10 a 0,20 para 0,10 a 0,15; gama de `dusk` de 130 a 150 para 130 a 140; temperatura de `dusk` de 4.000 a 4.500 K para 4.250 a 4.500 K, a metade mais próxima do neutro).
  - **Checagem visual, regra fechada:** 20 imagens de treino sorteadas (semente da linha abaixo), uma pergunta só, com resposta sim ou não: "as embarcações com caixa continuam visíveis?". Se a resposta for não em alguma, a única ação permitida é reduzir a intensidade do efeito em causa num degrau já fixado na tabela, uma vez, com registro. Nenhuma métrica de detecção é calculada.
  - Biblioteca e versão: **Albumentations 2.0.8** (licença MIT), fixada no `requirements` do script de geração.
- Aleatoriedade: a semente de cada imagem é derivada da semente mestra e do nome do arquivo (como no iflens), de modo que o resultado não depende da ordem de execução. Semente mestra: **20261203**. Semente de cada imagem: os primeiros 8 bytes do SHA-256 de `"20261203:<nome do arquivo>"`, passada a `A.Compose(..., seed=...)`. A mesma semente mestra sorteia as 20 imagens da checagem visual.
- Script de geração registrado com hash antes de gerar; manifesto de saída com o SHA-256 de cada imagem e a condição aplicada.

## 3. Contrastes
- Primário: **R − C**, inalterado (adendo 4).
- Secundários deste adendo: **A − C** (o aumento barato ajuda?) e **R − A** (a fonte real pública supera a barata?); se o G existir, também **G − A**.
- **Família de Holm** = os contrastes secundários que existirem no estágio 1: A − C e R − A; se o G existir, também G − C, G − R e G − A. Os contrastes com o E do adendo 4 (E − C, E − R) não existem, porque o E saiu (D99).
- Mesma estatística do adendo 4: mAP50 de teste, diferença pareada por semente, margem de equivalência de ±1,0 pp por TOST (IC90%), IC95% para melhora, e a mesma regra de leitura para sobreposição.
- **Referência do C nos contrastes com o A:** as 10 sementes do C em L4 (D53 e D60), para não confundir braço e GPU. O contraste primário R − C segue o adendo 4.
- Bootstrap em dois níveis (sementes e imagens do teste), como planejado, por causa da incerteza do conjunto de teste (383 imagens, 3 dias).
- **Sensibilidade a quadros escuros (D102):** todos os contrastes (o primário e os secundários) são recalculados também sem as imagens do teste com luminância média < 5 (escala 0–255). Descritiva: a análise primária usa as 383 imagens e nada muda de decisão. Na divisão D31 nenhuma imagem de teste fica abaixo do limiar (menor média 79,7; D103), então esta sensibilidade não exclui nenhuma imagem; ela fica registrada para o caso de o teste mudar. No treino efetivo há 3 quadros escuros ou quase escuros (D10, D103), relatados como ruído herdado, iguais em todos os braços.

## 4. Regra de recomendação por custo (pré-registrada)
- Ordem de custo fixada agora, por tipo de fonte: **C ≤ A < R < G**. Os custos medidos (seção 5) são relatados ao lado, mas não mudam a ordem.
- Para cada fonte cara X (R e, se existir, G), aplicada ao contraste X − A:
  - se X − A for **equivalente** (IC90% dentro de ±1 pp): recomenda-se o **A**;
  - se X − A for **superior** (IC95% acima de 0): recomenda-se **X**, com o custo ao lado;
  - se A − X for superior: recomenda-se o **A**;
  - caso contrário: **inconclusivo**, relatado como tal.
- A regra só ordena recomendações; não muda nenhum teste nem nenhuma correção.

## 5. Contabilidade de recursos
- Unidades físicas, com o valor em moeda e a data do preço ao lado: GPU-h de treino (`runs/REGISTRO_EXECUCOES.csv`), tempo de produção dos dados, chamadas e tokens de API (painéis de faturamento do Gemini e do Groq, por modelo e por dia), pessoa-h (auditoria, curadoria, execução).
- Separados: custo fixo (desenvolvimento do pipeline, piloto, filtro) e custo marginal (por imagem produzida e por imagem utilizável).
- Cada número marcado como **medido** ou **estimado** (por exemplo, tempo de auditoria do José, D94, estimado pelo avaliador; o da Daniela, retrospectivo).
- Rendimento por fonte: utilizáveis ÷ produzidas (E: 1.370 devolvidas e 0 utilizáveis no experimento principal, D99; A: 1.370 de 1.370 por construção).

## 6. YOLO26n (estágio 2)
- Definido no adendo 4, seção 4 (3 sementes: 7, 42, 123; Ultralytics 8.4.165, D79). Este adendo só fixa **em quais braços** ele roda: **C, R e A**, com os contrastes descritivos R − C e A − C, sem correção e sem decidir nada. O G não roda com o YOLO26n.

## 7. O que este adendo não muda
Divisão, conjunto de teste, métrica primária, contraste primário, margem de equivalência, as regras dos adendos 4, 4a e 4b e a saída do E do experimento principal (D99, D100).
