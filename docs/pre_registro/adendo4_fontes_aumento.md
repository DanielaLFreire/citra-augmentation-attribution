# Adendo 4 — Fontes de aumento: desenho, métricas e regras de decisão

## 1. Pergunta

Qual braço de treino melhora o detector no CITRA-3D-Real (teste privado), em comparação com o controle repetido do CITRA (C)? Em seguida, quais características das imagens explicam o efeito (análise de atribuição, fora deste adendo, desenhada depois dos resultados primários e rotulada como exploratória).

## 2. Braços

| Braço | Conteúdo do treino | Situação |
|---|---|---|
| C | CITRA de treino ×4 (1.370 imagens únicas) | 5 sementes executadas (D48) antes do lacre, sem avaliação no teste; as 5 sementes restantes (seção 4) são treinadas depois do lacre |
| R | CITRA ×3 + 1.370 imagens públicas reais (ABOShips 685 + SMD 685), lista `manifests/lista_R_seed20261121.csv` | Principal deste adendo |
| E | CITRA ×3 + 1.370 edições do iflens/Gemini | Condicional: só treina depois do adendo 4a lacrado e com ≥ 1.370 edições válidas |
| G | CITRA ×3 + 1.370 renderizações do GenShip com `.json` | Condicional: entra só se o João entregar ≥ 1.370 imagens distintas até 30/12/2026 (D24); caso contrário sai deste experimento e só entra por adendo posterior |

Os braços E e G não são lacrados em detalhe aqui. Qualquer treino com E ou G exige o seu adendo específico lacrado antes (4a para E).

## 3. Orçamento de treino (igual entre braços)

- Lote 16; época = 10.960 linhas de lista = 685 passos; 37 épocas = **25.345 passos** (D35, D43).
- Braços com externas: 25% das linhas (1.370 por época-lista); CITRA ×3 por ciclo, 2 ciclos por época.
- Plano reserva (D36): se E tiver menos de 1.370 edições válidas ao fim de 30/12/2026 (Brasília), vale o desenho com 454 externas e 222 épocas, para E e, por igualdade de desenho, para os demais braços externos comparados com E. O C e o R seriam repetidos nesse desenho. Esta regra só afeta comparações que incluam E.
- Configuração: `configs/treino_yolo11n_d43.yaml` (hash em `hashes.json`; AdamW lr0 0,001, `cos_lr`, aquecimento 500 passos, `close_mosaic` 2, `patience` 100, 640 px). Ultralytics 8.4.165.
- Modelo inicial `yolo11n.pt` (sha256 0ebbc80d…), o mesmo em todos os braços.

## 4. Detectores e sementes

- Primário: YOLO11n, **10 sementes** em todos os braços: 7, 42, 123, 2024, 31415 (as cinco do C já treinado) e 101, 1001, 2025, 4242, 27182. Fixadas aqui; não há troca nem exclusão de semente depois de ver resultados.
- Razão do N = 10: com 5 sementes e o desvio entre sementes do C na validação nova (0,67 pp), a meia-largura do IC95% da diferença seria cerca de 0,8 pp (sementes pareando de fato) a 1,2 pp (sem pareamento real); com 10 fica entre cerca de 0,5 e 0,7 pp, o que torna possível concluir equivalência de ±1 pp. O desvio no teste pode diferir do medido na validação.
- Secundário: YOLO26n, 3 sementes (7, 42, 123), apenas se a versão fixada do Ultralytics o suportar com o mesmo otimizador; senão, não entra e isso é registrado, sem substituição por outro detector.

## 5. Dados e avaliação

- Divisão: `data/divisao_citra_blocos_dias/divisao_blocos_dias.csv` (D31): treino 1.370 efetivas, validação 325, **teste 383 imagens em 3 dias**.
- O modelo avaliado é sempre o **último checkpoint** (`last.pt`), sem escolha por validação.
- A validação serve só para monitorar o treino.
- **O teste é avaliado uma única vez**, com a lista de modelos fixada (todas as execuções do plano principal registradas em `runs/REGISTRO_EXECUCOES.csv`), **somente depois** de (i) todas as execuções dos braços incluídos terem terminado e (ii) o adendo 4a ter sido lacrado, mesmo que o E acabe não entrando. Assim, nenhuma escolha sobre E ou G pode ser influenciada pelo resultado de R no teste. Se o 4a não for lacrado até 30/12/2026, o E sai do experimento e C e R podem ser avaliados, com o E ficando para adendo posterior rotulado como posterior ao resultado.
- **Procedimento de avaliação fixado:** Ultralytics 8.4.165, `val` no split de teste, 640 px, `conf` 0,001, `iou` 0,7, `max_det` 300, lote 16, classe única; mAP50 = AP com IoU 0,5 da API do Ultralytics. Recall small: caixas com área < 32² px no tamanho de 640, confiança 0,25, IoU 0,5. O script (`scripts/avaliar_teste.py`) será escrito e testado em validação e seu hash registrado antes de qualquer avaliação no teste.
- **Alcance da inferência:** o IC da seção 7 mede apenas a variação de treino (sementes). Não inclui a incerteza de amostragem do conjunto de teste (383 imagens em 3 dias, com imagens correlacionadas no mesmo dia). O resultado vale para esses 3 dias e não prova generalização para outras condições.

