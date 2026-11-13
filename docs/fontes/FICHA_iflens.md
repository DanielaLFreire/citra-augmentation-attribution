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
