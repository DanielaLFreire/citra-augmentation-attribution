"""Renderiza imagens subexpostas com contraste esticado e as caixas do rótulo desenhadas.

Serve para decidir, por inspeção visual, se o objeto rotulado existe na cena mesmo quando a imagem
original é quase preta. O esticamento é por imagem (branco = percentil 99,7 do cinza) e só para
visualização; nada é gravado de volta no dataset.

Uso (Colab):
  python -m scripts.inspecionar_escuras --raiz /content/drive/.../CITRA-3D-Real --saida /content/escuras \\
      --imagens train/11.05.2022-14-13-13 train/07.07.2022-09-39-44 test/11.07.2022-10-56-15
O rótulo lido é <raiz>/<split>/labels_final/<nome>.txt (formato YOLO).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


def esticar(img: Image.Image, pct: float = 99.7) -> Image.Image:
    a = np.asarray(img.convert("RGB"), dtype=np.float64)
    topo = max(float(np.percentile(a.max(axis=2), pct)), 1.0)
    return Image.fromarray(np.clip(a * (255.0 / topo), 0, 255).astype(np.uint8))


def ler_caixas(txt: Path, W: int, H: int):
    if not txt.exists():
        return None
    out = []
    for linha in txt.read_text().splitlines():
        p = linha.split()
        if len(p) >= 5:
            cx, cy, w, h = (float(v) for v in p[1:5])
            out.append(((cx - w / 2) * W, (cy - h / 2) * H, (cx + w / 2) * W, (cy + h / 2) * H))
    return out


def renderizar(raiz: Path, split: str, nome: str, saida: Path) -> dict:
    img_p = next(iter(sorted((Path(raiz) / split / "images").glob(f"{nome}.*"))), None)
    if img_p is None:
        raise FileNotFoundError(f"imagem não encontrada: {split}/{nome}")
    img = Image.open(img_p)
    W, H = img.size
    caixas = ler_caixas(Path(raiz) / split / "labels_final" / f"{nome}.txt", W, H)
    vis = esticar(img)
    d = ImageDraw.Draw(vis)
    for x0, y0, x1, y1 in caixas or []:
        d.rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], outline=(255, 255, 0), width=3)
    saida = Path(saida); saida.mkdir(parents=True, exist_ok=True)
    destino = saida / f"{split}_{nome}.png"
    vis.save(destino)
    return {"arquivo": str(destino), "n_caixas": None if caixas is None else len(caixas), "tamanho": (W, H)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", required=True, type=Path)
    ap.add_argument("--saida", required=True, type=Path)
    ap.add_argument("--imagens", nargs="+", required=True, help="split/nome, sem extensão")
    a = ap.parse_args(argv)
    for item in a.imagens:
        split, nome = item.split("/", 1)
        print(renderizar(a.raiz, split, nome, a.saida))


if __name__ == "__main__":
    main()