## 6. Métricas

- **Primária: mAP50 no teste** (decisão A01, 2026-11-21; menor variância entre sementes na Fase 5: dp 0,59 pp).
- Secundárias: recall de embarcações pequenas com confiança 0,25; AP50 small. Reportadas sem teste de hipótese e sem alterar a conclusão primária.
- Nenhuma métrica é trocada depois de ver resultados do teste.

## 7. Regra de decisão (R contra C, único contraste primário)

- Estatística: diferença pareada por semente, Δ = mAP50(R) − mAP50(C), com 10 pares. O pareamento é nominal (a semente fixa inicialização e ordem, mas as listas diferem); o teste t pareado continua válido, só pode ser menos eficiente que o ideal. Como verificação de robustez, reporta-se também o teste de permutação e a diferença de médias com t de Welch; a conclusão vale a do t pareado.
- Intervalo de confiança de 95% pela t de Student com 9 graus de liberdade.
- Margem de equivalência: ±1,0 ponto percentual (TOST, α = 0,05, equivalente a IC de 90% dentro de ±1 pp).
- Conclusões possíveis, fixadas de antemão:
  - **R melhora**: IC95% inteiro acima de 0.
  - **R piora**: IC95% inteiro abaixo de 0.
  - **Equivalente**: IC90% inteiro dentro de ±1 pp.
  - **Inconclusivo**: nenhum dos anteriores. Reportado como inconclusivo, sem acrescentar sementes depois de ver o teste.
  - **Sobreposição**: se o IC95% ficar acima de 0 e o IC90% dentro de ±1 pp, reporta-se "melhora estatística, equivalente na margem de ±1 pp", sem escolher só uma das duas leituras.
  - Efeito mínimo detectável aproximado com 10 sementes: 0,5 a 0,7 pp (seção 4); efeitos menores não serão afirmados.
- Contrastes secundários (E−C, G−C, E−R, G−R), se existirem: mesma estatística, correção de Holm entre eles, rotulados secundários.

## 8. Critério de descarte e desvios

- Uma execução só é refeita por falha técnica **antes** da última época (queda do Colab, erro de código, divergência numérica com NaN), com a mesma semente e a mesma configuração; a original fica documentada em `DECISOES.md`.
- Execução concluída nunca é descartada por causa do resultado.
- Qualquer desvio deste adendo é registrado como decisão nova em `docs/DECISOES.md`, antes de ser aplicado, e citado em qualquer relato dos resultados.

## 9. Lista de execuções e artefatos fixados

- Lista de treino C: `manifests/lista_treino_C.csv`; lista de treino R: `manifests/lista_treino_R.csv`; lista das externas R: `manifests/lista_R_seed20261121.csv`; exclusão `manifests/exclusao_R_A13.csv`; divisão e configuração acima. Os hashes estão em `docs/pre_registro/hashes.json`.
- Plano principal: C (5 sementes, concluído), R (5 sementes), mais E e G se as condições da seção 2 forem satisfeitas.
- Identificação: `{braço}_{plano}_{modelo}_seed{semente}`; todas registradas em `runs/REGISTRO_EXECUCOES.csv` com commit do código, hashes e versões.

## 10. Divulgações de transparência

- Os resultados de validação das 5 sementes do C no plano principal (média 0,630, dp 0,0067) foram vistos antes deste lacre (D48). Nenhum resultado de teste foi visto.
- A escolha da métrica primária (A01) usou a variância entre sementes dos modelos de controle da Fase 5 (validação, divisão antiga), registrada em `docs/PLANEJAMENTO.md`, e não um piloto novo selado; o `README.md` do pré-registro previa o piloto antes do lacre. Declara-se aqui como desvio consciente: a métrica foi escolhida sem ver nenhum braço novo, e a decisão está na D50.
- O `README.md` também previa manifestos de todas as fontes antes do lacre. Esta versão lacra por etapas (D50): E e G ficam condicionais e têm adendo próprio.

## 11. O que este adendo não decide

Regras de validade das edições do E (4a), seleção das 454 externas do plano reserva, classificação das condições originais (A21), calibração da convenção de caixa do G (A19) e a análise de atribuição.
