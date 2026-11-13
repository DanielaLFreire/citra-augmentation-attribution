import csv
import json

import cv2
import numpy as np

from scripts import auditoria_recortes_iflens as aud


def _montar(tmp_path):
    orig = tmp_path / "orig"; orig.mkdir()
    for nome in ("a", "b"):
        cv2.imwrite(str(orig / f"{nome}.png"), np.full((270, 480, 3), 120, np.uint8))
        (orig / f"{nome}.txt").write_text("0 0.5 0.5 0.1 0.1\n0 0.2 0.3 0.05 0.05\n")
    saidas = []
    for i, h in enumerate(("h1", "h2")):
        d = tmp_path / f"s{i}"; d.mkdir(); saidas.append(str(d))
        for nome in ("a", "b"):
            cv2.imwrite(str(d / f"AUG_{nome}.png"), np.full((300, 533, 3), 90, np.uint8))
            (d / f"AUG_{nome}.json").write_text(json.dumps({"status": "ok", "image": f"{nome}.png", "output_file": f"AUG_{nome}.png",
                                                            "base_prompt_sha256": h, "original_conditions": {}, "variation_conditions": {}}))
    return orig, saidas


def test_wilson():
    lo, hi = aud.wilson(2, 10)
    assert 0.05 < lo < 0.2 < hi < 0.55
    assert aud.wilson(0, 0)[0] != aud.wilson(0, 0)[0]  # nan


def test_recorte_dentro_da_imagem():
    x0, y0, x1, y1 = aud.recorte_norm(0.99, 0.01, 0.02, 0.02, 480, 270)
    assert 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1


def test_gerar_e_resumir(tmp_path):
    orig, saidas = _montar(tmp_path)
    out = tmp_path / "aud"
    assert aud.main(["gerar", "--saidas", *saidas, "--originais", str(orig), "--out", str(out), "--semente", "1"]) == 0
    assert len(list(out.glob("A*.png"))) == 4
    linhas = list(csv.DictReader(open(out / "auditoria_modelo.csv")))
    assert sum(r["tipo"] == "caixa" for r in linhas) == 8 and sum(r["tipo"] == "imagem" for r in linhas) == 4
    chave = {r["codigo"]: r["base_prompt_sha256"] for r in csv.DictReader(open(out / "chave_cega.csv"))}
    for r in linhas:  # preenche: prompt h2 tem uma imagem reprovada
        r["categoria"] = "0" if r["tipo"] == "imagem" else "valida"
    alvo = next(c for c, h in chave.items() if h == "h2")
    for r in linhas:
        if r["codigo"] == alvo and r["tipo"] == "caixa" and r["item"] == "1":
            r["categoria"] = "apagada"
    with open(out / "auditoria_modelo.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys())); w.writeheader(); w.writerows(linhas)
    assert aud.main(["resumir", "--csv", str(out / "auditoria_modelo.csv"), "--chave", str(out / "chave_cega.csv")]) == 0


def test_resumir_rejeita_categoria_invalida(tmp_path):
    orig, saidas = _montar(tmp_path); out = tmp_path / "aud"
    aud.main(["gerar", "--saidas", saidas[0], "--originais", str(orig), "--out", str(out), "--semente", "1"])
    linhas = list(csv.DictReader(open(out / "auditoria_modelo.csv")))
    linhas[0]["categoria"] = "talvez"
    with open(out / "auditoria_modelo.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys())); w.writeheader(); w.writerows(linhas)
    assert aud.main(["resumir", "--csv", str(out / "auditoria_modelo.csv"), "--chave", str(out / "chave_cega.csv")]) == 1
