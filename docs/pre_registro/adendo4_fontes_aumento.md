# Adendo 4 — Fontes de aumento: desenho, métricas e regras de decisão

Estado: RASCUNHO aguardando aprovação de Daniela (remover esta linha antes de lacrar).

## 1. Pergunta

Qual braço de treino melhora o detector no CITRA-3D-Real (teste privado), em comparação com o controle repetido do CITRA (C)? Em seguida, quais características das imagens explicam o efeito (análise de atribuição, fora deste adendo, desenhada depois dos resultados primários e rotulada como exploratória).

## 2. Braços

| Braço | Conteúdo do treino | Situação |
|---|---|---|
| C | CITRA de treino ×4 (1.370 imagens únicas) | Executado (D48), 5 sementes, antes do lacre; nenhum resultado de teste |
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

- Primário: YOLO11n, sementes 7, 42, 123, 2024, 31415 em todos os braços (as mesmas sementes pareiam os braços).
- Secundário: YOLO26n, 3 sementes (7, 42, 123), apenas se a versão fixada do Ultralytics o suportar com o mesmo otimizador; senão, não entra e isso é registrado, sem substituição por outro detector.

## 5. Dados e avaliação

- Divisão: `data/divisao_citra_blocos_dias/divisao_blocos_dias.csv` (D31): treino 1.370 efetivas, validação 325, **teste 383 imagens em 3 dias**.
- O modelo avaliado é sempre o **último checkpoint** (`last.pt`), sem escolha por validação.
- A validação serve só para monitorar o treino. O teste é avaliado **uma vez**, com a lista de modelos fixada: todas as execuções do plano principal registradas em `runs/REGISTRO_EXECUCOES.csv`, depois do fim de todas elas.
- Limitação declarada: o teste cobre 3 dias; o resultado vale para esses dias e não prova generalização para outras condições.

## 6. Métricas

- **Primária: mAP50 no teste** (decisão A01, 2026-11-21; menor variância entre sementes na Fase 5: dp 0,59 pp).
- Secundárias: recall de embarcações pequenas com confiança 0,25; AP50 small. Reportadas sem teste de hipótese e sem alterar a conclusão primária.
- Nenhuma métrica é trocada depois de ver resultados do teste.

## 7. Regra de decisão (R contra C, único contraste primário)

- Estatística: diferença pareada por semente, Δ = mAP50(R) − mAP50(C), com 5 pares.
- Intervalo de confiança de 95% pela t de Student com 4 graus de liberdade.
- Margem de equivalência: ±1,0 ponto percentual (TOST, α = 0,05, equivalente a IC de 90% dentro de ±1 pp).
- Conclusões possíveis, fixadas de antemão:
  - **R melhora**: IC95% inteiro acima de 0.
  - **R piora**: IC95% inteiro abaixo de 0.
  - **Equivalente**: IC90% inteiro dentro de ±1 pp.
  - **Inconclusivo**: nenhum dos anteriores. Com 5 sementes e desvio da diferença pareada ≳ 0,7 pp, o IC pode ser largo demais para concluir equivalência; esse resultado será reportado como inconclusivo, sem acrescentar sementes depois de ver o teste.
- Contrastes secundários (E−C, G−C, E−R, G−R), se existirem: mesma estatística, correção de Holm entre eles, rotulados secundários.

## 8. Critério de descarte e desvios

- Uma execução só é refeita por falha técnica **antes** da última época (queda do Colab, erro de código, divergência numérica com NaN), com a mesma semente e a mesma configuração; a original fica documentada em `DECISOES.md`.
- Execução concluída nunca é descartada por causa do resultado.
- Qualquer desvio deste adendo é registrado como decisão nova em `docs/DECISOES.md`, antes de ser aplicado, e citado em qualquer relato dos resultados.

## 9. Lista de execuções e artefatos fixados

- Lista de treino C: `manifests/lista_treino_C.csv`; lista de treino R: `manifests/lista_treino_R.csv`; lista das externas R: `manifests/lista_R_seed20261121.csv`; exclusão `manifests/exclusao_R_A13.csv`; divisão e configuração acima. Os hashes estão em `docs/pre_registro/hashes.json`.
- Plano principal: C (5 sementes, concluído), R (5 sementes), mais E e G se as condições da seção 2 forem satisfeitas.
- Identificação: `{braço}_{plano}_{modelo}_seed{semente}`; todas registradas em `runs/REGISTRO_EXECUCOES.csv` com commit do código, hashes e versões.

## 10. O que este adendo não decide

Regras de validade das edições do E (4a), seleção das 454 externas do plano reserva, classificação das condições originais (A21), calibração da convenção de caixa do G (A19) e a análise de atribuição.
