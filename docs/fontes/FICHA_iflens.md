# Ficha da fonte: edições iflens do CITRA (generativa)

Ferramenta: [iflens](https://github.com/Starblessed/iflens), commit `beb5e7d`. Classificação de condições por modelo de visão (Qwen3.6-27b via Groq), sorteio de variação de classes de condição (arquivo YAML), edição pelo Gemini (`gemini-3.1-flash-lite-image` por padrão). Rótulos herdados da imagem original; SAM 3 usado pela equipe só para detectar alucinação e deslocamento.

| Campo | Valor | Quem informou / como foi verificado | Data |
| --- | --- | --- | --- |
| Tipo | Generativa (edição de imagem real) | Código da ferramenta, relatos da equipe | 2026-11-10 |
| Conjunto disponível | **Nenhum utilizável.** Existe só o piloto: 60 originais, 53 edições, 7 falhas de classificação; 36 edições são de imagens do CITRA | Pacotes INPUT/OUTPUT de 2026-08-11 | 2026-11-10 |
| Pacote `iflens.rar` (34.557 JPG, 181 PNG, 21 classes) | **Fora do experimento** (D01) | Dannylo C. Maurício, por mensagem | 2026-11-10 |
| Seed e condições sorteadas por imagem | **Não gravadas** pela ferramenta | Leitura do código | 2026-11-10 |
| Resolução de saída | Altura 768 px fixa; proporção preservada (desvio máx. 0,034% nos 53 pares) | Medido nos pares | 2026-11-10 |
| Splits | Nenhum controle no piloto; o piloto contém imagem em quarentena do CITRA (`29.04.2022-14-59-27`) e rótulo `Quadrado_marcacao(Clone)` | Medido | 2026-11-10 |
| Custo | ~R$ 0,15 por imagem (relato da equipe) | Relatório de atividades | 2026-11-10 |
| Auditoria do piloto | 98 caixas em 36 imagens: 46 válidas e alinhadas, 29 apagadas, 16 sem objeto visível, 6 deslocadas, 1 não avaliável. 22% (C+D) inválidas; pequenos mais afetados | Auditoria visual, um avaliador | 2026-11-10 |
| Arquivos da auditoria | `data/auditoria_piloto_iflens/` | — | — |
| Licença / termos | **desconhecido** (termos de uso do Gemini para treino) | Questionário, comum Q1 | — |

Mudanças propostas na ferramenta antes de qualquer geração nova: gravar condição original, variação sorteada, seed, modelo e data por imagem; instrução explícita de não mover, remover nem adicionar objetos; arquivo de condições restrito.

## Leitura do código (2026-11-13, commit `beb5e7d`)

- Seleção de imagens por `random.choice` sobre uma pasta, sem semente nem lista fixa.
- Classificação por `qwen/qwen3.6-27b` via Groq com `temperature=1`, sem semente; resposta bruta não gravada.
- `get_variation` troca todas as classes de condição de uma vez (exceto as de `KEEP_CLASSES`), sem semente; no exemplo do repositório são `people`, `time_of_day`, `precipitation` (o `planet` fica).
- Prompt base: pede "sem outras mudanças significativas de composição" e lista as descrições das condições; nenhuma instrução de preservar objetos.
- Só o PNG de saída (`AUG_<nome>.png`) é gravado; falhas são impressas e a imagem é pulada; `mime_type` fixo em `image/png`.
- Licença MIT (Dannylo C. Mauricio). Requer Python 3.13+, chaves `GEMINI_API_KEY` e `GROQ_API_KEY`.
- Proposta de alterações enviada ao autor: https://claude.ai/artifact/J64KiEHBYo5wHwaoRmHS1P (sete mudanças, conjunto restrito de condições, registro por imagem, oito perguntas, entre elas se Daniela pode usar a ferramenta ela mesma e sob que autorização e plano de API as imagens do CITRA foram enviadas aos provedores).

## Alterações implementadas e verificação de termos (2026-11-13)

**Alterações no código** (ramo `reprodutibilidade-condicoes-restritas` do clone local; patch e bundle em `docs/fontes/iflens_patch/`; falta fork e pull request, que dependem de Daniela criar o fork): semente mestra obrigatória (`--seed`); sorteio de imagens, classificação (temperatura 0, `seed` do Groq) e variação com semente derivada por imagem (SHA-256, independe da ordem); arquivo `AUG_<nome>.json` por imagem com condições originais e sorteadas, sementes, prompt completo, modelo pedido e retornado, id da resposta, horário e SHA-256 de entrada, saída e arquivo de condições; prompt que proíbe mover, remover, adicionar, redimensionar ou redesenhar objetos e mudar enquadramento; `conditions-citra.yaml` (litoral brasileiro) e `conditions-citra-risk.yaml` (chuva forte e neblina densa, estrato opcional); correção de falha quando o classificador omite uma classe. 5 testes passam. **Limite:** a chamada de edição de imagem não recebe semente, então não é determinística; a reprodutibilidade vem de arquivar as saídas e o registro. Não foi testada contra as APIs reais (sem chaves aqui): o piloto precisa confirmar que `id` e `model` vêm na resposta (o código usa `getattr` e grava `null` se faltarem). A comparação "mesma imagem, mesma semente, duas chamadas" fica para o piloto.

**Versão do modelo (pergunta 6).** `gemini-3.1-flash-lite-image` consta como disponibilidade geral no changelog do Gemini; os modelos de imagem em preview anteriores foram descontinuados com data de desligamento, e os termos proíbem uso de produção de serviços "Preview". Recomendação: manter o id exato fixado (sem alias), gravar `generation_model_returned` e `response_id` por imagem, arquivar toda saída com hash e conferir a página de depreciações antes de gerar. Descontinuação afeta só a regeração, não as imagens já geradas e arquivadas.

**Termos (pergunta 7), lidos em 2026-11-13; não é parecer jurídico.**
- Gemini API: em serviço **pago** (chave em projeto Cloud com faturamento ativo) o Google declara que não usa prompts, imagens e respostas para melhorar produtos, e registra por tempo limitado para detectar violações. Em serviço **não pago**, o Google usa o conteúdo e revisores humanos podem ler, e os termos mandam não enviar informação sensível, confidencial ou pessoal. **Pendente de Daniela:** confirmar que a chave é de projeto com faturamento ativo. Sem isso, não enviar imagens do CITRA.
- Os termos vedam usar o serviço para "desenvolver modelos que compitam com os Serviços". Um detector YOLO de navios não compete com o Gemini; o risco é baixo, mas a leitura é minha, e a decisão sobre o enquadramento cabe à CASNAV/jurídico.
- Groq: a documentação diz que não retém dados de inferência por padrão, com registros de até 30 dias para solução de problemas e abuso, e permite ativar Zero Data Retention nas configurações; fontes secundárias afirmam que o contrato proíbe treino com os dados do cliente. As páginas do próprio Groq divergem sobre a retenção padrão (30 dias na descrição, nenhuma no corpo). Ativar ZDR antes de enviar imagens do CITRA.
- Alternativas se a autorização não vier: (a) enviar só as imagens públicas (R) e usar o braço E em imagens de fonte pública; (b) classificar as condições localmente com modelo aberto (sem envio ao Groq); (c) edição local com modelo aberto, trocando a fonte generativa e registrando o desvio. A autorização para enviar imagens do CITRA ao exterior é decisão da CASNAV, não minha.

**Crédito:** o autor da ferramenta será coautor (Daniela).

**Geografia (D19):** a lista de condições segue a afirmação de Daniela sobre as câmeras (litoral do Rio de Janeiro, Baía de Todos os Santos, Santos). As duas páginas da Marinha que ela citou não puderam ser abertas por mim; registrar a fonte oficial no artigo.

## Teste de fumaça real (2026-11-13, Colab, imagens de exemplo do repositório, não do CITRA)

Ramo `reprodutibilidade-condicoes-restritas` (commit `3b9ca6b`), 3 imagens, semente 42, duas execuções com o código atual (`saida2`, `saida3`).
- Gemini `gemini-3.1-flash-lite-image` (biblioteca `google-genai` 3.3.0, mais nova que a do `pyproject`) respondeu; `response_id` e modelo retornado gravados.
- Groq: `qwen/qwen3.6-27b` **não existe mais** (NotFoundError); o padrão passou a `qwen/qwen3.8-27b`. Um arquivo de 8000×5331 px gerou BadRequest antes de a imagem ser reduzida para a classificação; depois da correção as 3 passaram.
- Reprodutibilidade entre as duas execuções: hash da entrada, sementes, condições originais classificadas, variação e prompt **iguais nas 3 imagens**; a imagem gerada **difere** (a edição não recebe semente), como previsto. Amostra pequena (3 imagens × 2); a classificação com `seed` do Groq é "melhor esforço", não garantia.
- Resolução da saída: área ~1,06–1,07 MP com proporção preservada (desvio ≤ 0,05%): 8000×5331 → 1264×842; 4654×2555 → 1399×768; 3502×3024 → 1112×960. Não é "altura fixa de 768" (isso valia só para a proporção do piloto). Imagens do CITRA em 1920×1080 sairão perto de 1365×768: **decidir antes do treino se as geradas são reamostradas para a resolução original** (caixas normalizadas continuam válidas; o tamanho em pixels dos objetos pequenos muda).
- Não verificado: preservação dos objetos (exige comparação visual com a original).

## Primeiro teste com imagens do CITRA (2026-11-13; 5 imagens de treino, semente 42, prompt v1)

Condições da D21 cumpridas antes do envio: chave do Gemini paga (declarado por Daniela), ZDR global ativo no Groq (tela mostrada por Daniela). Imagens de treino apenas, sem os 3 quadros em quarentena, rótulos `labels_final`. Conferência visual, original × gerada com as caixas desenhadas nas duas (painel enviado por Daniela; as imagens não entram no repositório, que não guarda imagens do CITRA):
- Caixas continuam sobre os objetos em 3 das 5 imagens (07.07 09-26-33, 11.07 15-51-56 com alvos minúsculos difíceis de ver nesta escala, 12.04 13-27-48 com 8 caixas e o texto do casco legível).
- **Objeto novo sem caixa** em 04.05 15-20-13: aparece um navio grande no horizonte à direita; no original não é visível (pode ter sido inventado ou estar escondido pela neblina removida).
- **Objeto novo e embarcação alterada** em 28.06 10-22-39: aparece uma boia sem caixa; o navio dentro da caixa parece outro (cor e aparência diferentes), com fumaça. Conferir ampliando.
- Aderência às condições irregular: a chuva leve é quase invisível na 11.07; o céu "noon/clear" fica saturado e com aspecto de foto de banco de imagens, bem diferente do original neblinoso (deslocamento de domínio a considerar na atribuição).
- Classificação de hora do dia: `afternoon` para os quadros de 09:26 e 10:22 (pelo nome do arquivo; relógio das câmeras não verificado).
Amostra de 5: não estima taxas. Em 2 de 5 houve objeto adicionado (falso negativo no treino se o rótulo for herdado); o piloto anterior tinha 22% de caixas inválidas. **Novo critério de auditoria:** "objeto adicionado sem rótulo", além de apagado, sem objeto, deslocado.
Próximo: prompt v2 (proíbe adicionar objetos e repintar cascos) via `--prompt-file`, mesma semente e mesmas 5 imagens para comparar com o v1; congelar o prompt antes do piloto.
