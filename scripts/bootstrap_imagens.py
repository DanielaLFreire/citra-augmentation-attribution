"""Incerteza de amostragem do teste (adendo 4b, seção 5.7): bootstrap por imagem da diferença R−C na AP50 própria.

Para cada reamostragem, sorteia com reposição as imagens do teste (as MESMAS imagens para todos os modelos, o que mantém o pareamento) e
recalcula a AP50 própria de cada modelo sobre as predições gravadas pelo avaliador; a estatística é a média sobre as sementes de R menos a
média sobre as sementes de C (planos `principal`; as réplicas de hardware ficam de fora). O casamento predição–caixa é por imagem, então ele
é calculado uma vez; a reamostragem só muda os pesos das imagens na curva de precisão e revocação.

É descritivo e SUBESTIMA a incerteza: imagens do mesmo dia e da mesma sequência são correlacionadas, e com 3 dias não há como reamostrar por dia.
Não substitui o IC por sementes nem altera a conclusão primária.

Uso: python -m scripts.bootstrap_imagens --avaliacao <csv> --pasta-predicoes <pasta> --saida <json> [--reamostragens 10000] [--semente 20261123]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from scripts import avaliar_teste as v1
from scripts.avaliar_teste_v2 import carregar_predicoes

SEMENTE_PADRAO = 20261123
REAMOSTRAGENS_PADRAO = 10000


def casamentos(imagens: list[dict]) -> dict:
    """Por modelo: confianças e acertos de todas as predições (ordenados por confiança, estável), a imagem de cada uma e as caixas por imagem."""
    conf, tp, idx, n_gt = [], [], [], []
    for k, im in enumerate(imagens):
        gt = np.asarray(im["gt_xyxy"], dtype=float).reshape(-1, 4)
        pred = np.asarray(im["pred_xyxy"], dtype=float).reshape(-1, 4)
        c, t, _, _ = v1.casar_imagem(pred, im["pred_conf"], gt, np.zeros(len(gt), bool), np.zeros(len(pred), bool))
        conf.append(c)
        tp.append(t)
        idx.append(np.full(len(c), k))
        n_gt.append(len(gt))
    conf, tp, idx = (np.concatenate(x) if x else np.array([]) for x in (conf, tp, idx))
    ordem = np.argsort(-conf, kind="stable")
    return {"tp": tp[ordem].astype(float), "img": idx[ordem].astype(int), "n_gt": np.array(n_gt, dtype=float)}


def ap_ponderado(m: dict, pesos_imagem: np.ndarray) -> float:
    """AP50 (101 pontos) com cada imagem contada `pesos_imagem[k]` vezes. Com pesos 1 dá o mesmo valor de `v1.ap_de_curva`."""
    n_ref = float(pesos_imagem @ m["n_gt"])
    if n_ref == 0:
        return float("nan")
    w = pesos_imagem[m["img"]]
    tpc, fpc = np.cumsum(w * m["tp"]), np.cumsum(w * (1.0 - m["tp"]))
    rec = tpc / n_ref
    prec = tpc / np.maximum(tpc + fpc, 1e-12)
    mrec = np.concatenate(([0.0], rec, [1.0]))
    mpre = np.concatenate(([1.0], prec, [0.0]))
    mpre = np.flip(np.maximum.accumulate(np.flip(mpre)))
    x = np.linspace(0, 1, 101)
    integra = getattr(np, "trapezoid", None) or np.trapz
    return float(integra(np.interp(x, mrec, mpre), x))


def bootstrap(modelos_R: list[dict], modelos_C: list[dict], n_imagens: int, B: int = REAMOSTRAGENS_PADRAO,
              semente: int = SEMENTE_PADRAO) -> dict:
    """`modelos_*`: saídas de `casamentos`, uma por semente."""
    um = np.ones(n_imagens)
    ponto = float(np.mean([ap_ponderado(m, um) for m in modelos_R]) - np.mean([ap_ponderado(m, um) for m in modelos_C]))
    rng = np.random.default_rng(semente)
    dif = np.empty(B)
    for b in range(B):
        w = rng.multinomial(n_imagens, np.full(n_imagens, 1.0 / n_imagens)).astype(float)
        dif[b] = np.mean([ap_ponderado(m, w) for m in modelos_R]) - np.mean([ap_ponderado(m, w) for m in modelos_C])
    dif = dif[np.isfinite(dif)]
    return {"diferenca_pontual": ponto, "ic95_percentil": [float(np.percentile(dif, 2.5)), float(np.percentile(dif, 97.5))],
            "dp_bootstrap": float(dif.std(ddof=1)), "reamostragens": int(len(dif)), "semente": semente, "n_imagens": n_imagens,
            "estatistica": "média das sementes de R menos média das sementes de C, AP50 própria",
            "aviso": "descritivo; subestima a incerteza (imagens correlacionadas por dia e sequência; 3 dias)"}


def principal(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--avaliacao", required=True)
    p.add_argument("--pasta-predicoes", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--reamostragens", type=int, default=REAMOSTRAGENS_PADRAO)
    p.add_argument("--semente", type=int, default=SEMENTE_PADRAO)
    a = p.parse_args(argv)
    with open(a.avaliacao, newline="", encoding="utf-8") as f:
        ids = [r["id_execucao"] for r in csv.DictReader(f)]
    grupos = {"R": [], "C": []}
    n_imagens = None
    for i in ids:
        for b in grupos:
            if i.startswith(f"{b}_principal_"):
                itens = carregar_predicoes(Path(a.pasta_predicoes) / f"{i}.npz")
                if n_imagens is None:
                    n_imagens = len(itens)
                if len(itens) != n_imagens:
                    raise SystemExit(f"{i}: número de imagens diferente dos demais")
                grupos[b].append(casamentos(itens))
    if not grupos["R"] or not grupos["C"]:
        raise SystemExit("faltam modelos de R ou de C na avaliação")
    res = bootstrap(grupos["R"], grupos["C"], n_imagens, a.reamostragens, a.semente)
    res["n_modelos"] = {b: len(g) for b, g in grupos.items()}
    Path(a.saida).write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"diferenca_pp": round(100 * res["diferenca_pontual"], 3),
                      "ic95_pp": [round(100 * x, 3) for x in res["ic95_percentil"]]}, ensure_ascii=False))


if __name__ == "__main__":
    principal()
