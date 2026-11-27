# Notas para o estudo posterior do E (adendo 4e): como reduzir as falhas da edição

Estado: anotações de 2026-11-27 (D101), sem valor de pré-registro. Escritas depois de ver a auditoria das 150 (D96) e o filtro (D99). **As 150 imagens auditadas passam a ser conjunto de desenvolvimento do estudo posterior**: qualquer prompt, corretor ou filtro novo pode ser ajustado nelas, mas tem de ser validado numa amostra nova, sorteada entre as fontes ainda não auditadas e auditada às cegas.

## 1. O que falhou nas 150 (descritivo, sem teste; n pequeno por célula)
- Taxa primária: 44/150 = 29,3% (qualquer avaliador). Entre as reprovadas, 32 tinham caixa apagada, deslocada ou alterada e 21 tinham embarcação adicionada (as duas coisas podem ocorrer na mesma imagem).
- Por condição-alvo, a taxa varia pouco e sem padrão claro: hora do dia de 19% (`dawn`) a 41% (`dusk`); céu de 27% a 32%; atmosfera de 22% (`light_rain`) a 36% (`heavy_rain`), com `haze` em 3/4. Estrato padrão 29%, risco 30%.
- Trocar entre dia e crepúsculo: 33% (78 imagens) contra 25% (72) sem a troca.
- Por número de caixas: 1 caixa 27%, 2 a 4 caixas 37%, 5 ou mais 18%.
- Leitura: a falha parece **estrutural** (o modelo redesenha a cena), não ligada a uma condição específica. Prompt sozinho tende a ajudar pouco; vale mais proteger os objetos rotulados.

## 2. Mudanças candidatas no prompt
1. **Inventário explícito**: informar o número de embarcações e a posição aproximada de cada uma (a partir dos rótulos, em termos como "à esquerda, perto do horizonte"), e pedir que o número final seja o mesmo. Risco a testar: o modelo desenhar marcas ou caixas.
2. **Proibir adições nos lugares onde elas apareceram**: horizonte, bordas da imagem e água vazia ("do not add vessels, boats, buoys or any object on the horizon, at the image borders or on empty water").
3. **Objetos pequenos e borrados**: pedir que pontos distantes, pequenos ou desfocados sejam preservados sem nitidez nova e sem reinterpretação ("keep small, distant or blurry objects exactly as they are; do not sharpen, reinterpret or remove them").
4. **Mudança global, não redesenho**: pedir que a mudança seja de iluminação, cor e atmosfera aplicadas por cima da foto, sem regenerar o conteúdo ("apply the change as a global colour, light and atmosphere adjustment over the existing photo; do not regenerate the scene").
5. **Condição original explícita**: dizer a condição atual e a de destino ("current: dusk, overcast, haze; target: ..."), para o modelo mudar só a diferença.
6. **Resolução**: verificar se o modelo devolve na mesma resolução da entrada; se ele gera em resolução menor e amplia, as embarcações pequenas se perdem. Pedir a mesma resolução e comparar.

## 3. Mudanças fora do prompt (provavelmente mais eficazes)
1. **Proteger e recolar**: depois da edição, recolar o conteúdo original de cada caixa (com margem) sobre a imagem editada e ajustar a cor do recorte à cena (transferência de cor). Elimina apagada, deslocada e alterada por construção; não resolve embarcação adicionada fora das caixas. Risco: emendas visíveis e iluminação incoerente no recorte.
2. **Edição com máscara**, se a API permitir: editar só céu, água e fundo, com as caixas protegidas.
3. **Corretor automático externo** (por exemplo SAM 3 com o prompt de texto "boat"): remover caixa sem embarcação, ajustar caixa deslocada, acrescentar caixa para embarcação nova; regra conservadora para objetos pequenos (só remover com evidência forte). Não usar os modelos do experimento (C, R) como corretor.
4. **Várias gerações por fonte com escolha automática pré-especificada** (por exemplo, a de maior semelhança dentro das caixas). Exige adendo próprio, porque o 4a proíbe regenerar.
5. **Correção humana**: cerca de 1,6 min por imagem (José, D94), da ordem de 35 a 40 h para 1.370 imagens. Exata e com custo mensurável; serve também de referência para o corretor automático.
6. **Modelo de edição mais forte** (com custo maior), comparado no mesmo protocolo.

## 4. Cuidados de desenho para o 4e
- Desenvolvimento nas 150 já auditadas; validação numa amostra nova, com os mesmos avaliadores, cegos, e kappa medido de novo.
- Comparação entre prompts ou métodos com as regras de α e poder já previstas no 4a (seção 8: 0,05 bilateral, 90%).
- O critério de uso continua sendo a taxa residual de rótulo ruim (≤ 7%), medida contra a referência humana "qualquer avaliador".
- Custo de cada alternativa registrado desde o início (chamadas, GPU, pessoa-h).

## 5. Achado à parte, sobre os dados
- A052: José anotou "imagem totalmente preta" e "imagem original inválida". Se o original do CITRA for de fato preto, há pelo menos uma imagem inválida com rótulos no treino, o que é ruído herdado igual em todos os braços. A conferir no arquivo original antes do estágio 1, sem mudar a divisão sem registro.
