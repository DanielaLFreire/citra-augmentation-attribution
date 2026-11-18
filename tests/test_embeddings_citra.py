import numpy as np

from scripts.embeddings_citra import l2, nomes_reais


def test_nomes_reais_filtra_quarentena_e_nao_reais():
    nomes = [
        "x/train/images/14.04.2022-15-53-50.png",
        "x/train/images/Lancha_0529_RainON.png",
        "x/train/images/29.04.2022-14-59-27.png",
        "x/train/images/0123.png",
        "x/train/images/01.01.2022-08-00-00.png",
    ]
    assert [b for _, b in nomes_reais(nomes)] == ["01.01.2022-08-00-00", "14.04.2022-15-53-50"]


def test_l2_norma_unitaria():
    v = l2(np.array([[3.0, 4.0], [1.0, 0.0]]))
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0)
