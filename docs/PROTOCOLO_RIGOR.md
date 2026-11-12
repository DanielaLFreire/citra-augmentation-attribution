# Protocolo de rigor

Regras que valem para todo o repositório. Herdam as do repositório das Fases 0–5
([synth-detection-attribution](https://github.com/DanielaLFreire/synth-detection-attribution), tag `v1.1-fase5-fechada`) e as ampliam para este experimento.
Quem as quebrar precisa registrar o desvio em `docs/DESVIOS.md`.

## 1. Pré-registro antes de dados

1. Nenhum treino que entre numa conclusão começa antes de o adendo de pré-registro estar **lacrado** (SHA-256 em `docs/pre_registro/hashes.json`, commit público).
2. O adendo fixa: braços, fatores, métrica primária e secundárias, número de seeds, orçamento de passos, regra de decisão, critério de descarte de imagens, lista de execuções.
3. Mudança depois de lacrado = adendo novo. Adendo não é editado nem re-lacrado.
4. Toda análise feita *depois* de ver resultados é rotulada **post hoc** no texto e na tabela de alegações.

## 2. Dados

1. Imagens, rótulos brutos e pesos ficam no armazenamento do projeto (Drive), nunca neste repositório. Aqui entram **manifestos** (uma linha por imagem: id, origem, split de origem, hash do arquivo, parâmetros de geração) e seus SHA-256.
2. Todo manifesto usado em treino tem o hash registrado (`scripts/registrar_artefato.py`) **antes** do primeiro treino que o usa.
3. Cada fonte tem uma ficha em `docs/fontes/` com proveniência, licença, o que se sabe e o que não se sabe. Campo desconhecido fica escrito como desconhecido.
4. Val e test do CITRA-3D-Real nunca entram em treino, nem como original de edição generativa. Verificação por hash de conteúdo, não por nome.
5. Rótulos de imagens de aumento vêm da origem (público, simulador ou herdados da original). **Nenhuma caixa é criada por um detector treinado no CITRA**; isso tornaria a avaliação circular.

## 3. Treino e avaliação

1. Protocolo V2 herdado: YOLO11n, AdamW, 640 px, lote 16, checkpoint fixo `last.pt`, sem parada antecipada, passos de otimização iguais entre braços e comprimento de lista fixo.
2. Seeds: lista fixa no adendo; mesmas seeds em todos os braços (bloco por seed). Todas as seeds executadas são reportadas, inclusive as ruins.
3. Piso de ruído da Fase 1 (~2 pp de recall) e o desvio medido na Fase 5 orientam o dimensionamento (`scripts/dimensionamento_fase5.py`).
4. Teste avaliado **uma vez**, com a guarda de avaliação única herdada, sobre lista de modelos fixada no adendo.
5. Cada execução é uma linha em `runs/REGISTRO_EXECUCOES.csv`: braço, seed, commit do código, hash do manifesto, hash da configuração, versão de bibliotecas, GPU, duração, caminho dos pesos, hash dos pesos.

## 4. Análise

1. Estatística conforme o adendo: diferença pareada por seed, IC de 95%, equivalência por TOST com margem declarada. Sem valor-p solto.
2. Múltiplas métricas: uma primária; as demais são secundárias e declaradas como tal.
3. Resultado nulo ou negativo é resultado. Entra no artigo com o mesmo destaque.
4. Figuras e tabelas do artigo são geradas por script a partir de `results/` (ver `docs/artigo/FIGURAS_TABELAS.csv`); nenhuma é editada à mão.

## 5. Rastreabilidade do texto

1. Cada número do artigo aponta para uma linha em `docs/artigo/LIVRO_DE_ALEGACOES.csv`: alegação, evidência (arquivo + commit), status (`pre-registrado`, `exploratório`, `post hoc`), limitações.
2. Literatura: `docs/literatura/REGISTRO_BUSCA.md` guarda as buscas feitas, as datas, os critérios e o que foi lido por inteiro ou só por resumo. Afirmação de novidade só com busca sistemática registrada.
3. Decisões de projeto vão para `docs/DECISOES.md` (uma entrada por decisão, com data, alternativas e motivo). O diário cronológico fica em `docs/CHANGELOG_metodologico.md`.

## 6. Auditoria de rótulos de imagens geradas

Ver `docs/PLANEJAMENTO.md` (seção sobre o braço generativo). Resumo: rótulos herdados, triagem automática com SAM 3, auditoria manual de todas as caixas, amostra com segundo avaliador para medir concordância, descarte da imagem inteira se qualquer caixa for reprovada. Taxas de descarte por condição e por tamanho entram no artigo.

## 7. Integridade

`python -m scripts.verificar_integridade` confere os hashes de `docs/pre_registro/hashes.json` contra os arquivos do repositório. Roda na integração contínua e antes de cada lacração.
