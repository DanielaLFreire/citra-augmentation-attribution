"""Utilitários comuns de hash e do arquivo docs/pre_registro/hashes.json."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HASHES = RAIZ / "docs" / "pre_registro" / "hashes.json"


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def relativo(caminho: Path, raiz: Path = RAIZ) -> str:
    try:
        return str(Path(caminho).resolve().relative_to(raiz))
    except ValueError:
        return str(caminho)


def carregar(hashes_json: Path = HASHES) -> dict:
    if Path(hashes_json).exists():
        return json.loads(Path(hashes_json).read_text(encoding="utf-8"))
    return {}


def salvar(registro: dict, hashes_json: Path = HASHES) -> None:
    Path(hashes_json).write_text(json.dumps(registro, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
