# Adendo 4a (RASCUNHO, NÃO LACRADO): fidelidade de rótulos das imagens geradas pelo iflens

Estado: rascunho revisado em 2026-11-24 (revisão crítica: taxa primária única, filtro com desenvolvimento e validação separados, protocolo de produção do E, calendário). Sem itens abertos, falta a revisão de Daniela para lacrar (`scripts/lacrar_adendo.py` recusa lacrar enquanto houver algum marcador de pendência no texto). Este adendo alimenta o adendo 4 (fontes de aumento): é o "piloto do braço generativo auditado" exigido em `README.md`.

## 1. Pergunta
Qual fração das imagens do CITRA editadas pelo iflens (prompt v1) deixa de preservar os rótulos herdados, e quanto desse problema um filtro automático consegue remover antes do treino?
Não há hipótese de superioridade entre prompts. É um estudo de **caracterização** (estimativa com intervalo), não um teste de hipótese.

## 2. Por que não comparamos prompts de novo
No piloto (30 imagens × 2 prompts, exploratório, avaliadora única), o v1 reprovou 2/30 e o v2 reprovou 10/30 (pareado 0 só v1 / 8 só v2). O v2 não melhorou nada. O v1 é o prompt padrão do fork e foi o ponto de partida, definido antes dos resultados. Um prompt novo só será desenvolvido se a regra do item 9 for acionada. As 30 imagens do piloto ficam como conjunto de desenvolvimento e **não entram** na amostra deste adendo.
Textos e hashes: `prompts/prompt_v1.txt` (5437d06c…4f64) e `prompts/prompt_v2.txt` (e96659f9…423b).

## 3. Instrumento congelado
- Prompt: v1, texto e hash acima. O texto do v1 não muda (versão e hash já registrados; decisão de Daniela em 24/11/2026).
- Gerador: Gemini `gemini-3.1-flash-lite-image` (Interactions API; sem seed, geração não determinística). Registrar por imagem: modelo solicitado e retornado (o identificador retornado deve ser o mesmo na amostra de 150 e na produção do E; se mudar, a geração para, o fato vai a `docs/DESVIOS.md`, e as imagens com identificador diferente do da amostra não entram no E), `response_id`, hash do prompt, condições sorteadas, hash SHA-256 da saída. Janela de geração: depois do lacre deste adendo e do registro da lista sorteada, e até 20/12/2026 (Brasília), para sobrar prazo antes de 30/12/2026. A data e a hora de cada geração ficam no registro por imagem.
- Classificador das condições originais: Groq `qwen/qwen3.8-27b`, temperatura 0, com cache. Capacidade (A21): plano pago do Groq, sem o limite diário de 200 mil tokens do plano gratuito (decisão de Daniela em 24/11/2026). O modelo retornado e a data de cada chamada ficam no registro por imagem, e a classificação roda antes da geração, dentro da janela acima.
- Código: ramo `reprodutibilidade-condicoes-restritas` do fork, fixado no commit `0bd983f30ecabd8aa1d1682faafe318e1d096e4c` (16/11/2026, "Add --classification-cache: reuse a stored classification instead of calling the vision API again"), lido na branch pública `DanielaLFreire/iflens` em 24/11/2026. A geração usa esse commit por checkout do hash, e commits posteriores do ramo não valem.
- Condições: `conditions-citra.yaml` (domínio brasileiro) e o estrato de risco `conditions-citra-risk.yaml` (chuva forte, neblina densa) conforme D19/A07.

## 4. Amostra
- População: imagens do split de **treino da divisão em blocos de dias** (D16/D23), lista congelada em `data/divisao_citra_blocos_dias/divisao_blocos_dias.csv` (sha256 `1e7674fdef8dff8413e93f7e9562d830dfe792dd85d35fe9033282e4e2e3bea9`), com pelo menos 1 caixa. O script de sorteio grava a lista elegível e o hash dela antes de sortear.
- Excluídas: as 30 imagens do piloto, os quadros em quarentena, imagens usadas no desenvolvimento do prompt.
- Tamanho: 150 imagens (n = 131 para poder de 90% num cenário de comparação; aqui a justificativa é a precisão da estimativa da taxa primária, que é a de "qualquer avaliador" (seção 5). Com 150 imagens, o IC95% de Wilson para 20% observados (30/150, como no piloto com dois avaliadores) é 14,4%–27,1%, e para 6,7% (10/150) é 3,7%–11,8%. Com essa precisão, o limiar de 15% separa os dois cenários, mas uma taxa observada entre cerca de 11% e 19% deixará o IC cruzando o limiar, e isso será dito).
- Sorteio: semente pré-registrada 20261201, `random.Random(semente)`, script e lista de saída registrados com hash antes de gerar.
- Dependência entre imagens: quadros do mesmo vídeo/sessão são correlacionados. 1 imagem por bloco. O CITRA não tem identificador de sessão, então define-se bloco como a data, a hora e a dezena de minutos do nome do arquivo (`DD.MM.AAAA-HH-MM-SS`, dezena = minuto dividido por 10). A divisão de treino tem 293 blocos, 89 combinações de data e hora, e 20 dias. O sorteio escolhe 150 blocos entre os que têm pelo menos 1 imagem elegível, e 1 imagem em cada. Se houver menos de 150 blocos elegíveis, usa-se 1 imagem em todos eles e o restante é sorteado sem restrição. O bloco de 10 minutos é uma hipótese de trabalho para reduzir quase-duplicatas, não uma medida de independência, e a análise reporta também o IC por bootstrap de blocos.
- Estrato de risco: 20% das 150 (30 imagens) com condições de risco, analisadas em separado. A taxa primária é a global das 150 (80% padrão, 20% risco), a mesma proporção usada na produção do E (seção 10), para que a taxa medida se aplique ao E.
- Uma geração por imagem (a taxa estimada é por geração).

