# Esboço do artigo

Título provisório: *Que tipo de fonte aumenta um detector de embarcações pequenas? Imagens reais públicas, renderizadas e geradas por IA, com passos de otimização igualados.*

Regra: cada seção só afirma o que está no livro de alegações (`LIVRO_DE_ALEGACOES.csv`) com status e evidência. A seção de resultados é escrita a partir de `results/`, nunca de memória.

| Seção | Conteúdo | Material de origem | Estado |
| --- | --- | --- | --- |
| Introdução | Escassez de dados em alvo operacional; três famílias de aumento; lacuna (a confirmar pela busca sistemática) | `literatura/REGISTRO_BUSCA.md` | a escrever depois da busca |
| Trabalhos relacionados | Sim-to-real marítimo, edição generativa para robustez, valoração de dados | `literatura/` | rascunho em `PLANEJAMENTO.md` |
| Alvo e protocolo | CITRA-3D-Real, YOLO11n, protocolo V2, ruído, piso de 2 pp, passos igualados | `PROTOCOLO_RIGOR.md`, repositório das Fases 0–5 | disponível |
| Fontes | Quatro públicas, GenShip, iflens; fichas; deduplicação; auditoria de rótulos | `fontes/` | fichas em preenchimento |
| Desenho | Portão por tipo de fonte, depois atribuição; seeds; estatística | adendo lacrado | depende do adendo |
| Resultados: tipo de fonte | Diferenças pareadas, IC, TOST | `results/` | vazio |
| Resultados: atribuição | Só se o portão achar efeito | `results/` | vazio |
| Auditoria de rótulos gerados | Taxas de descarte por condição e tamanho; concordância entre avaliadores | `data/auditoria_*` | piloto feito (um avaliador) |
| Ameaças à validade | Um alvo, uma arquitetura, domínio do teste igual ao do treino, terceira avaliação do teste, API de modelo mutável | `PLANEJAMENTO.md` (riscos) | rascunho |
| Reprodutibilidade | Commit, manifestos com hash, registro de execuções, ambiente | `runs/`, `CHECKLIST_REPRODUTIBILIDADE.md` | em construção |

Entregas aceitáveis, em ordem: (1) resultado negativo bem dimensionado no portão; (2) efeito de uma ou mais fontes com atribuição; (3) protocolo de verificação de rótulos de edição generativa com taxas medidas, independentemente do resultado de treino.
