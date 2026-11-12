"""Lacra um ADENDO de pré-registro: grava o SHA-256 em docs/pre_registro/hashes.json.

Salvaguardas:
- recusa adendo com marcador de decisão pendente ("DECISÃO PENDENTE" ou "___");
- recusa re-lacração (correção = adendo novo);
- só acrescenta em `adendos`; nunca altera entradas existentes.

Uso:  python -m scripts.lacrar_adendo docs/pre_registro/adendo4_fontes_aumento.md
O commit público de hashes.json + adendo é a lacração.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts._hashes import HASHES, carregar, relativo, salvar, sha256

MARCADORES_PENDENTES = ("DECISÃO PENDENTE", "___")


def lacrar_adendo(caminho_adendo: Path, hashes_json: Path = HASHES) -> dict:
    caminho_adendo = Path(caminho_adendo)
    texto = caminho_adendo.read_text(encoding="utf-8")
    for marcador in MARCADORES_PENDENTES:
        if marcador in texto:
            raise ValueError(f"Adendo contém '{marcador}': resolva a decisão pendente antes de lacrar.")
    registro = carregar(hashes_json)
    registro.setdefault("artefatos", {})
    registro.setdefault("adendos", {})
    nome = caminho_adendo.name
    if nome in registro["adendos"]:
        raise ValueError(f"'{nome}' já está lacrado; correções vão em um novo adendo.")
    registro["adendos"][nome] = {
        "lacrado_em_utc": datetime.now(timezone.utc).isoformat(),
        "caminho": relativo(caminho_adendo),
        "sha256": sha256(caminho_adendo),
        "tamanho_bytes": caminho_adendo.stat().st_size,
    }
    salvar(registro, hashes_json)
    return registro["adendos"][nome]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: python -m scripts.lacrar_adendo <adendo.md>")
        sys.exit(2)
    e = lacrar_adendo(Path(sys.argv[1]))
    print(f"Adendo lacrado: {e['caminho']}\n  sha256: {e['sha256']}\nCommite hashes.json junto com o adendo.")
