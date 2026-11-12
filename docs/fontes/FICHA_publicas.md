# Fichas das fontes reais públicas

Base: inventário de `_zips` de 2026-11-11 (`INVENTARIO_zips_2026-11-11.txt`, saída do `scripts/inventario_zips.py`, rodado por Daniela). Licenças, citações e hashes dos pacotes ainda por preencher no modelo `FICHA_modelo.md`.

| Fonte | Pacote em `_zips` | Imagens | Rótulos | Estrutura | Pendências e riscos |
| --- | --- | --- | --- | --- | --- |
| Singapore Maritime Dataset (on-shore) | `smd_clean.zip` (0,16 GB) | 914 JPG | YOLO `.txt` | Tudo sob `smd_clean/test/{images,labels}`, nomes Roboflow (`MVI_xxxx_VIS_frameNNN_jpg.rf.<hash>`) | Quadros de poucos vídeos: quase-duplicatas esperadas (cluster dHash). A pasta `test` é do Roboflow, não é teste do CITRA |
| SeaShips | `SeaShips_voc.zip` (0,63 GB) | 13.105 JPG, 13.120 XML | VOC XML | `train/`, `test/` e arquivos na raiz; exportação Roboflow, com cópias aumentadas da mesma imagem | A regra herdada (nome-base Roboflow, primeiro em ordem alfabética) dá 6.979 bases. Decisão A09: escolher entre este pacote, `seaship.zip` (7.000 JPG, `train.csv`/`test.csv`) e `SeaShips_voc_incompleto_6509.zip` (11.002 JPG, 10.979 XML) |
| ABOShips | `ABOships.zip` (8,17 GB) | 9.880 PNG | CSV `Labels/Vesibussi_Labels.csv` (colunas `filename,xmin,xmax,ymin,ymax,width,height,class`) | `ABOshipsDataset/Seaships/<data>/<nome>.png`; traz `ABOshipDescription.pdf` e `parse_seaships.py` | Sequências por data: quase-duplicatas. Ler a descrição do dataset para licença e citação |
| InaTechShips | `dataset_25k_v2.zip` (10,7 GB) | 27.796 JPG | YOLO `.txt`; `data.yaml` e `data_single_class.yaml` | `train` (25.015), `test` (8.341), `val` (8.337) internos da fonte, mais `reconstrucao_report.json` | Dataset "reconstruído": ler o relatório antes de confiar na contagem. As divisões internas não valem para este experimento |

Fora do experimento, mas presentes em `_zips`:

| Pacote | O que é | Observação |
| --- | --- | --- |
| `synth_abo`, `synth_both`, `synth_inatech`, `synth_inatech_v04_fullpool` (~11 GB, 21.840 imagens cada) | Composições sintéticas das Fases 3–5, com nomes de imagem do CITRA e sufixo `_vN` | Linha encerrada. Contêm fundos do CITRA; nunca misturar com fontes externas |
| `crops_abo`, `InaTechShips_crops_sam` | Recortes extraídos | Só servem à linha encerrada |
| `UA-DETRAC-DATASET-10K.zip` | Segundo domínio-alvo | Extensão futura, fora do escopo |
| `INPUT_/OUTPUT_2026-08-11_14-31-55.zip` | Piloto do iflens | Ver `FICHA_iflens.md` |

Gerar o manifesto de cada fonte: `python -m scripts.manifesto_fonte construir --fonte <nome> --formato <yolo|voc|abocsv> --zip <pacote> --saida manifests/manifesto_<nome>.csv --citra-hashes <tabela>`. Antes, gerar a tabela de hashes do CITRA com `python -m scripts.manifesto_fonte hashes-citra`.

## Resultados dos manifestos

Relatórios colados por Daniela em 2026-11-11 (Colab); os CSV dos manifestos ainda não foram enviados ao repositório.

| Fonte | Imagens | Sem rótulo | Dup. nome-base | Dup. conteúdo exato | Clusters quase-dup (dHash ≤ 4) | Caixas | Small a 640 | Colide com CITRA (exata / quase) | SHA-256 do pacote |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SMD | 914 | 0 | 0 | 0 | 743 (171 imagens agrupadas, 18,7%) | 7.043 | 4.043 (57,4%) | 0 / 0 |
| ABOShips | 9.880 | **839 (8,5%)** | 0 | 0 | 8.155 (1.725 agrupadas, 17,5%) | 41.967 | 29.657 (70,7%) | 0 / **3** |
| InaTechShips | 27.796 | 0 | 0 | **5.651 (20,3%)** | 22.067 (5.729 agrupadas, 20,6%) | 27.796 (1 por imagem) | **0 (0%)** | 0 / **62** |
| SeaShips (`SeaShips_voc.zip`) | — | — | — | — | — | — | — | — | `77b01da5…c48efc` (completo: `77b01da5e2f9664144295273202634bb25e5f86a220d83142c8b45ed0fc48efc`) |

Leituras e limites:
- 914 imagens e 7.043 caixas conferem com a contagem das Fases 0–5.
- A ausência de colisão com o CITRA vale para cópias idênticas (hash de pixels) e para quase-cópias com dHash de 64 bits a distância ≤ 4. Esse hash é grosseiro; não detecta recortes nem reamostragens fortes. O limiar de 4 não foi calibrado.
- O SMD tem 57,4% de caixas small a 640, contra 82,2% do CITRA: é a fonte com perfil mais próximo entre as medidas até agora, mas ainda mais "fácil" que o alvo.
- CITRA: 1.348 train, 332 val e 401 test, como no plano. As 3 imagens sem split eram 2 em `_quarantine` (`14.04.2022-13-48-55`, `29.04.2022-14-59-27`) e a figura `escala_citra3d_report.png`, que não é do dataset. A segunda quarentena é a imagem que aparece também no piloto do iflens. O script agora marca a pasta como `quarentena` e ignora figuras de relatório.

Pontos que exigem verificação antes de qualquer uso:

- **SeaShips:** a execução parou com `UnidentifiedImageError` depois de ~7.000 imagens (arquivo ilegível dentro do pacote). O script foi corrigido para registrar o arquivo como `ilegivel` e continuar; falta reexecutar. Os arquivos ilegíveis ficam listados no relatório.
- **ABOShips, 839 imagens sem caixa:** ou são quadros sem embarcação, ou o nome do arquivo não casou com a coluna `filename` do CSV. Comparar o nº de `filename` distintos do CSV com 9.880 − 839 = 9.041.
- **InaTechShips:** exatamente uma caixa por imagem e **nenhuma small** a 640: é um conjunto de fotos de um objeto grande, sem relação com o regime do CITRA. 20,3% das imagens são cópias exatas de outras do próprio pacote (as divisões train/test/val internas não são independentes, o que também confirma que não servem de referência).
- **Colisões com o CITRA por quase-cópia:** 3 no ABOShips e 62 no InaTechShips, com dHash ≤ 4. Podem ser falsos positivos (imagens com pouca textura, como mar e céu uniformes, têm dHash parecido) ou cópias reais. Só a inspeção visual decide: `python -m scripts.manifesto_fonte colisoes ...`. Até lá, tratar as imagens marcadas como excluídas do pool.
- Os SHA-256 dos pacotes de ABOShips e InaTechShips não foram calculados (use `--hash-pacote` ou `sha256sum`).
