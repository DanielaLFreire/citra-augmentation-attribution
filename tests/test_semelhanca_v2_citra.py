import json

import numpy as np

from scripts.semelhanca_v2_citra import amostrar_pares, analisar, limiares, otsu, pares_positivos, tau_de_rotulos, tempo


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


def test_otsu_separa_dois_modos():
    rng = np.random.default_rng(1)
    v = np.concatenate([rng.normal(0.3, 0.05, 500), rng.normal(0.9, 0.03, 500)])
    assert 0.4 < otsu(v) < 0.8


def test_amostrar_pares_estratos_e_reprodutivel():
    sims = np.linspace(0.5, 1.0, 80)
    a = amostrar_pares(sims)
    assert len(a) == 40 and len({i for i, _ in a}) == 40
    assert all(sum(1 for _, e in a if e == k) == 5 for k in range(8))
    assert a == amostrar_pares(sims)


def test_tau_de_rotulos():
    sims = [0.99, 0.97, 0.95, 0.93, 0.91, 0.80, 0.70, 0.60]
    assert tau_de_rotulos(sims, ["sim"] * 5 + ["nao"] * 3) == 0.91
    assert tau_de_rotulos(sims, ["nao"] * 8) is None
    assert tau_de_rotulos(sims, ["sim", "nao", "sim", "nao", "sim", "nao", "nao", "nao"]) is None


def test_calibrar_tres_limiares(tmp_path, capsys):
    import csv

    from scripts.semelhanca_v2_citra import calibrar

    sims = [0.99, 0.97, 0.95, 0.93, 0.91, 0.80, 0.70, 0.60]
    resp = ["sim", "mesmo_alvo", "sim", "mesmo_alvo", "sim", "cena", "nao", "nao"]
    with open(tmp_path / "c.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "split_esq", "nome_esq", "nome_dir_treino", "cosseno_cls", "estrato_octil"])
        for i, v in enumerate(sims):
            w.writerow([f"P{i + 1:02d}", "test", "a", "b", v, 0])
    with open(tmp_path / "f.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "resposta_sim_cena_nao", "observacao"])
        for i, r in enumerate(resp):
            w.writerow([f"P{i + 1:02d}", r, ""])
    calibrar(str(tmp_path / "c.csv"), str(tmp_path / "f.csv"))
    r = json.loads(capsys.readouterr().out)
    assert r["tau_objeto_principal"] == 0.91 and r["tau_estrito_so_sim"] is None and r["tau_fundo_sim_mesmo_alvo_cena"] == 0.80


def test_fracoes(tmp_path, capsys):
    import csv

    from scripts.semelhanca_v2_citra import fracoes

    with open(tmp_path / "q.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "nome", "max_sim_treino"])
        for sp, v in [("test", 0.9), ("test", 0.5), ("val", 0.95), ("val", 0.96)]:
            w.writerow([sp, "x", v])
    fracoes(str(tmp_path / "q.csv"), 0.9)
    r = json.loads(capsys.readouterr().out)
    assert r["test"]["tau_0.9000"]["acima"] == 1 and r["val"]["tau_0.9000"]["abaixo_ficam_no_subconjunto"] == 0


def test_wilson_e_newcombe():
    from scripts.semelhanca_v2_citra import newcombe, wilson

    lo, hi = wilson(26, 40)
    assert abs(lo - 0.495) < 0.002 and abs(hi - 0.779) < 0.002
    l, u = newcombe(26, 40, 26, 40)
    assert abs(l + u) < 1e-12 and u > 0
    assert newcombe(10, 40, 26, 40)[1] < 0


def test_aplicar_divisao(tmp_path):
    import csv

    import pytest

    from scripts.semelhanca_v2_citra import aplicar_divisao

    nomes = np.array(["a", "b"])
    with open(tmp_path / "d.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nome", "dia", "divisao"])
        w.writerows([["a", "x", "test"], ["b", "x", "train"]])
    assert list(aplicar_divisao(np.array(["train", "train"]), nomes, str(tmp_path / "d.csv"))) == ["test", "train"]
    with pytest.raises(ValueError):
        aplicar_divisao(np.array(["train"]), np.array(["z"]), str(tmp_path / "d.csv"))


def test_vazamento_residual(tmp_path, capsys):
    import csv

    from scripts.semelhanca_v2_citra import vazamento_residual

    with open(tmp_path / "c.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "split_esq", "nome_esq", "nome_dir_treino", "cosseno_cls", "estrato_octil"])
        for i in range(4):
            w.writerow([f"P{i + 1:02d}", "test", "01.01.2022-08-00-00", "02.01.2022-08-00-00", 0.9, 0])
    with open(tmp_path / "f.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "resposta_sim_cena_nao", "observacao"])
        for i, r in enumerate(["sim", "mesmo_alvo", "cena", "nao"]):
            w.writerow([f"P{i + 1:02d}", r, ""])
    vazamento_residual(str(tmp_path / "c.csv"), str(tmp_path / "f.csv"))
    r = json.loads(capsys.readouterr().out)
    assert r["mesmas_embarcacoes_nova"]["x"] == 2 and r["mesmo_dia_entre_pares"] == 0


def test_normalizar_resposta():
    from scripts.semelhanca_v2_citra import normalizar_resposta

    assert normalizar_resposta(" Não ") == "nao" and normalizar_resposta("nao") == "nao"
    assert normalizar_resposta("mesmo_alvo") == "mesmo_alvo" and normalizar_resposta(None) == ""
