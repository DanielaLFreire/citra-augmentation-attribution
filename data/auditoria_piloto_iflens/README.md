# Auditoria do piloto iflens

- `audit_0.jpg` … `audit_3.jpg`: 98 pares de recortes (original à esquerda, edição à direita, caixa herdada em amarelo).
- `auditoria_iflens_piloto.json`: uma entrada por caixa. Campos: `i` índice na grade, `s` imagem, `j` caixa, `bw`/`bh` tamanho da caixa em px, `classe`.

Classes: **A** objeto visível e alinhado; **B** objeto no lugar, mas muito apagado; **C** nada visível dentro da caixa; **D** objeto deslocado ou substituído; **U** não avaliável. Avaliador único (Claude, revisão visual). Fronteira entre B e C é subjetiva. Uma medida automática por correlação de bordas foi descartada (D03). **A auditoria precisa de revisão por Daniela e de um segundo avaliador antes de entrar no artigo.**
