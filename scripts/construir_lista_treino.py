"""Constrói a lista de treino de um braço (D35): uma "época" do Ultralytics com repetições.

O Ultralytics recebe uma lista de imagens e embaralha a cada época; não aceita uma lista de lotes.
Por isso a composição do treino é fixada **na lista**: o CITRA aparece `fator_citra` vezes por ciclo e as
externas 1 vez, e uma época de treino vale `ciclos_por_epoca` ciclos, de modo que o número de linhas seja
múltiplo do lote (sem lote quebrado). A ordem das linhas aqui é só determinística (por fonte e id); quem
embaralha é o treinador, com a semente da execução.

Planos (D35):
  principal: CITRA ×3 + 1.370 externas ×1 por ciclo; 2 ciclos por época = 10.960 linhas = 685 passos;
             37 épocas = 25.345 passos.
  reserva:   CITRA ×1 + 454 externas; 1 ciclo por época = 1.824 linhas = 114 passos; 222 épocas = 25.308 passos.
  f5_reproducao: braço C na divisão ANTIGA, como na Fase 5: real ×4 (1.348 imagens, com as 3 da D10), 5.392 linhas = 337
             passos; 75 épocas = 25.275 passos (D09, D43).

Braço C: no lugar das externas entram cópias extras do CITRA, sorteadas sem repetição com a semente. Com
n_ext = nº de imagens do CITRA (plano principal) o sorteio sem repetição é o conjunto inteiro, então C = CITRA ×4.

Uso:
  python -m scripts.construir_lista_treino <braco> <plano> <divisao.csv> <saida.csv> [<externas.csv> [<semente>]]
O CSV de externas tem a coluna id_imagem (e, opcionalmente, fonte). Escreve <saida.csv> e <saida>.relatorio.json.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

QUARENTENA_D10 = ("11.05.2022-14-13-13", "07.07.2022-09-39-44", "11.07.2022-09-43-17")
LOTE = 16
BRACOS = ("C", "R", "E", "G")
PLANOS = {
    "principal": {"fator_citra": 3, "n_ext": 1370, "ciclos_por_epoca": 2, "epocas": 37, "passos_por_epoca": 685,
                  "excluir_d10": True},
    "reserva": {"fator_citra": 1, "n_ext": 454, "ciclos_por_epoca": 1, "epocas": 222, "passos_por_epoca": 114,
                "excluir_d10": True},
    # Checagem de reprodutibilidade da D09: C na divisão antiga, como na Fase 5 (real x4, 75 épocas de 337 passos,
    # com as 3 imagens da D10 ainda no treino, pois a Fase 5 as usou).
    "f5_reproducao": {"fator_citra": 4, "n_ext": 0, "ciclos_por_epoca": 1, "epocas": 75, "passos_por_epoca": 337,
                      "excluir_d10": False},
}


def treino_efetivo(divisao_csv: Path, excluir=QUARENTENA_D10) -> list[str]:
    """Nomes (sem .png) do split de treino da divisão congelada, menos as imagens a excluir (D10)."""
    with open(divisao_csv, newline="", encoding="utf-8") as f:
        nomes = [r["nome"] for r in csv.DictReader(f) if r["divisao"] == "train"]
    return sorted(n for n in nomes if n not in set(excluir))


def ler_externas(caminho: Path, fonte_padrao: str) -> list[tuple[str, str]]:
    with open(caminho, newline="", encoding="utf-8") as f:
        return [(r["id_imagem"], r.get("fonte") or fonte_padrao) for r in csv.DictReader(f)]


def construir_lista(treino: list[str], externas: list[tuple[str, str]] | None, braco: str, *,
                    fator_citra: int, n_ext: int, ciclos_por_epoca: int, semente: int = 0,
                    lote: int = LOTE) -> list[dict]:
    """Linhas de UMA época: dicts com id_imagem, fonte, copia. Levanta ValueError se algo não fecha."""
    if braco not in BRACOS:
        raise ValueError(f"braço inválido: {braco}")
    if len(set(treino)) != len(treino):
        raise ValueError("ids de treino repetidos")
    if braco == "C":
        if externas:
            raise ValueError("o braço C não recebe externas")
        if n_ext > len(treino):
            raise ValueError("C: mais cópias extras que imagens do CITRA (sorteio sem repetição impossível)")
        rng = np.random.default_rng(semente)
        idx = sorted(rng.choice(len(treino), size=n_ext, replace=False).tolist())
        ext = [(treino[i], "citra_extra") for i in idx]
    else:
        if not externas:
            raise ValueError(f"o braço {braco} precisa da lista de externas")
        ids = [e[0] for e in externas]
        if len(set(ids)) != len(ids):
            raise ValueError("ids externos repetidos")
        if len(ids) != n_ext:
            raise ValueError(f"externas: {len(ids)} em vez de {n_ext} (N igual em todos os braços)")
        if set(ids) & set(treino):
            raise ValueError("externa com o mesmo id de uma imagem do CITRA")
        ext = list(externas)
    por_ciclo = [(i, "citra") for i in treino for _ in range(fator_citra)] + ext
    linhas = [t for _ in range(ciclos_por_epoca) for t in por_ciclo]
    if len(linhas) % lote:
        raise ValueError(f"{len(linhas)} linhas por época não é múltiplo do lote {lote}")
    linhas.sort()
    visto: Counter = Counter()
    saida = []
    for i, fonte in linhas:
        visto[(i, fonte)] += 1
        saida.append({"id_imagem": i, "fonte": fonte, "copia": visto[(i, fonte)]})
    return saida


def relatorio(linhas: list[dict], *, epocas: int, lote: int = LOTE) -> dict:
    por_fonte = Counter(r["fonte"] for r in linhas)
    n = len(linhas)
    externas = n - por_fonte.get("citra", 0)
    vezes = Counter(r["id_imagem"] for r in linhas)
    return {
        "linhas_por_epoca": n,
        "passos_por_epoca": n // lote,
        "epocas": epocas,
        "passos_total": (n // lote) * epocas,
        "lote": lote,
        "por_fonte": dict(por_fonte),
        "fracao_externa": round(externas / n, 4),
        "imagens_distintas": len(vezes),
        "vezes_por_imagem": dict(sorted(Counter(vezes.values()).items())),
    }


def principal(braco: str, plano: str, divisao_csv: str, saida_csv: str,
              externas_csv: str | None = None, semente: int = 0) -> dict:
    p = PLANOS[plano]
    treino = treino_efetivo(Path(divisao_csv), QUARENTENA_D10 if p.get("excluir_d10", True) else ())
    externas = ler_externas(Path(externas_csv), {"R": "publica", "E": "iflens", "G": "genship"}.get(braco, "")) \
        if externas_csv else None
    linhas = construir_lista(treino, externas, braco, fator_citra=p["fator_citra"], n_ext=p["n_ext"],
                             ciclos_por_epoca=p["ciclos_por_epoca"], semente=semente)
    saida = Path(saida_csv)
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ordem", "id_imagem", "fonte", "copia"])
        for k, r in enumerate(linhas, 1):
            w.writerow([k, r["id_imagem"], r["fonte"], r["copia"]])
    rel = relatorio(linhas, epocas=p["epocas"])
    rel.update({"braco": braco, "plano": plano, "semente_sorteio": semente, "n_treino_efetivo": len(treino),
                "parametros": p, "excluidas_d10": list(QUARENTENA_D10),
                "sha256_lista": hashlib.sha256(saida.read_bytes()).hexdigest()})
    saida.with_suffix(".relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=2), encoding="utf-8")
    return rel


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 4:
        sys.exit(__doc__)
    print(json.dumps(principal(a[0], a[1], a[2], a[3], a[4] if len(a) > 4 else None,
                               int(a[5]) if len(a) > 5 else 0), ensure_ascii=False, indent=2))
