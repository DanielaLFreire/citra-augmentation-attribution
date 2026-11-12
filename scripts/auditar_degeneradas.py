"""Varre imagens procurando quadros degenerados (pretos, estourados, uniformes).

Para cada imagem: média e desvio-padrão do cinza (0-255), p1 e p99. Marca como degenerada se
desvio <= LIM_STD, ou média <= LIM_ESCURO, ou média >= LIM_CLARO. Os limites são ponto de partida e
NÃO foram calibrados: leia a lista visualmente antes de agir.

Uso (Colab):
  python -m scripts.auditar_degeneradas --raiz /content/drive/.../CITRA-3D-Real --saida /content/degeneradas_citra.csv
  python -m scripts.auditar_degeneradas --zip /content/drive/.../_zips/SeaShips_voc.zip --saida /content/degeneradas_seaships.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np
from PIL import Image

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp")
LIM_STD, LIM_ESCURO, LIM_CLARO = 4.0, 8.0, 247.0
CAMPOS = ["caminho", "split", "media", "desvio", "p1", "p99", "largura", "altura", "motivo"]


def estatisticas(dados: bytes) -> dict:
    with Image.open(io.BytesIO(dados)) as im:
        g = np.asarray(im.convert("L"), dtype=np.float64)
        larg, alt = im.size
    return {"media": round(float(g.mean()), 2), "desvio": round(float(g.std()), 2),
            "p1": float(np.percentile(g, 1)), "p99": float(np.percentile(g, 99)), "largura": larg, "altura": alt}


def motivo(e: dict) -> str:
    m = []
    if e["desvio"] <= LIM_STD: m.append("uniforme")
    if e["media"] <= LIM_ESCURO: m.append("escuro")
    if e["media"] >= LIM_CLARO: m.append("claro")
    return "+".join(m)


def _split(partes) -> str:
    if any(q in partes for q in ("_quarantine", "quarantine")): return "quarentena"
    return next((s for s in ("train", "valid", "val", "test") if s in partes), "")


def varrer_pasta(raiz: Path):
    for p in sorted(Path(raiz).rglob("*")):
        if p.suffix.lower() in IMG_EXT and "report" not in p.stem.lower():
            yield str(p), _split(p.parts), p.read_bytes()


def varrer_zip(caminho: Path):
    with zipfile.ZipFile(caminho) as z:
        for n in sorted(i.filename for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith(IMG_EXT)):
            yield n, _split(PurePosixPath(n).parts), z.read(n)


def auditar(fonte) -> tuple[list[dict], dict]:
    linhas, total, ilegiveis = [], 0, 0
    for caminho, split, dados in fonte:
        total += 1
        try:
            e = estatisticas(dados)
        except Exception:
            ilegiveis += 1
            linhas.append({"caminho": caminho, "split": split, "motivo": "ilegivel"} | {k: "" for k in CAMPOS if k not in ("caminho", "split", "motivo")})
            continue
        m = motivo(e)
        if m:
            linhas.append({"caminho": caminho, "split": split, "motivo": m} | e)
    resumo = {"n_imagens": total, "n_ilegiveis": ilegiveis, "n_degeneradas": len(linhas) - ilegiveis,
              "por_split": {}}
    for l in linhas:
        resumo["por_split"][l["split"]] = resumo["por_split"].get(l["split"], 0) + 1
    return linhas, resumo


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--raiz", type=Path); g.add_argument("--zip", type=Path)
    ap.add_argument("--saida", required=True, type=Path)
    a = ap.parse_args(argv)
    linhas, resumo = auditar(varrer_pasta(a.raiz) if a.raiz else varrer_zip(a.zip))
    with open(a.saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS); w.writeheader(); w.writerows(linhas)
    print(resumo)
    for l in linhas[:30]:
        print(l["split"], l["motivo"], l["media"], l["desvio"], l["caminho"][-70:])


if __name__ == "__main__":
    main()
