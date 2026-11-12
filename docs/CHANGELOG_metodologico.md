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

