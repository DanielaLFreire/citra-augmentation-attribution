"""Confere hashes.json contra os arquivos do repositório.

Sai com código 1 se algum artefato/adendo registrado sumiu ou mudou.
Também confere data/*/PROVENIENCIA.json (arquivos herdados) quando existir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from scripts._hashes import HASHES, RAIZ, carregar, sha256


def verificar(hashes_json: Path = HASHES, raiz: Path = RAIZ) -> list[str]:
    erros: list[str] = []
    registro = carregar(hashes_json)
    for secao in ("artefatos", "adendos"):
        for nome, e in registro.get(secao, {}).items():
            caminho = raiz / e["caminho"]
            if not caminho.is_file():
                erros.append(f"{secao}/{nome}: arquivo ausente ({e['caminho']})")
            elif sha256(caminho) != e["sha256"]:
                erros.append(f"{secao}/{nome}: hash difere do registrado ({e['caminho']})")
    for prov in sorted((raiz / "data").glob("*/PROVENIENCIA.json")):
        dados = json.loads(prov.read_text(encoding="utf-8"))
        for arq, h in dados.get("arquivos", {}).items():
            caminho = prov.parent / arq
            if not caminho.is_file():
                erros.append(f"{prov.parent.name}/{arq}: ausente")
            elif sha256(caminho) != h:
                erros.append(f"{prov.parent.name}/{arq}: hash difere da proveniência")
    return erros


if __name__ == "__main__":
    erros = verificar()
    if erros:
        print("FALHA de integridade:")
        for e in erros:
            print("  -", e)
        sys.exit(1)
    print("Integridade OK.")
