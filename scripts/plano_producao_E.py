"""Plano de produção do braço E (adendo 4a, seção 10), fixado ANTES da primeira geração.

Lê a lista elegível (1.370 fontes, `manifests/lista_elegivel_4a.csv`) e grava um plano com, para cada geração:
passagem, posição na ordem, fonte, estrato (padrão ou risco) e semente mestra do iflens daquela passagem.

Regras (4a §10, todas já lacradas; aqui só se fixam os números que o 4a deixou para "lista de sementes registrada antes de gerar"):
  ordem das fontes        sorteio sem reposição da lista elegível, `random.Random(20261202).sample`, igual nas duas passagens;
  estrato                 exatamente 20% de cada passagem em risco (274 de 1.370), escolhidos por `random.Random(20261210)` sobre as
                          posições, uma vez por passagem (a semente da passagem 2 é a da passagem 1 + 1); 80% padrão;
  semente mestra iflens   20261208 na passagem 1 e 20261209 na passagem 2. A variação de condição do iflens depende de (semente mestra,
                          nome da imagem), então a mesma fonte recebe condição NOVA na passagem 2 (4a §10), e as condições de toda a
                          produção ficam determinadas por este arquivo;
  passagem 2              só se, ao fim da passagem 1, houver menos de 1.370 válidas; o plano a registra desde já, para não decidir depois.
O plano não depende de nenhuma imagem gerada nem de nenhuma avaliação.

Uso: python -m scripts.plano_producao_E --lista manifests/lista_elegivel_4a.csv --saida manifests/plano_producao_E_seed20261202.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

from scripts._hashes import RAIZ, sha256

SEMENTE_ORDEM = 20261202
SEMENTE_ESTRATO = 20261210
SEMENTES_MESTRAS = {1: 20261208, 2: 20261209}
FRACAO_RISCO = 0.20
N_ALVO = 1370


def ordem_fontes(nomes: list[str], semente: int = SEMENTE_ORDEM) -> list[str]:
    return random.Random(semente).sample(sorted(nomes), len(nomes))


def estratos(n: int, semente: int) -> list[str]:
    n_risco = round(FRACAO_RISCO * n)
    risco = set(random.Random(semente).sample(range(n), n_risco))
    return ["risco" if i in risco else "padrao" for i in range(n)]


def montar_plano(nomes: list[str]) -> list[dict]:
    ordem = ordem_fontes(nomes)
    linhas = []
    for passagem in (1, 2):
        est = estratos(len(ordem), SEMENTE_ESTRATO + passagem - 1)
        for pos, (nome, e) in enumerate(zip(ordem, est), 1):
            linhas.append({"geracao": len(linhas) + 1, "passagem": passagem, "posicao": pos, "nome": nome, "estrato": e,
                           "semente_mestra": SEMENTES_MESTRAS[passagem]})
    return linhas


def principal(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lista", default=str(RAIZ / "manifests" / "lista_elegivel_4a.csv"))
    ap.add_argument("--saida", default=str(RAIZ / "manifests" / "plano_producao_E_seed20261202.csv"))
    a = ap.parse_args(argv)
    saida = Path(a.saida)
    if saida.exists():
        print(f"{saida} já existe; recuso sobrescrever.", file=sys.stderr)
        return 2
    nomes = [r["nome"] for r in csv.DictReader(open(a.lista, encoding="utf-8", newline=""))]
    if len(nomes) != N_ALVO or len(set(nomes)) != N_ALVO:
        print(f"a lista elegível deveria ter {N_ALVO} fontes distintas; tem {len(nomes)}", file=sys.stderr)
        return 1
    linhas = montar_plano(nomes)
    with open(saida, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    rel = {"lista_sha256": sha256(Path(a.lista)), "plano_sha256": sha256(saida), "n_geracoes": len(linhas),
           "semente_ordem": SEMENTE_ORDEM, "semente_estrato": SEMENTE_ESTRATO, "sementes_mestras": SEMENTES_MESTRAS,
           "risco_por_passagem": {p: sum(r["estrato"] == "risco" for r in linhas if r["passagem"] == p) for p in (1, 2)}}
    saida.with_suffix(".relatorio.json").write_text(json.dumps(rel, indent=1), encoding="utf-8")
    print(json.dumps(rel, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
