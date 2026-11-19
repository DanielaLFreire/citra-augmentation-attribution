import numpy as np
import pytest

from scripts.semelhanca_recortes_citra import (analisar_recortes, bootstrap_dif_medianas, caixa_pixels, faixa_tamanho,
                                               ler_rotulo_yolo, max_cos, terços)


def test_ler_rotulo():
    assert ler_rotulo_yolo("0 0.5 0.5 0.2 0.1\n\n0 0.1 0.2 0.3 0.4\n") == [(0.5, 0.5, 0.2, 0.1), (0.1, 0.2, 0.3, 0.4)]
    with pytest.raises(ValueError):
        ler_rotulo_yolo("0 0.5 0.5 0.2\n")


def test_caixa_com_margem_de_20_por_cento():
    # caixa 100x50 px no centro de 1000x500: margem 20 px em x e 10 px em y de cada lado
    assert caixa_pixels(1000, 500, 0.5, 0.5, 0.1, 0.1) == (430, 215, 570, 285)


def test_caixa_clampada_e_minimo_de_1_px():
    x0, y0, x1, y1 = caixa_pixels(100, 100, 0.0, 0.0, 0.0, 0.0)
    assert (x0, y0) == (0, 0) and x1 >= 1 and y1 >= 1
    x0, y0, x1, y1 = caixa_pixels(100, 100, 1.0, 1.0, 0.5, 0.5)
    assert x1 == 100 and y1 == 100 and x0 >= 0


def test_max_cos_e_controle_outros_dias():
    base = np.eye(3, dtype=np.float32)
    v, j = max_cos(base, base)
    assert v.tolist() == [1, 1, 1] and j.tolist() == [0, 1, 2]
    dias = np.array(["a", "a", "b"])
    v, j = max_cos(base[:2], base, dias[:2], dias)
    assert v.tolist() == [0, 0] and j[0] in (2,)  # ignora o mesmo dia ("a"): só sobra o dia "b"


def test_faixas_de_tamanho():
    areas = np.arange(1, 10, dtype=float)
    c = terços(areas)
    f = faixa_tamanho(areas, c)
    assert set(f) == {"pequena", "media", "grande"} and f[0] == "pequena" and f[-1] == "grande"


def test_bootstrap_reproduzivel_e_sinal():
    rng = np.random.default_rng(0)
    novo = rng.normal(0.5, 0.05, 200)
    antigo = rng.normal(0.8, 0.05, 200)
    img_n = np.repeat(np.arange(50), 4)
    img_a = np.repeat(np.arange(50), 4)
    a = bootstrap_dif_medianas(novo, img_n, antigo, img_a, n=200)
    b = bootstrap_dif_medianas(novo, img_n, antigo, img_a, n=200)
    assert a == b
    assert a["dif_mediana"] < -0.2 and a["ic95"][1] < 0


def test_analisar_recortes_exclui_d10_e_usa_so_treino():
    rng = np.random.default_rng(1)
    n = 60
    emb = rng.normal(size=(n, 8)).astype(np.float32)
    emb /= np.linalg.norm(emb, axis=1, keepdims=True)
    nomes = np.array([f"img{i // 2:02d}" for i in range(n)])
    dias = np.array([f"d{(i // 2) % 6}" for i in range(n)])
    split = np.where(np.arange(n) < 40, "train", np.where(np.arange(n) < 50, "val", "test"))
    r = analisar_recortes(emb, nomes, dias, split, split, np.arange(1, n + 1), excluir=("img00",))
    assert r["divisoes"]["nova"]["teste"]["n"] == 10
    assert "dif_medianas_nova_menos_antiga" in r
    # divisões iguais: diferença de medianas nula
    assert r["dif_medianas_nova_menos_antiga"]["dif_mediana"] == 0
