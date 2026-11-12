import io

import numpy as np
from PIL import Image

from scripts.auditar_degeneradas import auditar, estatisticas, motivo


def img(valor=None, seed=0):
    rng = np.random.default_rng(seed)
    a = np.full((40, 60, 3), valor, np.uint8) if valor is not None else rng.integers(0, 255, (40, 60, 3), dtype=np.uint8)
    b = io.BytesIO(); Image.fromarray(a).save(b, "PNG"); return b.getvalue()


def test_motivos():
    assert motivo(estatisticas(img(0))) == "uniforme+escuro"
    assert motivo(estatisticas(img(255))) == "uniforme+claro"
    assert motivo(estatisticas(img(128))) == "uniforme"
    assert motivo(estatisticas(img())) == ""


def test_auditar_resume_por_split_e_ilegivel():
    itens = [("a/train/i.png", "train", img(0)), ("a/val/j.png", "val", img()), ("a/test/k.png", "test", b"lixo")]
    linhas, r = auditar(iter(itens))
    assert r["n_imagens"] == 3 and r["n_degeneradas"] == 1 and r["n_ilegiveis"] == 1
    assert r["por_split"] == {"train": 1, "test": 1}


def test_todas_grava_tudo_e_resumo_nao_conta_normais():
    itens = [("a/train/i.png", "train", img(0)), ("a/val/j.png", "val", img())]
    linhas, r = auditar(iter(itens), todas=True)
    assert len(linhas) == 2 and r["n_degeneradas"] == 1
