# Adendo 4a (RASCUNHO, NÃO LACRADO): fidelidade de rótulos das imagens geradas pelo iflens

Estado: rascunho de 2026-11-18. Contém marcadores "DECISÃO PENDENTE" de propósito: `scripts/lacrar_adendo.py` recusa lacrar enquanto houver algum. Este adendo alimenta o adendo 4 (fontes de aumento): é o "piloto do braço generativo auditado" exigido em `README.md`.

## 1. Pergunta
Qual fração das imagens do CITRA editadas pelo iflens (prompt v1) deixa de preservar os rótulos herdados, e quanto desse problema um filtro automático consegue remover antes do treino?
Não há hipótese de superioridade entre prompts. É um estudo de **caracterização** (estimativa com intervalo), não um teste de hipótese.

## 2. Por que não comparamos prompts de novo
No piloto (30 imagens × 2 prompts, exploratório, avaliadora única), o v1 reprovou 2/30 e o v2 reprovou 10/30 (pareado 0 só v1 / 8 só v2). O v2 não melhorou nada. O v1 é o prompt padrão do fork e foi o ponto de partida, definido antes dos resultados. Um prompt novo só será desenvolvido se a regra do item 9 for acionada. As 30 imagens do piloto ficam como conjunto de desenvolvimento e **não entram** na amostra deste adendo.
Textos e hashes: `prompts/prompt_v1.txt` (5437d06c…4f64) e `prompts/prompt_v2.txt` (e96659f9…423b).

## 3. Instrumento congelado
- Prompt: v1, texto e hash acima. DECISÃO PENDENTE: confirmar que o texto do v1 não muda (versão e hash já registrados).
- Gerador: Gemini `gemini-3.1-flash-lite-image` (Interactions API; sem seed, geração não determinística). Registrar por imagem: modelo solicitado e retornado, `response_id`, hash do prompt, condições sorteadas, hash SHA-256 da saída. DECISÃO PENDENTE: data/hora da janela de geração.
- Classificador das condições originais: Groq `qwen/qwen3.8-27b`, temperatura 0, com cache. DECISÃO PENDENTE: capacidade de classificação (A21, limite diário de 200 mil tokens).
- Código: ramo `reprodutibilidade-condicoes-restritas` do fork, commit DECISÃO PENDENTE (registrar hash do commit).
- Condições: `conditions-citra.yaml` (domínio brasileiro) e o estrato de risco `conditions-citra-risk.yaml` (chuva forte, neblina densa) conforme D19/A07.

## 4. Amostra
- População: imagens do split de **treino** de `labels_final` com pelo menos 1 caixa.
- Excluídas: as 30 imagens do piloto, os quadros em quarentena, imagens usadas no desenvolvimento do prompt.
- Tamanho: 150 imagens (n = 131 para poder de 90% num cenário de comparação; aqui a justificativa é a precisão da estimativa: com 7% de falha, o IC95% de Wilson fica em torno de 4%–12%).
- Sorteio: semente pré-registrada DECISÃO PENDENTE, `random.Random(semente)`, script e lista de saída registrados com hash antes de gerar.
- Dependência entre imagens: quadros do mesmo vídeo/sessão são correlacionados. DECISÃO PENDENTE: 1 imagem por sessão/cluster (como na lista R) ou amostra simples com IC por bootstrap de clusters.
- Estrato de risco: DECISÃO PENDENTE: fração das 150 com condições de risco (sugestão: 20%), analisada em separado.
- Uma geração por imagem (a taxa estimada é por geração).

## 5. Desfecho primário
Imagem **reprovada** se tiver pelo menos uma caixa `apagada`, `deslocada` ou `alterada`, ou uma **embarcação adicionada**. Justificativa: todas as 9 classes do CITRA são embarcações e o experimento usa `labels_single_class`; boia, ave e pessoa adicionadas não corrompem rótulo de detecção e são desfecho secundário (tipo registrado).
Ruído herdado do dataset (`sem_objeto_original`, `original_sem_rotulo`) é contado à parte e não entra na taxa de falha da geração.
Observação de transparência: este critério foi refinado depois do piloto (v3 da auditoria, pós-hoc). Aqui ele é fixado antes dos dados confirmatórios.

## 6. Avaliação
- Dois avaliadores humanos independentes (Daniela e José), cegos entre si e ao parâmetro de geração, com a planilha e as definições do piloto (`INSTRUCOES_avaliador2.md`).
- Concordância entre eles medida primeiro nas 60 folhas do piloto (kappa com IC95% por bootstrap de folhas). DECISÃO PENDENTE: limiar mínimo de kappa por campo e conduta se não for atingido (refinar definições e reavaliar).
- Resolução de discordâncias: DECISÃO PENDENTE (opções: reprovada se qualquer um marcar, "conservadora"; reprovada se ambos marcarem; terceira leitura). Relatar sempre as duas taxas extremas.
- Leitor LLM (família diferente do gerador desejável): usado como terceiro leitor e como filtro; calibrado contra os humanos.

## 7. Filtro automático de qualidade
Objetivo: descartar imagens reprovadas antes do treino, já que a auditoria humana não escala. Validação nas 150: sensibilidade e especificidade com IC95% contra o consenso humano. DECISÃO PENDENTE: limiar mínimo de sensibilidade para usar o filtro no braço E e o que fazer se não for atingido.

## 8. Análise
Taxa de reprovação com IC95% de Wilson (ou bootstrap por cluster); taxa por estrato (padrão e risco); tipos de falha; concordância entre avaliadores; desempenho do filtro. Sem teste de hipótese e sem múltiplas comparações. Regras de α e poder (0,05 bilateral, 90%) ficam para qualquer comparação futura entre prompts.

## 9. Regras de decisão
- Imagens reprovadas (ou sinalizadas pelo filtro) são **descartadas, não regeneradas**; a taxa de descarte é relatada.
- Se a taxa de reprovação do v1 for maior que DECISÃO PENDENTE (sugestão: 15%) ou o descarte inviabilizar o volume do braço E, abre-se um novo ciclo de desenvolvimento de prompt em conjunto de desenvolvimento separado, e um novo adendo.
- O conjunto de teste do CITRA não é usado em nenhuma decisão deste adendo.

## 10. Desvios
Qualquer mudança (amostra, prompt, modelo, critérios) é registrada em `docs/DESVIOS.md` com data e motivo; este documento não é editado depois de lacrado.
