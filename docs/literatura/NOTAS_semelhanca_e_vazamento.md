# Notas de literatura: semelhança entre imagens, detecção de cópias e vazamento (2026-11-18)

Origem: verificação da justificativa da medida v2 (D25, `docs/fontes/FICHA_semelhanca_v2.md`). **Profundidade de leitura: trechos devolvidos por busca e pelas páginas dos repositórios, não os artigos completos.** Antes de citar no texto final, abrir o artigo, conferir o número da seção, a tabela e o veículo de publicação (campos "confirmar" abaixo).

## Referências

| Id | Referência | Link | Lido | Para que serve no nosso artigo |
| --- | --- | --- | --- | --- |
| R1 | Caron et al., *Emerging Properties in Self-Supervised Vision Transformers* (DINO), 2021 | https://arxiv.org/abs/2104.14294 | trechos (Tabela 4 e seção 4.2.1) | Atributos congelados de ViT auto-supervisionado servem para recuperação por vizinho mais próximo, em pontos de referência e em detecção de cópias (Copydays) |
| R2 | Oquab et al., *DINOv2: Learning Robust Visual Features without Supervision*, 2023 (versão 2, fev. 2024) | https://arxiv.org/abs/2304.07193 | trechos (resumo e introdução) | Modelo usado na medida v2: atributos de uso geral, treinados em 142 milhões de imagens curadas sem rótulos, usados congelados |
| R3 | Pizzi et al., *A Self-Supervised Descriptor for Image Copy Detection* (SSCD), 2022 | https://arxiv.org/abs/2202.10261 | trechos (Tabelas 2 e 3) | Limite: descritor feito para cópias supera o DINO genérico em 2 a 5 vezes antes da normalização de escores, em transformações fortes (DISC2021) |
| R4 | Repositório e cartão do modelo DINOv2 (Meta) | https://github.com/facebookresearch/dinov2 | README e cartão do modelo | Licença Apache 2.0 do código e dos pesos; ViT-B/14 com 86 milhões de parâmetros; licença não comercial vale para modelos separados (células, raio X) |

Confirmar antes de citar: veículo de publicação de R1 (provável ICCV 2021), R2 (provável TMLR 2024) e R3 (provável CVPR 2022); licença da página `facebook/dinov2-base` no Hugging Face (não consegui abri-la).

## O que pode ser afirmado, e como

1. "Atributos auto-supervisionados congelados são usados para recuperar imagens parecidas e detectar cópias" (R1, R2). Apoiado.
2. "Usamos o DINOv2-base congelado como medida de semelhança" (R2, R4), com revisão dos pesos `f9e44c814b77203eaa57a6bdbbd535f21ede1415` e entrada 448×252 (`data/embeddings_citra/`).
3. "O DINOv2 não é o melhor detector de cópias editadas" (R3, sobre o DINO versão 1, ViT-B/16). Usar como ressalva, com a diferença de regime: nossos quadros não são editados.

## O que NÃO afirmar

- "O DINOv2 supera o CLIP em quase-duplicatas": só encontrei fontes secundárias (blogs, páginas de fornecedores) e um artigo que usa o DINOv2 como ferramenta (arXiv 2407.00592), nenhuma comparação direta controlada. Se for necessário, fazer a comparação no nosso corpus ou omitir.
- Qualquer limiar de cosseno como valor universal: ele depende do modelo, da resolução e do corpus. Nosso limiar sai da regra do D25 e da conferência humana, e vale só para este conjunto.

## Registro da busca

Quatro buscas em 2026-11-18 (modo padrão): (a) "DINOv2 Oquab 2023 self-supervised features copy detection instance retrieval Copydays Oxford Paris"; (b) "DINOv2 vs CLIP near-duplicate image detection comparison self-supervised copy detection"; (c) "facebookresearch dinov2 GitHub license Apache 2.0 model weights" (domínios github.com e huggingface.co); mais uma tentativa de abrir a página do modelo no Hugging Face, recusada pelo ambiente. Critério: fonte primária (artigo ou repositório oficial) para toda afirmação técnica; fonte secundária só para mapear o que procurar. Esta não é a busca sistemática prevista em `REGISTRO_BUSCA.md`: sobre vazamento de dados por quase-duplicatas em detecção de objetos ainda não busquei (ver pendência abaixo).

## Pendência

Busca sobre vazamento por quadros quase idênticos em conjuntos de detecção (câmeras fixas, divisão aleatória por quadro), para fundamentar a decisão D23 no artigo. Registrar aqui a string, a data e o resultado.
