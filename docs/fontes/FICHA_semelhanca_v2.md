# Ficha: medida de semelhança v2 do CITRA (DINOv2)

Critérios de uso fixados antes da extração em D25 (`docs/DECISOES.md`). Script: `scripts/embeddings_citra.py`. Extração de 2026-11-18: `data/embeddings_citra/` (1.348 / 332 / 401 imagens reais, 768 valores por imagem).

## Verificação da justificativa na literatura (2026-11-18)

O que está sustentado:
- Os atributos congelados do DINO (versão 1) funcionam bem para recuperação por vizinho mais próximo em referências de pontos de referência (Oxford, Paris) e em detecção de cópias (Copydays, subconjunto "strong"): Caron et al. 2021, arXiv 2104.14294, seção 4.2.1.
- O DINOv2 (Oquab et al. 2023, arXiv 2304.07193) é apresentado como gerador de atributos de uso geral, usados congelados e competitivos com os melhores modelos fracamente supervisionados. O treino usa 142 milhões de imagens curadas, sem rótulos.
- O ViT-B/14 tem 86 milhões de parâmetros (README do repositório oficial).
- Licença: Apache 2.0 para código e pesos do DINOv2 segundo o README e o cartão do modelo do repositório oficial (a licença não comercial vale para modelos separados de células e de raio X). Não consegui abrir a página `facebook/dinov2-base` no Hugging Face; a versão usada é a conversão para `transformers`. Conferir a licença nessa página antes de submeter o artigo.

O que NÃO está sustentado como eu disse:
- "O DINOv2 é melhor que o CLIP para quase-duplicatas": só encontrei fontes secundárias (blogs, páginas de fornecedor e um artigo que o usa como ferramenta, arXiv 2407.00592), nenhuma comparação direta controlada. É plausível, mas não está demonstrado por mim. Não afirmar no artigo sem essa referência; a conferência humana (D25) é a validação no nosso corpus.

Limite importante:
- Pizzi et al. 2022 (SSCD, arXiv 2202.10261) mostram que um descritor treinado especificamente para detecção de cópias melhora 2 a 5 vezes a linha de base do DINO (ViT-B/16, versão 1) em transformações fortes (conjunto DISC2021). Ou seja, o DINO genérico não é o melhor detector de cópias editadas. Nosso caso é diferente (quadros sem edição, da mesma câmera), mas o limite se aplica: a medida é uma aproximação, e a conferência de 30 pares testa se serve aqui.
