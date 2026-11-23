"""Análise do experimento conforme o adendo 4, versão 2 (corrige a v1, `analisar_principal.py`, registrada em D58).

O que a v1 fazia de errado: dava veredito e p de Holm às métricas secundárias de R−C, e punha a AP50 própria (conferência da implementação)
na mesma família. O adendo 4 diz que as secundárias (recall small a conf 0,25 e AP50 small) são reportadas SEM teste de hipótese e sem
alterar a conclusão primária, e que o Holm vale entre os contrastes entre braços (E−C, G−C, E−R, G−R), rotulados secundários.

Aqui: (1) contraste primário R−C no mAP50 da API, regra do adendo 4, com sensibilidades; (2) métricas secundárias de R−C: só diferença e IC95%;
(3) AP50 própria: só verificação de consistência com o mAP50 da API; (4) contrastes secundários entre braços (os que existirem), mAP50 da API,
com Holm entre eles; (5) por dia e subconjunto, como na v1. As funções estatísticas são as da v1 (importadas, sem cópia).

Uso: python -m scripts.analisar_principal_v2 --avaliacao <csv> --saida <json> [--registro runs/REGISTRO_EXECUCOES.csv]
        [--contrastes E-C G-C E-R G-R] [--pasta-predicoes <pasta> --divisao-nova <csv> --divisao-antiga <csv>]
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy import stats

from scripts.analisar_principal import (MARGEM, analise_por_grupo, analise_principal, contraste_pareado, dias_e_subconjunto, holm,
                                        ler_avaliacao, por_braco)

SECUNDARIAS = ("recall_small_conf025", "AP50_small")
VERIFICACAO = "AP50_propria"
CONTRASTES_ENTRE_BRACOS = ("E-C", "G-C", "E-R", "G-R")


def descritivo(av: dict, braco_a: str, braco_b: str, metrica: str) -> dict:
    """Diferença média pareada por semente e IC95% (t, n−1 gl). Sem p, sem veredito."""
    A, B = por_braco(av, braco_a, metrica), por_braco(av, braco_b, metrica)
    s = sorted(set(A) & set(B))
    if len(s) < 3:
        raise ValueError(f"menos de 3 sementes em comum para {braco_a}-{braco_b}")
    d = np.array([A[i] - B[i] for i in s])
    ep = d.std(ddof=1) / np.sqrt(len(d))
    t = stats.t.ppf(0.975, len(d) - 1)
    return {"metrica": metrica, "contraste": f"{braco_a}-{braco_b}", "n": len(s), "diferenca": float(d.mean()),
            "ic95": (float(d.mean() - t * ep), float(d.mean() + t * ep))}


def contrastes_secundarios(av: dict, pares: list[str], margem: float = MARGEM, metrica: str = "mAP50_ultralytics") -> list[dict]:
    """Contrastes entre braços (mAP50 da API), rotulados secundários, com Holm entre eles. Só os pares com ≥3 sementes em comum."""
    saida = []
    for par in pares:
        a, b = par.split("-")
        try:
            r = analise_principal(av, a, b, metrica, margem=margem)
        except ValueError:
            continue
        saida.append({"contraste": par, "rotulo": "secundário", **r["principal"], "sementes": r["sementes"]})
    if saida:
        for r, q in zip(saida, holm([r["p_t_pareado"] for r in saida])):
            r["p_holm"] = q
    return saida


def analisar(av: dict, gpu: dict[str, str] | None = None, contrastes: list[str] | None = None, margem: float = MARGEM) -> dict:
    res = {"primaria": analise_principal(av, "R", "C", "mAP50_ultralytics", gpu_por_id=gpu, margem=margem),
           "secundarias_descritivas": [descritivo(av, "R", "C", m) for m in SECUNDARIAS],
           "verificacao_AP50_propria": {**descritivo(av, "R", "C", VERIFICACAO),
                                        "diferenca_do_mAP50_API": None},
           "contrastes_secundarios": contrastes_secundarios(av, contrastes or [], margem)}
    res["verificacao_AP50_propria"]["diferenca_do_mAP50_API"] = (res["verificacao_AP50_propria"]["diferenca"]
                                                               - res["primaria"]["principal"]["diferenca"])
    return res


def principal(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--avaliacao", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--registro", default=None)
    p.add_argument("--contrastes", nargs="*", default=[])
    p.add_argument("--pasta-predicoes", default=None)
    p.add_argument("--divisao-nova", default=None)
    p.add_argument("--divisao-antiga", default=None)
    a = p.parse_args(argv)
    if any(c not in CONTRASTES_ENTRE_BRACOS for c in a.contrastes):
        raise SystemExit(f"contrastes permitidos: {CONTRASTES_ENTRE_BRACOS}")
    av = ler_avaliacao(Path(a.avaliacao))
    gpu = {}
    if a.registro:
        with open(a.registro, newline="", encoding="utf-8") as f:
            gpu = {r["id_execucao"]: r["gpu"] for r in csv.DictReader(f)}
    res = analisar(av, gpu, a.contrastes)
    if a.pasta_predicoes and a.divisao_nova and a.divisao_antiga:
        res["por_grupo"] = analise_por_grupo(Path(a.pasta_predicoes), av, dias_e_subconjunto(Path(a.divisao_nova), Path(a.divisao_antiga)))
    Path(a.saida).write_text(json.dumps(res, indent=2, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    pr = res["primaria"]["principal"]
    print(json.dumps({"primaria": {"diferenca_pp": round(100 * pr["diferenca"], 3), "ic95_pp": [round(100 * x, 3) for x in pr["ic95"]],
                                   "conclusao": pr["conclusao"]},
                      "secundarias_descritivas": [{"metrica": s["metrica"], "diferenca_pp": round(100 * s["diferenca"], 3),
                                                  "ic95_pp": [round(100 * x, 3) for x in s["ic95"]]} for s in res["secundarias_descritivas"]]},
                     ensure_ascii=False))


if __name__ == "__main__":
    principal()
