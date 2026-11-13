"""Planilha de recortes para a auditoria manual das imagens geradas pelo iflens (tarefa 10, parte manual).

Duas ações:
  gerar    Para cada registro AUG_*.json com status ok, monta uma folha PNG (imagem inteira original | gerada
           com as caixas de labels_final, e um recorte original | gerado por caixa, ampliado), identificada por
           um código embaralhado (cego ao prompt e à condição). Escreve auditoria_modelo.csv (para preencher)
           e chave_cega.csv (código -> prompt, condições; não abrir antes de terminar a auditoria).
  resumir  Lê o CSV preenchido e a chave e calcula, por prompt, a fração de imagens reprovadas com IC de Wilson 95%.

Categorias por caixa: valida, apagada, sem_objeto, deslocada, alterada, nao_avaliavel.
Por imagem: objeto_adicionado = 1 se há embarcação/boia/objeto novo sem caixa (0 caso contrário).
Reprovada = alguma caixa apagada/sem_objeto/deslocada/alterada OU objeto_adicionado = 1. A unidade de análise é
a imagem (caixas da mesma imagem não são independentes).

Uso (Colab ou local; só precisa de opencv e numpy):
  python -m scripts.auditoria_recortes_iflens gerar --saidas SAIDA1 [SAIDA2 ...] --originais DIR [--rotulos DIR] --out DIR --semente 42
  python -m scripts.auditoria_recortes_iflens resumir --csv DIR/auditoria_modelo.csv --chave DIR/chave_cega.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

CATEGORIAS = ["valida", "apagada", "sem_objeto", "deslocada", "alterada", "nao_avaliavel"]
INVALIDAS = {"apagada", "sem_objeto", "deslocada", "alterada"}
LARGURA_INTEIRA = 800
ALTURA_RECORTE = 240
MIN_LADO_PX = 96


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def ler_caixas(txt: Path) -> list[tuple[int, float, float, float, float]]:
    caixas = []
    if txt.exists():
        for linha in txt.read_text(encoding="utf-8").splitlines():
            p = linha.split()
            if len(p) >= 5:
                caixas.append((int(float(p[0])), *map(float, p[1:5])))
    return caixas


def recorte_norm(cx, cy, bw, bh, w, h):
    """Região normalizada (x0, y0, x1, y1) em torno da caixa: margem de 50% e lado mínimo de MIN_LADO_PX."""
    lw = max(bw * 2.0, MIN_LADO_PX / w)
    lh = max(bh * 2.0, MIN_LADO_PX / h)
    x0, x1 = cx - lw / 2, cx + lw / 2
    y0, y1 = cy - lh / 2, cy + lh / 2
    if x0 < 0: x1 -= x0; x0 = 0.0
    if y0 < 0: y1 -= y0; y0 = 0.0
    if x1 > 1: x0 -= x1 - 1; x1 = 1.0
    if y1 > 1: y0 -= y1 - 1; y0 = max(0.0, y0); y1 = 1.0
    return max(0.0, x0), max(0.0, y0), min(1.0, x1), min(1.0, y1)


def _texto(cv2, im, txt, y=16):
    cv2.rectangle(im, (0, y - 14), (im.shape[1], y + 4), (0, 0, 0), -1)
    cv2.putText(im, txt, (4, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


def folha(cv2, np, orig, ger, caixas, codigo):
    def inteira(im, titulo):
        h0, w0 = im.shape[:2]
        e = LARGURA_INTEIRA / w0
        im = cv2.resize(im, (LARGURA_INTEIRA, round(h0 * e)), interpolation=cv2.INTER_AREA)
        h, w = im.shape[:2]
        for i, (_, cx, cy, bw, bh) in enumerate(caixas, 1):
            p1 = (int((cx - bw / 2) * w), int((cy - bh / 2) * h)); p2 = (int((cx + bw / 2) * w), int((cy + bh / 2) * h))
            cv2.rectangle(im, p1, p2, (0, 0, 255), 1)
            cv2.putText(im, str(i), (p1[0], max(12, p1[1] - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        _texto(cv2, im, titulo)
        return im

    a, b = inteira(orig, f"{codigo} ORIGINAL"), inteira(ger, f"{codigo} GERADA")
    if a.shape[0] != b.shape[0]:
        b = cv2.resize(b, (a.shape[1], a.shape[0]))
    topo = np.hstack([a, b])
    linhas = []
    for i, (cls, cx, cy, bw, bh) in enumerate(caixas, 1):
        pares = []
        for im, nome in ((orig, "orig"), (ger, "gerada")):
            h, w = im.shape[:2]
            x0, y0, x1, y1 = recorte_norm(cx, cy, bw, bh, orig.shape[1], orig.shape[0])
            rec = im[int(y0 * h):max(int(y1 * h), int(y0 * h) + 1), int(x0 * w):max(int(x1 * w), int(x0 * w) + 1)]
            e = ALTURA_RECORTE / rec.shape[0]
            rec = cv2.resize(rec, (max(1, min(LARGURA_INTEIRA - 8, round(rec.shape[1] * e))), ALTURA_RECORTE), interpolation=cv2.INTER_CUBIC)
            _texto(cv2, rec, f"caixa {i} {nome}")
            pares.append(rec)
        linha = np.hstack([pares[0], np.zeros((ALTURA_RECORTE, 8, 3), np.uint8), pares[1]])
        linhas.append(linha)
    largura = topo.shape[1]
    corpo = []
    for l in linhas:
        if l.shape[1] < largura:
            l = np.hstack([l, np.zeros((l.shape[0], largura - l.shape[1], 3), np.uint8)])
        corpo.append(l[:, :largura])
    return np.vstack([topo] + corpo)


def gerar(args) -> int:
    import cv2
    import numpy as np
    regs = []
    for s in args.saidas:
        for f in sorted(Path(s).rglob("AUG_*.json")):
            r = json.loads(f.read_text(encoding="utf-8"))
            if r.get("status") == "ok":
                r["_dir"] = str(f.parent); r["_json"] = str(f)
                regs.append(r)
    if not regs:
        print("nenhum registro ok encontrado"); return 1
    ordem = list(range(len(regs)))
    random.Random(args.semente).shuffle(ordem)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rot = Path(args.rotulos or args.originais)
    modelo, chave = [], []
    for n, idx in enumerate(ordem, 1):
        r = regs[idx]; codigo = f"A{n:03d}"
        stem = Path(r["image"]).stem
        orig = cv2.imread(str(Path(args.originais) / r["image"])); ger = cv2.imread(str(Path(r["_dir"]) / r["output_file"]))
        if orig is None or ger is None:
            print(f"- pulado {codigo}: imagem ausente ({r['image']})"); continue
        caixas = ler_caixas(rot / f"{stem}.txt")
        cv2.imwrite(str(out / f"{codigo}.png"), folha(cv2, np, orig, ger, caixas, codigo))
        for i, (cls, *_ ) in enumerate(caixas, 1):
            modelo.append({"codigo": codigo, "tipo": "caixa", "item": i, "classe": cls, "categoria": "", "observacao": ""})
        modelo.append({"codigo": codigo, "tipo": "imagem", "item": 0, "classe": "", "categoria": "", "observacao": ""})
        chave.append({"codigo": codigo, "imagem": r["image"], "base_prompt_sha256": r.get("base_prompt_sha256", ""),
                      "saida": r["_dir"], "original_conditions": json.dumps(r.get("original_conditions", {})),
                      "variation_conditions": json.dumps(r.get("variation_conditions", {})), "response_id": r.get("response_id", "")})
    for nome, linhas, campos in (("auditoria_modelo.csv", modelo, ["codigo", "tipo", "item", "classe", "categoria", "observacao"]),
                                 ("chave_cega.csv", chave, list(chave[0].keys()) if chave else [])):
        with open(out / nome, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=campos); w.writeheader(); w.writerows(linhas)
    print(f"{len(chave)} folhas em {out}. Preencha auditoria_modelo.csv: caixa -> categoria em {CATEGORIAS}; "
          "imagem -> categoria = 0 ou 1 (objeto_adicionado). Não abra chave_cega.csv antes de terminar.")
    return 0


def resumir(args) -> int:
    chave = {r["codigo"]: r for r in csv.DictReader(open(args.chave, encoding="utf-8"))}
    por_img: dict[str, dict] = defaultdict(lambda: {"caixas": [], "adicionado": None})
    for r in csv.DictReader(open(args.csv, encoding="utf-8")):
        cat = r["categoria"].strip().lower()
        if not cat:
            continue
        if r["tipo"] == "caixa":
            if cat not in CATEGORIAS:
                print(f"categoria inválida {cat!r} em {r['codigo']} caixa {r['item']}"); return 1
            por_img[r["codigo"]]["caixas"].append(cat)
        else:
            if cat not in {"0", "1"}:
                print(f"objeto_adicionado deve ser 0 ou 1 em {r['codigo']}"); return 1
            por_img[r["codigo"]]["adicionado"] = int(cat)
    faltam = [c for c in chave if c not in por_img or por_img[c]["adicionado"] is None]
    if faltam:
        print(f"{len(faltam)} imagens sem auditoria completa (ex.: {faltam[:5]})")
    grupos: dict[str, dict] = defaultdict(lambda: {"n": 0, "reprov": 0, "adic": 0, "cx": 0, "cx_inv": 0})
    for c, d in por_img.items():
        if c not in chave or d["adicionado"] is None:
            continue
        g = grupos[chave[c]["base_prompt_sha256"] or "(prompt padrão)"]
        av = [x for x in d["caixas"] if x != "nao_avaliavel"]
        inv = sum(x in INVALIDAS for x in av)
        g["n"] += 1; g["adic"] += d["adicionado"]; g["cx"] += len(av); g["cx_inv"] += inv
        g["reprov"] += int(inv > 0 or d["adicionado"] == 1)
    print("prompt (SHA-256)           imagens  reprovadas (IC95% Wilson)    c/ objeto adicionado   caixas inválidas/avaliáveis")
    for h, g in sorted(grupos.items()):
        lo, hi = wilson(g["reprov"], g["n"])
        print(f"{h[:24]:<26} {g['n']:>7}  {g['reprov']:>3} = {g['reprov']/g['n']:.0%} ({lo:.0%}–{hi:.0%})   {g['adic']:>3}                    {g['cx_inv']}/{g['cx']}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="acao", required=True)
    g = sub.add_parser("gerar")
    g.add_argument("--saidas", nargs="+", required=True); g.add_argument("--originais", required=True)
    g.add_argument("--rotulos"); g.add_argument("--out", required=True); g.add_argument("--semente", type=int, required=True)
    r = sub.add_parser("resumir")
    r.add_argument("--csv", required=True); r.add_argument("--chave", required=True)
    a = p.parse_args(argv)
    return gerar(a) if a.acao == "gerar" else resumir(a)


if __name__ == "__main__":
    sys.exit(main())
