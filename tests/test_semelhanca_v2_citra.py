import json

import numpy as np

from scripts.semelhanca_v2_citra import analisar, limiares, pares_positivos, tempo


def test_tempo_diferenca_em_segundos():
    assert tempo("14.04.2022-15-54-50") - tempo("14.04.2022-15-53-50") == 60


def test_pares_positivos_mesmo_dia_ate_60s():
    nomes = ["14.04.2022-15-53-50", "14.04.2022-15-54-50", "14.04.2022-15-55-52", "15.04.2022-15-53-50"]
    assert [tuple(p) for p in pares_positivos(nomes)] == [(0, 1)]


def test_limiares_percentis():
    r = limiares(np.arange(101, dtype=float))
    assert r == {"p5": 5.0, "p1": 1.0, "p10": 10.0}


def test_analisar_sintetico(tmp_path):
    rng = np.random.default_rng(0)
    base = rng.normal(size=(1, 8))
    nomes = ["14.04.2022-15-53-50", "14.04.2022-15-54-10", "14.04.2022-15-54-30", "16.04.2022-10-00-00"]
    split = ["train", "train", "test", "val"]
    cls = np.vstack([base, base + 0.01, base + 0.02, rng.normal(size=(1, 8))])
    np.savez(tmp_path / "e.npz", split=np.array(split), nome=np.array(nomes), cls=cls, patch_medio=cls)
    analisar(str(tmp_path / "e.npz"), str(tmp_path / "out"))
    r = json.load(open(tmp_path / "out" / "semelhanca_v2_resumo.json", encoding="utf-8"))
    assert r["n_pares_positivos"] == 3 and r["aviso"] is not None
    assert r["por_split"]["test"]["n"] == 1 and r["por_split"]["test"]["quantis_max_sim"]["50"] > 0.99
