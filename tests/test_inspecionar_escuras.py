import numpy as np
from PIL import Image

from scripts.inspecionar_escuras import esticar, ler_caixas, renderizar


def test_esticar_clareia_imagem_escura():
    a = np.zeros((20, 30, 3), np.uint8); a[5:10, 5:10] = 3
    assert np.asarray(esticar(Image.fromarray(a))).max() > 200


def test_renderizar_desenha_caixa(tmp_path):
    (tmp_path / "train/images").mkdir(parents=True); (tmp_path / "train/labels_final").mkdir(parents=True)
    a = np.zeros((100, 200, 3), np.uint8); a[40:60, 90:110] = 2
    Image.fromarray(a).save(tmp_path / "train/images/x.png")
    (tmp_path / "train/labels_final/x.txt").write_text("0 0.5 0.5 0.1 0.2\n")
    r = renderizar(tmp_path, "train", "x", tmp_path / "out")
    assert r["n_caixas"] == 1 and (tmp_path / "out/train_x.png").exists()
    assert ler_caixas(tmp_path / "nao.txt", 10, 10) is None
