# Fontes de aumento para detecção de embarcações pequenas no CITRA-3D-Real

Experimento pré-registrado que compara, com passos de otimização igualados, o efeito de acrescentar ao treino do CITRA-3D-Real (YOLO11n) imagens **reais públicas**, **renderizadas** (simulador GenShip) ou **editadas por IA generativa** (iflens/Gemini), e, para as fontes com efeito detectável, investiga quais características das imagens explicam o ganho ou a perda.

Continua o trabalho das Fases 0–5, fechadas em [synth-detection-attribution](https://github.com/DanielaLFreire/synth-detection-attribution) (tag `v1.1-fase5-fechada`), onde nenhuma fonte externa superou o CITRA puro e os efeitos observados ficaram no tamanho do ruído entre seeds.

**Estado (2026-11-11): planejamento.** Nenhum adendo lacrado, nenhum treino executado. Aguardando respostas das equipes do Genship 3D e do iflens e o piloto de métrica.

## Leitura

| Documento | Para quê |
| --- | --- |
| [`docs/PLANEJAMENTO.md`](docs/PLANEJAMENTO.md) | Pergunta, etapas com portões, dimensionamento, riscos, tarefas |
| [`docs/PROTOCOLO_RIGOR.md`](docs/PROTOCOLO_RIGOR.md) | Regras de pré-registro, dados, treino, análise e rastreabilidade |
| [`docs/DECISOES.md`](docs/DECISOES.md), [`docs/DESVIOS.md`](docs/DESVIOS.md) | Decisões tomadas e abertas; desvios do pré-registro |
| [`docs/CHANGELOG_metodologico.md`](docs/CHANGELOG_metodologico.md) | Diário cronológico |
| [`docs/fontes/`](docs/fontes/) | Ficha de cada fonte de dados (proveniência, licença, lacunas) |
| [`docs/QUESTIONARIO_equipes.md`](docs/QUESTIONARIO_equipes.md) | Perguntas enviadas às equipes |
| [`docs/pre_registro/`](docs/pre_registro/) | Adendos lacrados e `hashes.json` |
| [`docs/artigo/`](docs/artigo/) | Esboço, livro de alegações, figuras e tabelas, checklist |
| [`docs/literatura/`](docs/literatura/) | Registro de buscas e leituras |

## Estrutura

```
docs/        documentação, pré-registro, artigo
data/        só material pequeno e rastreável (auditoria do piloto, dados herdados da Fase 5)
manifests/   manifestos de fontes e listas de treino (CSV com hash)
configs/     configurações de treino e análise
runs/        registro de execuções (uma linha por treino)
results/     saídas agregadas geradas por script
scripts/     lacração, registro de hash, verificação, dimensionamento, perfis
tests/       testes dos scripts
```

Imagens, rótulos brutos e pesos **não** ficam aqui: ficam no Drive do projeto, referenciados por manifesto e hash.

## Checagens

```bash
pip install -r requirements.txt
make check        # testes + verificação de integridade dos hashes
python scripts/dimensionamento_fase5.py data/herdado_fase5   # reproduz as tabelas de dimensionamento
```

## Licença e citação

Código e documentos: MIT (`LICENSE`). Os dados de terceiros mantêm as licenças de origem (ver fichas). Metadados de citação em `CITATION.cff`.
