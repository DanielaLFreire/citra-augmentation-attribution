"""Compara os rótulos do experimento (CITRA-3D-Real/<split>/labels_final) com as três versões do espelho
(`navio/labels`, `navio/labels_pass_1`, `navio/labels_reviewed` dentro de citra-mirror.zip).

Compara por nome de imagem, como conjunto de caixas (x, y, w, h arredondados a 1e-4), ignorando a classe
(o experimento usa classe única; o espelho tem 9 classes). Grava um resumo JSON e a lista das diferenças.

Uso (Colab):
  python -m scripts.comparar_rotulos_mirror --zip <_zips>/citra-mirror.zip \\
      --raiz /content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real --saida <pasta>
"""
from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

VERSOES = ("labels", "labels_pass_1", "labels_reviewed")
SPLITS = ("train", "val", "valid", "test")


def caixas(texto: str) -> frozenset:
    out = []
    for linha in texto.replace("\r", "").splitlines():
        p = linha.split()
        if len(p) != 5:
            continue
        try:
            out.append(tuple(round(float(v), 4) for v in p[1:]))
        except ValueError:
            continue
    return frozenset(out)


def comparar(caminho_zip: Path, raiz: Path, saida: Path) -> dict:
    saida.mkdir(parents=True, exist_ok=True)
    espelho: dict[str, dict[str, frozenset]] = {v: {} for v in VERSOES}
    with zipfile.ZipFile(caminho_zip) as z:
        for i in z.infolist():
            p = PurePosixPath(i.filename)
            if i.is_dir() or p.suffix != ".txt" or "quarantine" in i.filename.lower():
                continue
            if p.parent.name in VERSOES:
                espelho[p.parent.name][p.stem] = caixas(z.read(i).decode("utf-8", "replace"))
    local: dict[str, frozenset] = {}
    split_de: dict[str, str] = {}
    for s in SPLITS:
        pasta = Path(raiz) / s / "labels_final"
        if pasta.is_dir():
            for f in pasta.glob("*.txt"):
                local[f.stem] = caixas(f.read_text(encoding="utf-8", errors="replace"))
                split_de[f.stem] = s
    res: dict = {"n_imagens_raiz": len(local), "n_por_split": dict(Counter(split_de.values())),
                 "n_caixas_raiz": sum(len(v) for v in local.values())}
    diferencas = []
    for v in VERSOES:
        m = espelho[v]
        c = Counter()
        for nome, cx in local.items():
            if nome not in m:
                c["ausente_no_espelho"] += 1
                continue
            if cx == m[nome]:
                c["igual"] += 1
            else:
                c["difere"] += 1
                if len(diferencas) < 300:
                    diferencas.append({"versao": v, "imagem": nome, "split": split_de[nome],
                                       "n_raiz": len(cx), "n_espelho": len(m[nome]),
                                       "so_na_raiz": len(cx - m[nome]), "so_no_espelho": len(m[nome] - cx)})
        c["so_no_espelho"] = len(set(m) - set(local))
        res[v] = {"n_imagens_espelho": len(m), "n_caixas_espelho": sum(len(x) for x in m.values()), **c}
    (saida / "comparacao_rotulos.json").write_text(json.dumps({"resumo": res, "diferencas": diferencas}, indent=1, ensure_ascii=False), encoding="utf-8")
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", required=True, type=Path)
    ap.add_argument("--raiz", required=True, type=Path)
    ap.add_argument("--saida", required=True, type=Path)
    a = ap.parse_args()
    print(json.dumps(comparar(a.zip, a.raiz, a.saida), indent=2, ensure_ascii=False))