## 5. Desfecho primário
Definições completas em `data/auditoria_piloto_iflens/DEFINICOES_auditoria_v4.md` (inclui a categoria `degradada` e o teste prático da caixa `apagada`). Imagem **reprovada** se tiver pelo menos uma caixa `apagada`, `deslocada` ou `alterada` (outro objeto; nitidez sozinha não conta), ou uma **embarcação adicionada**. Secundário: `degradada`; sensibilidade contando `degradada` como falha. Justificativa: todas as 9 classes do CITRA são embarcações e o experimento usa `labels_single_class`; boia, ave e pessoa adicionadas não corrompem rótulo de detecção e são desfecho secundário (tipo registrado).
Ruído herdado do dataset (`sem_objeto_original`, `original_sem_rotulo`) é contado à parte e não entra na taxa de falha da geração.
Observação de transparência: este critério foi refinado depois do piloto (v3 da auditoria, pós-hoc). Aqui ele é fixado antes dos dados confirmatórios.

## 6. Avaliação
- Dois avaliadores humanos independentes (Daniela e José; Daniela informou em 24/11/2026 que José avaliará), cegos entre si e ao parâmetro de geração, com a planilha e as definições do piloto (`INSTRUCOES_avaliador2.md`).
- Concordância medida primeiro nas 60 folhas do piloto: objeto adicionado kappa 0,85; original sem rótulo 0,52; caixa 0,27 (6 categorias), por definição ambígua de `alterada`. Definições refinadas (v4) e as caixas divergentes reavaliadas por cada um sem ver a resposta do outro. Resultado da reavaliação (D33): imagem reprovada kappa 0,86 (IC95% 0,69–1,00); caixa em 6 categorias 0,44 (0,29–0,57). Limiar: kappa de pelo menos 0,60 no campo imagem reprovada para prosseguir. Se não for atingido, discutem-se as definições e as duas avaliações são refeitas sem ver a resposta do outro, relatando o kappa antes e depois. Se continuar abaixo, o desfecho primário continua sendo "qualquer avaliador" (seção 5) e relatam-se as duas taxas e o kappa; a decisão do limiar da seção 9 usa só a primária.
- Resolução de discordâncias: primário = reprovada se **qualquer** avaliador marcar; sensibilidade = só se ambos marcarem; relatar as duas taxas (no piloto, com os dois avaliadores, v1: 6/30 contra 2/30; v2: 13/30 contra 10/30).
- Leitor LLM (família diferente do gerador desejável): usado apenas como filtro (seção 7), nunca como avaliador nem como terceiro leitor. O padrão de referência é sempre humano.

## 7. Filtro automático de qualidade
Objetivo: descartar imagens reprovadas antes do treino, já que a auditoria humana não escala.
- **Padrão de referência:** "reprovada por qualquer avaliador humano", a mesma definição do desfecho primário. O LLM não entra na referência, para o filtro não ser avaliado contra si mesmo. A concordância com o consenso (ambos) é reportada como descritiva.
- **Desenvolvimento e validação separados:** o filtro (modelo, prompt e limiar de pontuação) é ajustado só nas imagens do piloto (30 imagens × 2 prompts, já auditadas, seção 2) e depois **congelado e registrado com hash** em `docs/pre_registro/hashes.json` antes de ser aplicado às 150 e antes de a saída dele ser cruzada com as avaliações humanas das 150. Não há ajuste depois disso.
- **Validação nas 150:** sensibilidade e especificidade com IC95% de Wilson, sempre acompanhadas do número de positivos de referência. Limiar: **sensibilidade estimada (pontual) de pelo menos 80%**. Com poucos positivos o IC é largo (por exemplo, 80% com 20 positivos tem IC95% de 58% a 92%), e a decisão vale só para este protocolo, sem generalização a outras amostras ou modelos.
- Se o limiar não for atingido, o filtro não é usado como critério de descarte, e o braço E só pode ser formado por novo adendo que declare o risco de rótulos não verificados.
- Relatar também a fração de imagens boas descartadas pelo filtro (1 − especificidade), porque ela define o volume que sobra para o E.

## 8. Análise
Taxa de reprovação com IC95% de Wilson (ou bootstrap por cluster); taxa por estrato (padrão e risco); tipos de falha; concordância entre avaliadores; desempenho do filtro. Sem teste de hipótese e sem múltiplas comparações. Regras de α e poder (0,05 bilateral, 90%) ficam para qualquer comparação futura entre prompts.

