import csv
import io
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from scripts._nomes import nome_seguro
from scripts.manifesto_fonte import hashes_imagem
from scripts.materializar_externas import linha_yolo, materializar


def _png(w, h, cor):
    b = io.BytesIO()
    Image.new("RGB", (w, h), cor).save(b, "PNG")
    return b.getvalue()


def _pacotes(tmp_path):
    ab = tmp_path / "ab.zip"
    img = _png(200, 100, (10, 20, 30))
    with zipfile.ZipFile(ab, "w") as z:
        z.writestr("Seaships/20180626/201806260722_000.png", img)
        z.writestr("Seaships/Labels/l.csv", "filename,xmin,xmax,ymin,ymax\n201806260722_000,10,60,20,50\n201806260722_000,190,260,0,40\n")
    smd = tmp_path / "smd.zip"
    img2 = _png(100, 100, (200, 0, 0))
    with zipfile.ZipFile(smd, "w") as z:
        z.writestr("smd/test/images/MVI_1_a.png", img2)
        z.writestr("smd/test/labels/MVI_1_a.txt", "3 0.5 0.5 0.2 0.4\n")
    return ab, smd, img, img2


def _lista(tmp_path, img, img2, hash_ok=True):
    h1, h2 = hashes_imagem(img)["sha256_conteudo"], hashes_imagem(img2)["sha256_conteudo"]
    if not hash_ok:
        h1 = "0" * 64
    p = tmp_path / "lista.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fonte", "id_imagem", "caminho_relativo", "unidade", "sha256_conteudo", "n_caixas", "n_small_640"])
        w.writerow(["aboships", "aboships:Seaships/20180626/201806260722_000.png", "Seaships/20180626/201806260722_000.png", "u", h1, 2, 0])
        w.writerow(["smd", "smd:smd/test/images/MVI_1_a.png", "smd/test/images/MVI_1_a.png", "v", h2, 1, 0])
    return p


def test_nome_seguro_sem_separadores_e_ids_do_citra_intactos():
    assert nome_seguro("aboships:A/B/c d.png") == "aboships_A_B_c_d.png"
    assert nome_seguro("01.07.2022-10-37-14") == "01.07.2022-10-37-14"


def test_linha_yolo_corta_e_descarta_caixa_sem_area():
    assert linha_yolo(10, 20, 60, 50, 200, 100) == "0 0.175000 0.350000 0.250000 0.300000"
    assert linha_yolo(190, 0, 260, 40, 200, 100) == "0 0.975000 0.200000 0.050000 0.400000"  # cortada em x=200
    assert linha_yolo(300, 0, 400, 40, 200, 100) is None  # toda fora da imagem


def test_materializa_converte_para_classe_unica_e_escreve_mapa(tmp_path):
    ab, smd, img, img2 = _pacotes(tmp_path)
    saida = tmp_path / "out"
    rel = materializar(_lista(tmp_path, img, img2), {"aboships": (ab, "abocsv"), "smd": (smd, "yolo")}, saida)
    assert rel["fontes"]["aboships"]["n"] == 1 and rel["fontes"]["smd"]["n"] == 1
    mapa = list(csv.DictReader(open(saida / "mapa_externas.csv", encoding="utf-8")))
    assert len(mapa) == 2
    por_id = {m["id_imagem"]: m for m in mapa}
    rot = Path(por_id["smd:smd/test/images/MVI_1_a.png"]["caminho_rotulo"]).read_text().split()
    assert rot[0] == "0" and rot[1:] == ["0.500000", "0.500000", "0.200000", "0.400000"]  # classe 3 vira 0
    assert Path(por_id["aboships:Seaships/20180626/201806260722_000.png"]["caminho_imagem"]).exists()


def test_conteudo_diferente_da_lista_interrompe(tmp_path):
    ab, smd, img, img2 = _pacotes(tmp_path)
    with pytest.raises(ValueError, match="conteúdo diferente"):
        materializar(_lista(tmp_path, img, img2, hash_ok=False), {"aboships": (ab, "abocsv"), "smd": (smd, "yolo")}, tmp_path / "o")


def test_fonte_sem_pacote_interrompe(tmp_path):
    ab, smd, img, img2 = _pacotes(tmp_path)
    with pytest.raises(ValueError, match="sem pacote"):
        materializar(_lista(tmp_path, img, img2), {"aboships": (ab, "abocsv")}, tmp_path / "o")
