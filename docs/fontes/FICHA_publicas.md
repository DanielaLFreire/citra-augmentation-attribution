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
