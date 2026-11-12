"""Gera a lista de imagens externas do braço R (D13, D15), a partir dos manifestos.

Regras: fontes ABOShips + SMD, metade e metade (se uma não alcançar a metade, a outra completa);
elegíveis = com ao menos 1 caixa, legíveis, sem cópia exata/nome-base, fora de `exclusao_R_A13.csv`;
unidade independente = sessão (ABOShips: prefixo AAAAMMDDHHMM) ou vídeo (SMD: MVI_NNNN);
dentro da unidade, uma imagem por cluster de quase-duplicata; cota igual por unidade com o excedente
redistribuído; sorteio com semente explícita.

Uso:  python -m scripts.gerar_lista_r --seed 42 --n 1348 --saida manifests/lista_R_seed42.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import defaultdict
from pathlib import Path

from scripts._hashes import RAIZ

CAMPOS = ["fonte", "id_imagem", "caminho_relativo", "unidade", "sha256_conteudo", "n_caixas", "n_small_640"]
_UNIDADE = {"aboships": re.compile(r"/(\d{12})_\d+\.png$", re.I), "smd": re.compile(r"(MVI_\d+)")}


def unidade(fonte: str, caminho: str) -> str | None:
    m = _UNIDADE[fonte].search(caminho)
    return m.group(1) if m else None


def elegiveis(fonte: str, linhas: list[dict], excluidas: set[str]) -> dict[str, list[dict]]:
    por_unidade: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in sorted(linhas, key=lambda r: r["caminho_relativo"]):
        if (int(r["n_caixas"] or 0) < 1 or r["status_auditoria"] == "ilegivel" or r["dup_base_de"]
                or r["dup_conteudo_de"] or r["id_imagem"] in excluidas):
            continue
        u = unidade(fonte, r["caminho_relativo"])
        if u is None:
            continue
        por_unidade[u].setdefault(r["cluster_quase_dup"] or r["id_imagem"], r)  # 1 por cluster na unidade
    return {u: list(c.values()) for u, c in por_unidade.items()}


def cotas(tamanhos: dict[str, int], n: int) -> dict[str, int]:
    """Cota igual por unidade; quem tem menos que a cota entrega tudo e o excedente é redistribuído."""
    q: dict[str, int] = {}
    restante, pendentes = n, sorted(tamanhos, key=lambda u: (tamanhos[u], u))
    while pendentes:
        base = restante // len(pendentes)
        u = pendentes[0]
        if tamanhos[u] <= base:
            q[u] = tamanhos[u]
            restante -= tamanhos[u]
            pendentes.pop(0)
        else:
            resto = restante - base * len(pendentes)
            for k, v in enumerate(pendentes):
                q[v] = base + (1 if k < resto else 0)
            break
    return q


def sortear(por_unidade: dict[str, list[dict]], n: int, rng: random.Random) -> list[tuple[str, dict]]:
    q = cotas({u: len(v) for u, v in por_unidade.items()}, n)
    out = []
    for u in sorted(por_unidade):
        itens = sorted(por_unidade[u], key=lambda r: r["id_imagem"])
        rng.shuffle(itens)
        out += [(u, r) for r in itens[: q[u]]]
    return out


def gerar(raiz: Path, seed: int, n: int, saida: Path) -> dict:
    man = raiz / "manifests"
    excl = {r["id_imagem"] for r in csv.DictReader(open(man / "exclusao_R_A13.csv", encoding="utf-8"))}
    pools = {}
    for f in ("aboships", "smd"):
        with open(man / f"manifesto_{f}.csv", encoding="utf-8", newline="") as fh:
            pools[f] = elegiveis(f, list(csv.DictReader(fh)), excl)
    disp = {f: sum(len(v) for v in p.values()) for f, p in pools.items()}
    cota = {"aboships": n // 2, "smd": n - n // 2}
    for a, b in (("smd", "aboships"), ("aboships", "smd")):
        if disp[a] < cota[a]:
            cota[b] += cota[a] - disp[a]
            cota[a] = disp[a]
    rng = random.Random(seed)
    linhas, rel = [], {"seed": seed, "n_pedido": n, "disponiveis": disp, "cota_por_fonte": cota, "fontes": {}}
    for f in ("aboships", "smd"):
        sel = sortear(pools[f], cota[f], rng)
        rel["fontes"][f] = {"n": len(sel), "n_unidades_disponiveis": len(pools[f]),
                            "n_unidades_usadas": len({u for u, _ in sel}),
                            "caixas": sum(int(r["n_caixas"]) for _, r in sel),
                            "caixas_small": sum(int(r["n_small_640"]) for _, r in sel)}
        linhas += [{"fonte": f, "id_imagem": r["id_imagem"], "caminho_relativo": r["caminho_relativo"], "unidade": u,
                    "sha256_conteudo": r["sha256_conteudo"], "n_caixas": r["n_caixas"], "n_small_640": r["n_small_640"]}
                   for u, r in sel]
    with open(saida, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS, lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)
    Path(str(saida) + ".relatorio.json").write_text(json.dumps(rel, indent=2), encoding="utf-8")
    return rel


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", required=True, type=int)
    ap.add_argument("--n", type=int, default=1348)
    ap.add_argument("--saida", required=True, type=Path)
    a = ap.parse_args()
    print(json.dumps(gerar(RAIZ, a.seed, a.n, a.saida), indent=2))
