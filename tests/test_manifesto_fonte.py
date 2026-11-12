import csv
import io
import zipfile

import numpy as np
from PIL import Image

from scripts.manifesto_fonte import (agrupar_quase_duplicatas, caixas_voc, caixas_yolo, construir, dhash,
                                     hashes_citra, small_letterbox)


def png(seed, size=(64, 48), ruido=0, fmt="PNG"):
    rng = np.random.default_rng(seed)
    base = rng.integers(0, 255, (size[1], size[0], 3), dtype=np.uint8)
    if ruido:
        base = np.clip(base.astype(int) + rng.integers(-ruido, ruido + 1, base.shape), 0, 255).astype(np.uint8)
    b = io.BytesIO()
    Image.fromarray(base).save(b, fmt)
    return b.getvalue()


def test_small_letterbox():
    assert small_letterbox(20, 20, 1920, 1080)          # 20*0.333 = 6.7 px -> small
    assert not small_letterbox(200, 200, 1920, 1080)    # 66 px -> não small


def test_caixas_yolo_e_voc():
    assert caixas_yolo("0 0.5 0.5 0.2 0.4\n", 100, 100) == [(40.0, 30.0, 60.0, 70.0)]
    xml = b"<annotation><object><bndbox><xmin>1</xmin><ymin>2</ymin><xmax>3</xmax><ymax>4</ymax></bndbox></object></annotation>"
    assert caixas_voc(xml) == [(1.0, 2.0, 3.0, 4.0)]


def test_agrupar_quase_duplicatas():
    a = 0xFFFF0000FFFF0000
    cl = agrupar_quase_duplicatas([a, a ^ 0b11, a ^ (1 << 40), 0x0123456789ABCDEF])
    assert cl[0] == cl[1] == cl[2] and cl[3] != cl[0]


def test_yolo(tmp_path):
    zp = tmp_path / "s.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("d/test/images/a.jpg", png(1, fmt="JPEG"))
        z.writestr("d/test/labels/a.txt", "0 0.5 0.5 0.1 0.1\n0 0.2 0.2 0.1 0.1\n")
        z.writestr("d/test/images/b.jpg", png(2, fmt="JPEG"))  # sem rótulo
    linhas, rel = construir("fx", "yolo", zp, progresso=0)
    por = {r["caminho_relativo"]: r for r in linhas}
    assert por["d/test/images/a.jpg"]["n_caixas"] == 2 and por["d/test/images/a.jpg"]["split_origem"] == "test"
    assert por["d/test/images/b.jpg"]["n_caixas"] == 0 and rel["n_sem_rotulo"] == 1


def test_voc_roboflow_e_duplicatas(tmp_path):
    zp = tmp_path / "v.zip"
    xml = b"<annotation><object><bndbox><xmin>1</xmin><ymin>2</ymin><xmax>30</xmax><ymax>40</ymax></bndbox></object></annotation>"
    img = png(3, fmt="JPEG")
    with zipfile.ZipFile(zp, "w") as z:
        for h in ("aaaa", "bbbb"):   # mesma base Roboflow, mesmo conteúdo
            z.writestr(f"d/train/000001_jpg.rf.{h}.jpg", img)
            z.writestr(f"d/train/000001_jpg.rf.{h}.xml", xml)
        z.writestr("d/test/000002_jpg.rf.cccc.jpg", png(4, fmt="JPEG"))
        z.writestr("d/test/000002_jpg.rf.cccc.xml", xml)
    linhas, rel = construir("fx", "voc", zp, progresso=0)
    assert rel["n_imagens"] == 3 and rel["n_dup_base_roboflow"] == 1 and rel["n_dup_conteudo_exato"] == 1
    assert rel["n_unicas_pela_regra_herdada"] == 2
    dup = [r for r in linhas if r["dup_base_de"]][0]
    assert dup["caminho_relativo"].endswith("bbbb.jpg") and dup["dup_base_de"].endswith("aaaa.jpg")


def test_abocsv_e_colisao_citra(tmp_path):
    zp = tmp_path / "a.zip"
    img_citra = png(5)
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("D/Seaships/20180101/x_000.png", img_citra)
        z.writestr("D/Seaships/20180101/y_001.png", png(6))
        z.writestr("D/Labels/L.csv", "filename,xmin,xmax,ymin,ymax,width,height,class\nx_000,1,11,2,12,10,10,ship\nx_000,20,30,20,30,10,10,ship\n")
    citra_dir = tmp_path / "citra" / "test" / "images"
    citra_dir.mkdir(parents=True)
    (citra_dir / "c.png").write_bytes(img_citra)
    citra = hashes_citra(tmp_path / "citra")
    assert citra[0]["split"] == "test"
    linhas, rel = construir("fx", "abocsv", zp, citra, progresso=0)
    por = {r["caminho_relativo"].split("/")[-1]: r for r in linhas}
    assert por["x_000.png"]["n_caixas"] == 2 and por["x_000.png"]["colide_citra"] == "exata:test"
    assert por["y_001.png"]["colide_citra"] == "" and rel["n_colide_citra_exata"] == 1


def test_dhash_estavel_a_pequeno_ruido():
    a = Image.open(io.BytesIO(png(7, (128, 96))))
    b = Image.open(io.BytesIO(png(7, (128, 96), ruido=3)))
    assert bin(dhash(a) ^ dhash(b)).count("1") <= 8


def test_hashes_citra_quarentena_e_relatorio(tmp_path):
    for sub, nome in (("train", "a.png"), ("_quarantine", "q.png"), (".", "escala_report.png")):
        d = tmp_path / sub
        d.mkdir(exist_ok=True)
        (d / nome).write_bytes(png(hash(nome) % 1000))
    splits = sorted(r["split"] for r in hashes_citra(tmp_path))
    assert splits == ["quarentena", "train"]
