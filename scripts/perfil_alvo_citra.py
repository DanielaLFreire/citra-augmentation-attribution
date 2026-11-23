"""Perfil do alvo (CITRA-3D-Real) só com o split de TREINO: resolução, caixas por imagem e tamanho das caixas.

Serve para descrever o domínio-alvo a quem vai gerar imagens sintéticas (GenShip) ou editadas, sem olhar o teste.
Lê só o cabeçalho das imagens (tamanho) e os rótulos de `labels_final`. Não treina nem avalia nada.

Uso (Colab): python -m scripts.perfil_alvo_citra --raiz <CITRA-3D-Real> --divisao <divisao_blocos_dias.csv> --saida perfil_alvo_citra_treino.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np

from scripts.avaliar_teste import LIMITE_SMALL, area_640, ler_rotulo_yolo


def perfil(itens: list[dict]) -> dict:
    """`itens`: dicts com largura, altura e gt_xyxy (pixels originais). Só estatísticas descritivas."""
    tamanhos = Counter(f"{i['largura']}x{i['altura']}" for i in itens)
    por_imagem = np.array([len(i["gt_xyxy"]) for i in itens])
    w, h, a640 = [], [], []
    for i in itens:
        c = np.asarray(i["gt_xyxy"], dtype=float).reshape(-1, 4)
        if len(c):
            w += list(c[:, 2] - c[:, 0])
            h += list(c[:, 3] - c[:, 1])
            a640 += list(area_640(c, i["largura"], i["altura"]))
    q = lambda v: {k: round(float(np.percentile(v, p)), 1) for k, p in (("p05", 5), ("p25", 25), ("mediana", 50), ("p75", 75), ("p95", 95))}  # noqa: E731
    return {
        "n_imagens": len(itens), "tamanhos_imagem": dict(tamanhos), "n_caixas": int(por_imagem.sum()),
        "caixas_por_imagem": {"media": round(float(por_imagem.mean()), 2), "max": int(por_imagem.max()),
                              "sem_caixa": int((por_imagem == 0).sum()), **q(por_imagem)} if len(itens) else {},
        "largura_caixa_px": q(w) if w else {}, "altura_caixa_px": q(h) if h else {},
        "fracao_small_640": round(float(np.mean(np.array(a640) < LIMITE_SMALL)), 4) if a640 else None,
    }


def principal(argv=None) -> None:
    from PIL import Image

    from scripts.executar_treino import ler_divisao
    from scripts.teste_epoca_ultralytics import indexar

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--raiz", required=True)
    p.add_argument("--divisao", required=True)
    p.add_argument("--saida", required=True)
    a = p.parse_args(argv)
    nomes = sorted(ler_divisao(Path(a.divisao))["train"])
    imagens, rotulos = indexar(Path(a.raiz))
    itens = []
    for n in nomes:
        if n not in imagens or n not in rotulos:
            continue
        with Image.open(imagens[n]) as im:
            larg, alt = im.size
        itens.append({"largura": larg, "altura": alt, "gt_xyxy": ler_rotulo_yolo(rotulos[n], larg, alt)})
    res = perfil(itens)
    res["split"] = "train"
    res["nomes_na_divisao"] = len(nomes)
    Path(a.saida).write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    principal()
