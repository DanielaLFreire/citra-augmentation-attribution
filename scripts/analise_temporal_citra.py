"""Mede a proximidade temporal entre os splits do CITRA a partir dos manifestos de labels_final.

Nomes de imagem = DD.MM.AAAA-HH-MM-SS. Para cada quadro de val/test, mede o intervalo até o quadro de
treino mais próximo e conta quantos dias aparecem em mais de um split. Só lê data/labels_final_citra.

Uso:  python -m scripts.analise_temporal_citra
"""
from __future__ import annotations

import bisect
import collections
import datetime as dt
import json
import statistics
from pathlib import Path

from scripts._hashes import RAIZ

FMT = "%d.%m.%Y-%H-%M-%S"


def carregar(pasta: Path) -> dict[str, list[dt.datetime]]:
    out = {}
    for s in ("train", "val", "test"):
        m = json.loads((pasta / f"labels_final_manifest_{s}.json").read_text(encoding="utf-8"))
        out[s] = sorted(dt.datetime.strptime(x["imagem_id"], FMT) for x in m["arquivos"])
    return out


def intervalos(ref: list[dt.datetime], alvo: list[dt.datetime]) -> list[float]:
    res = []
    for x in alvo:
        i = bisect.bisect_left(ref, x)
        c = []
        if i < len(ref):
            c.append((ref[i] - x).total_seconds())
        if i > 0:
            c.append((x - ref[i - 1]).total_seconds())
        res.append(min(c))
    return sorted(res)


def analisar(T: dict[str, list[dt.datetime]]) -> dict:
    dias = {s: {x.date() for x in v} for s, v in T.items()}
    todos = sorted(set().union(*dias.values()))
    r = {"n_dias": len(todos),
         "dias_em_mais_de_um_split": sum(1 for d in todos if sum(d in dias[s] for s in dias) > 1),
         "dias_nos_tres_splits": sum(1 for d in todos if all(d in dias[s] for s in dias))}
    for s in ("val", "test"):
        g = intervalos(T["train"], T[s])
        n = len(g)
        r[s] = {"n": n, "mediana_s": statistics.median(g), "minimo_s": g[0],
                "ate_60s": sum(x <= 60 for x in g) / n, "ate_300s": sum(x <= 300 for x in g) / n,
                "ate_3600s": sum(x <= 3600 for x in g) / n}
    return r


if __name__ == "__main__":
    print(json.dumps(analisar(carregar(RAIZ / "data" / "labels_final_citra")), indent=2))
