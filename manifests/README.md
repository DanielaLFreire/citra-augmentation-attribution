# Manifestos

Um CSV por lista de treino e por fonte. Só manifestos entram no repositório; as imagens ficam no Drive.

Colunas mínimas por imagem (`manifesto_<fonte>.csv`):

| Coluna | Significado |
| --- | --- |
| `id_imagem` | Identificador estável |
| `fonte` | citra, smd, seaships, aboships, inatechships, genship, iflens |
| `caminho_relativo` | Relativo à raiz da fonte no Drive |
| `sha256_conteudo` | Hash dos pixels decodificados (para deduplicar entre fontes e contra val/test do CITRA) |
| `sha256_arquivo` | Hash do arquivo |
| `largura`, `altura` | Em pixels |
| `n_caixas`, `n_small_640` | Nº de caixas e nº de pequenas no letterbox 640 |
| `split_origem` | train/val/test da origem, se houver |
| `id_original` | Para edições geradas: imagem de origem no CITRA |
| `parametros_json` | Parâmetros de geração (renderização ou condições sorteadas); vazio se desconhecido |
| `status_auditoria` | aprovada, descartada, não auditada |

Listas de treino (`lista_treino_<braco>_seed<N>.csv`): `ordem,id_imagem,fonte`. Registrar o hash de cada uma com `python -m scripts.registrar_artefato` antes do treino.
