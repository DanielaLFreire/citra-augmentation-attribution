"""Registra o SHA-256 de um artefato (manifesto, lista de treino, configuração) em hashes.json.

Recusa re-registrar um nome existente (amostra nova = adendo novo).
Uso:  python -m scripts.registrar_artefato manifests/lista_treino_C.csv
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts._hashes import HASHES, carregar, relativo, salvar, sha256


def registrar_artefato(caminho: Path, hashes_json: Path = HASHES, nome: str | None = None) -> dict:
    caminho = Path(caminho)
    if not caminho.is_file():
        raise FileNotFoundError(f"Artefato não encontrado: {caminho}")
    nome = nome or caminho.name
    registro = carregar(hashes_json)
    registro.setdefault("artefatos", {})
    registro.setdefault("adendos", {})
    if nome in registro["artefatos"]:
        raise ValueError(f"'{nome}' já está registrado; uma amostra nova exige adendo novo.")
    registro["artefatos"][nome] = {
        "registrado_em_utc": datetime.now(timezone.utc).isoformat(),
        "caminho": relativo(caminho),
        "sha256": sha256(caminho),
        "tamanho_bytes": caminho.stat().st_size,
    }
    salvar(registro, hashes_json)
    return registro["artefatos"][nome]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: python -m scripts.registrar_artefato <arquivo>")
        sys.exit(2)
    e = registrar_artefato(Path(sys.argv[1]))
    print(f"Registrado: {e['caminho']}\n  sha256: {e['sha256']}")
