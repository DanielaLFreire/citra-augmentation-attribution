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
