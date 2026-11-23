import csv
import json

import numpy as np
import pytest

from scripts import avaliar_teste as v1
from scripts import avaliar_teste_v2 as v2
from scripts import bootstrap_imagens as bi


def _imagens(rng, n=40, acerto=0.8):
    itens = []
    for _ in range(n):
        k = int(rng.integers(0, 4))
        gt = np.array([[10 + 60 * j, 10, 50 + 60 * j, 50] for j in range(k)], dtype=float).reshape(-1, 4)
        pred, conf = [], []
        for g in gt:
            if rng.random() < acerto:
                pred.append(g + rng.normal(0, 1, 4)); conf.append(rng.uniform(0.3, 0.99))
        for _ in range(int(rng.integers(0, 3))):
            pred.append([200 + rng.uniform(0, 50), 100, 260 + rng.uniform(0, 50), 150]); conf.append(rng.uniform(0.001, 0.6))
        itens.append({"pred_xyxy": np.array(pred, float).reshape(-1, 4), "pred_conf": np.array(conf, float), "gt_xyxy": gt,
                      "largura": 640, "altura": 640})
    return itens


def test_ap_ponderado_com_pesos_1_igual_ao_v1():
    rng = np.random.default_rng(0)
    itens = _imagens(rng)
    m = bi.casamentos(itens)
    esperado = v1.medidas_proprias(itens)["AP50_propria"]
    assert bi.ap_ponderado(m, np.ones(len(itens))) == pytest.approx(esperado, abs=1e-12)


def test_ap_ponderado_com_pesos_inteiros_igual_a_replicar_imagens():
    rng = np.random.default_rng(1)
    itens = _imagens(rng, n=12)
    pesos = np.array([2, 0, 1, 3, 1, 0, 1, 2, 1, 1, 0, 1], dtype=float)
    replicadas = [it for it, w in zip(itens, pesos) for _ in range(int(w))]
    assert bi.ap_ponderado(bi.casamentos(itens), pesos) == pytest.approx(v1.medidas_proprias(replicadas)["AP50_propria"], abs=1e-12)
    assert np.isnan(bi.ap_ponderado(bi.casamentos(itens), np.zeros(len(itens))))


def test_bootstrap_reproduzivel_e_contem_o_ponto():
    rng = np.random.default_rng(2)
    r = [bi.casamentos(_imagens(np.random.default_rng(10 + s), acerto=0.85)) for s in range(3)]
    c = [bi.casamentos(_imagens(np.random.default_rng(20 + s), acerto=0.75)) for s in range(3)]
    a = bi.bootstrap(r, c, 40, B=200, semente=5)
    b = bi.bootstrap(r, c, 40, B=200, semente=5)
    assert a == b
    assert a["ic95_percentil"][0] < a["ic95_percentil"][1] and a["reamostragens"] == 200 and a["n_imagens"] == 40
    outro = bi.bootstrap(r, c, 40, B=200, semente=6)
    assert outro["ic95_percentil"] != a["ic95_percentil"]


def test_cli_ponta_a_ponta(tmp_path):
    pasta = tmp_path / "pred"
    pasta.mkdir()
    linhas = []
    for b, acerto in (("R", 0.85), ("C", 0.75)):
        for s in (1, 2, 3):
            i = f"{b}_principal_yolo11n_seed{s}"
            itens = _imagens(np.random.default_rng(100 * s + ord(b)), acerto=acerto)
            v2.salvar_predicoes(pasta / f"{i}.npz", [f"img{k}" for k in range(len(itens))], itens)
            linhas.append({"id_execucao": i})
    # a réplica de hardware não entra
    v2.salvar_predicoes(pasta / "C_principalL4_yolo11n_seed1.npz", ["a"], _imagens(np.random.default_rng(9), n=1))
    linhas.append({"id_execucao": "C_principalL4_yolo11n_seed1"})
    csv_ = tmp_path / "a.csv"
    with open(csv_, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id_execucao"]); w.writeheader(); w.writerows(linhas)
    saida = tmp_path / "s.json"
    bi.principal(["--avaliacao", str(csv_), "--pasta-predicoes", str(pasta), "--saida", str(saida), "--reamostragens", "50"])
    r = json.loads(saida.read_text())
    assert r["n_modelos"] == {"R": 3, "C": 3} and r["n_imagens"] == 40 and r["diferenca_pontual"] > 0