## 9. Regras de decisão
- Imagens reprovadas (ou sinalizadas pelo filtro) são **descartadas, não regeneradas**; a taxa de descarte é relatada.
- Se a taxa primária (seção 5: "qualquer avaliador", global nas 150 imagens, estimativa pontual com IC95% de Wilson reportado) for maior que 15%, abre-se um novo ciclo de desenvolvimento de prompt em conjunto de desenvolvimento separado, e um novo adendo, e o braço E não treina com o prompt v1. A taxa por consenso e a taxa por estrato são descritivas e não entram nessa regra.
- Volume insuficiente do E (menos de 1.370 edições válidas) **não** abre novo ciclo de prompt: aplica-se o plano reserva da D36, na forma da seção 10.
- O conjunto de teste do CITRA não é usado em nenhuma decisão deste adendo.

## 10. Produção do braço E (protocolo fixado antes da geração)
Esta seção fixa o que o adendo 4 (linha 81) e a D36 deixaram para o 4a: a escolha das fontes, o volume, a regra de validade e a seleção das 454 do plano reserva.
- **Fontes:** imagens do treino efetivo (1.370, D35) com pelo menos 1 caixa em `labels_final`, na lista elegível da seção 4. A lista e o hash dela são gravados antes de qualquer sorteio. As imagens do piloto podem ser fontes. As edições geradas para a amostra de auditoria de 150 **não entram** no E, para que a taxa auditada e o E sejam produtos de gerações separadas.
- **Ordem e volume:** a ordem das fontes é um sorteio sem reposição da lista elegível, com semente pré-registrada 20261202. **Passagem 1:** 1 geração por fonte, nessa ordem. **Passagem 2:** só se, ao fim da passagem 1, houver menos de 1.370 válidas, e então 1 geração a mais por fonte, na mesma ordem, com nova condição sorteada. No máximo 2 gerações por fonte, e as duas edições de uma mesma fonte podem entrar no E. Consequência declarada: o E pode ter menos fontes distintas que o R, que tem 1.370 imagens distintas.
- **Condições:** sorteadas por geração, com a proporção 80% padrão e 20% risco, pela lista de sementes registrada antes de gerar. Relata-se a proporção efetiva entre as edições que entram no E, que o filtro pode alterar.
- **Edição válida** se todas as condições valem: (i) a API devolveu uma imagem, com o identificador de modelo da seção 3; (ii) o hash SHA-256 da saída não repete o de outra edição; (iii) o filtro congelado (seção 7), se aprovado, não a sinalizou; (iv) os rótulos são os da imagem de origem, sem alteração. Bloqueio da API por política de conteúdo conta como não válida. Só falha técnica (erro HTTP ou tempo esgotado) pode ser repetida, até 3 vezes, com a mesma condição.
- **Seleção:** o conjunto do E é formado pelas **primeiras 1.370 válidas na ordem de geração** (passagem, depois ordem da fonte). Nenhuma imagem é escolhida, trocada ou excluída por olhar o conteúdo.
- **Plano reserva (D36):** ao fim de 30/12/2026 (Brasília) conta-se as válidas. Se houver menos de 1.370, valem as **primeiras 454 válidas na mesma ordem**, e as demais regras da D36 e da D35 se mantêm. A contagem usa só os registros de geração e o filtro, nunca resultados de treino ou de teste.
- A geração do E pode começar logo depois do lacre, em paralelo à avaliação humana das 150. Se a seção 9 ou a seção 7 impedirem o uso do E, as edições geradas não são usadas, e esse custo é aceito.

## 11. Calendário
Só as datas de 20/12/2026 (fim da geração) e 30/12/2026 (contagem da D36) são limites; as demais são previstas e servem para checar viabilidade. Datas em Brasília.
| Etapa | Prevista | Depende de |
|---|---|---|
| Revisão e lacre do 4a; tag `lacre-adendo4a` | até 27/11 | Daniela |
| Script de sorteio, lista elegível e hashes registrados; filtro congelado e registrado | até 30/11 | lacre |
| Classificação das condições e geração das 150 | 01/12 a 04/12 | sorteio, plano pago do Groq |
| Avaliação humana das 150 (Daniela e José) e kappa | 05/12 a 10/12 | geração das 150 |
| Filtro aplicado às 150; decisão da seção 7 e da seção 9 | 11/12 a 12/12 | avaliações |
| Geração do E (classificação e passagens 1 e 2) | 05/12 a 20/12 | lacre, em paralelo à avaliação |
| Filtro nas edições do E, formação do conjunto e contagem | 21/12 a 30/12 | decisões das seções 7 e 9 |
Se a avaliação humana ultrapassar 12/12, a geração do E continua até 20/12 e a decisão fica para o dia em que sair, sem mudar o limite de 30/12.

## 12. Desvios
Qualquer mudança (amostra, prompt, modelo, critérios) é registrada em `docs/DESVIOS.md` com data e motivo; este documento não é editado depois de lacrado.
