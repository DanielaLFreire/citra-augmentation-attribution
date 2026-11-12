"""Gera a lista de exclusão do pool do braço R pela regra A13 (D08).

Regra: sai do pool toda imagem marcada com quase-cópia do CITRA (dHash, Hamming <= 4), sem exceção.
No SeaShips a exclusão vale para o nome-base inteiro (todas as versões Roboflow de uma imagem marcada).
Só lê os manifestos; não toca em imagens. Saída com hash registrado depois por registrar_artefato.

Uso:  python -m scripts.gerar_exclusao_a13
"""
from __future__ import annotations

import csv
from pathlib import Path

from scripts._hashes import RAIZ

FONTES = ("smd", "seaships", "aboships", "inatechships")
CAMPOS = ["fonte", "id_imagem", "caminho_relativo", "sha256_conteudo", "colide_citra", "motivo"]


def excluidas(fonte: str, linhas: list[dict]) -> list[dict]:
    if fonte == "seaships":
        bases = {r["base_roboflow"] for r in linhas if r["colide_citra"] and r["base_roboflow"]}
        sel = [(r, "nome-base marcado" if r["colide_citra"] else "outra versão de nome-base marcado")
               for r in linhas if r["base_roboflow"] in bases]
    else:
        sel = [(r, "dHash<=4 com CITRA") for r in linhas if r["colide_citra"]]
    return [{"fonte": fonte, "id_imagem": r["id_imagem"], "caminho_relativo": r["caminho_relativo"],
             "sha256_conteudo": r["sha256_conteudo"], "colide_citra": r["colide_citra"], "motivo": m} for r, m in sel]


def gerar(raiz: Path = RAIZ) -> Path:
    saida = raiz / "manifests" / "exclusao_R_A13.csv"
    todas: list[dict] = []
    for f in FONTES:
        with open(raiz / "manifests" / f"manifesto_{f}.csv", encoding="utf-8", newline="") as fh:
            todas += excluidas(f, list(csv.DictReader(fh)))
    todas.sort(key=lambda r: (r["fonte"], r["caminho_relativo"]))
    with open(saida, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS, lineterminator="\n")
        w.writeheader()
        w.writerows(todas)
    return saida


if __name__ == "__main__":
    p = gerar()
    n = sum(1 for _ in open(p, encoding="utf-8")) - 1
    print(f"{p}: {n} linhas")
