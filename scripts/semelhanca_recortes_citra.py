"""Semelhança no nível do recorte da embarcação (D39): responde à crítica de que o fundo predomina na medida da imagem inteira.

Dois passos, ambos fixados na D39 antes de gerar dados:
1. `extrair <CITRA-3D.zip> <pasta_rotulos> <saida.npz>` (Colab, GPU): para cada caixa de `labels_final` (YOLO, classe única) das
   imagens reais, recorte = caixa + margem de 20% de cada lado (clampada à imagem), redimensionado para 224x224 (sem manter a
   proporção), DINOv2-base fp32, token CLS normalizado (L2). Guarda nome, índice da caixa, geometria, split original e vetores.
2. `analise <recortes.npz> <divisao_nova.csv> <pasta_saida>` (sem GPU): para cada caixa de teste, maior cosseno com as caixas do
   treino (divisão antiga e nova); quantis, por terço de tamanho da caixa; controle (caixas de treino contra caixas de treino de
   OUTROS dias); diferença de medianas nova - antiga com bootstrap por imagem (2.000, semente 2026). Descritivo: sem limiar.
Limites: o recorte compara aparência, não identidade (embarcações do mesmo tipo podem parecer iguais); o bootstrap por imagem
subestima a incerteza (imagens do mesmo dia são correlacionadas e o teste novo tem 3 dias).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np

MARGEM = 0.20
LADO = 224
SEMENTE = 2026
N_BOOT = 2000
QUANTIS = (5, 25, 50, 75, 95)
D10_TREINO = ("11.05.2022-14-13-13", "07.07.2022-09-39-44", "11.07.2022-09-43-17")
CAIXAS_ESPERADAS = 7003  # D12: 1.348 + 332 + 401 imagens, 7.003 caixas


def ler_rotulo_yolo(texto: str) -> list[tuple[float, float, float, float]]:
    """[(cx, cy, w, h)] normalizados; ignora linhas vazias; exige 5 campos por linha."""
    caixas = []
    for linha in texto.splitlines():
        campos = linha.split()
        if not campos:
            continue
        if len(campos) != 5:
            raise ValueError(f"linha de rótulo inválida: {linha!r}")
        _, cx, cy, w, h = campos
        caixas.append((float(cx), float(cy), float(w), float(h)))
    return caixas


def caixa_pixels(largura: int, altura: int, cx: float, cy: float, w: float, h: float, margem: float = MARGEM):
    """(x0, y0, x1, y1) inteiros da caixa com margem em cada lado, clampada à imagem, com pelo menos 1 px."""
    bw, bh = w * largura, h * altura
    x0 = int(np.floor(cx * largura - bw / 2 - margem * bw))
    x1 = int(np.ceil(cx * largura + bw / 2 + margem * bw))
    y0 = int(np.floor(cy * altura - bh / 2 - margem * bh))
    y1 = int(np.ceil(cy * altura + bh / 2 + margem * bh))
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(largura, max(x1, x0 + 1)), min(altura, max(y1, y0 + 1))
    return x0, y0, max(x1, x0 + 1), max(y1, y0 + 1)


def terços(areas: np.ndarray) -> tuple[float, float]:
    """Cortes dos terços de área (percentis 33,3 e 66,7), calculados sobre TODAS as caixas antes de olhar resultados."""
    return tuple(float(x) for x in np.percentile(areas, [100 / 3, 200 / 3]))


def faixa_tamanho(areas: np.ndarray, cortes) -> np.ndarray:
    return np.where(areas <= cortes[0], "pequena", np.where(areas <= cortes[1], "media", "grande"))


def max_cos(consultas: np.ndarray, base: np.ndarray, dia_consultas=None, dia_base=None, bloco: int = 1024):
    """Maior produto interno de cada consulta com a base (vetores já normalizados); devolve (valor, índice).
    Se dias forem dados, ignora pares do mesmo dia (controle 'outros dias')."""
    val = np.empty(len(consultas), np.float32)
    idx = np.empty(len(consultas), np.int64)
    for i in range(0, len(consultas), bloco):
        s = consultas[i:i + bloco] @ base.T
        if dia_consultas is not None:
            s = np.where(dia_consultas[i:i + bloco, None] == dia_base[None, :], -np.inf, s)
        idx[i:i + bloco] = s.argmax(1)
        val[i:i + bloco] = s.max(1)
    return val, idx


def quantis(x) -> dict:
    x = np.asarray(x, float)
    return {"n": int(len(x)), **{f"p{q}": round(float(np.percentile(x, q)), 4) for q in QUANTIS}}


def bootstrap_dif_medianas(x_novo, img_novo, x_antigo, img_antigo, n=N_BOOT, semente=SEMENTE):
    """Diferença de medianas (novo - antigo) e IC 95% percentil, reamostrando IMAGENS (com todas as caixas) em cada divisão."""
    rng = np.random.default_rng(semente)

    def agrupar(x, img):
        u, inv = np.unique(img, return_inverse=True)
        return [np.asarray(x)[inv == k] for k in range(len(u))]

    gn, ga = agrupar(x_novo, img_novo), agrupar(x_antigo, img_antigo)
    dif = []
    for _ in range(n):
        a = np.concatenate([gn[i] for i in rng.integers(0, len(gn), len(gn))])
        b = np.concatenate([ga[i] for i in rng.integers(0, len(ga), len(ga))])
        dif.append(np.median(a) - np.median(b))
    obs = float(np.median(x_novo) - np.median(x_antigo))
    lo, hi = np.percentile(dif, [2.5, 97.5])
    return {"dif_mediana": round(obs, 4), "ic95": [round(float(lo), 4), round(float(hi), 4)], "n_boot": n, "semente": semente}


def analisar_recortes(emb, nomes, dias, split_antigo, split_novo, areas, excluir=D10_TREINO) -> dict:
    """emb (n,d) normalizado; nomes/dias por caixa (nome da imagem e dia); split_* por caixa; areas em pixels."""
    emb, nomes, dias = np.asarray(emb, np.float32), np.asarray(nomes), np.asarray(dias)
    split_antigo, split_novo = np.asarray(split_antigo), np.asarray(split_novo)
    areas = np.asarray(areas, float)
    fora = np.isin(nomes, list(excluir))
    cortes = terços(areas)
    faixas = faixa_tamanho(areas, cortes)
    res = {"cortes_area_px2": [round(c, 1) for c in cortes], "caixas_total": int(len(nomes)), "divisoes": {}}
    por_caixa = {}
    for rotulo, split in (("antiga", split_antigo), ("nova", split_novo)):
        tr = (split == "train") & ~fora
        te = split == "test"
        v, j = max_cos(emb[te], emb[tr])
        ctrl, _ = max_cos(emb[tr], emb[tr], dias[tr], dias[tr])
        mesmo_dia = dias[te] == dias[tr][j]
        bloco = {"teste": quantis(v), "controle_treino_outros_dias": quantis(ctrl),
                 "fracao_vizinho_do_mesmo_dia": round(float(mesmo_dia.mean()), 4), "por_faixa": {}}
        for f in ("pequena", "media", "grande"):
            m = faixas[te] == f
            if m.any():
                bloco["por_faixa"][f] = {"teste": quantis(v[m])}
            mc = faixas[tr] == f
            if mc.any():
                bloco["por_faixa"].setdefault(f, {})["controle"] = quantis(ctrl[mc])
        res["divisoes"][rotulo] = bloco
        por_caixa[rotulo] = {"max_cos": v, "imagem": nomes[te], "vizinho": nomes[tr][j], "mesmo_dia": mesmo_dia,
                             "faixa": faixas[te]}
    res["dif_medianas_nova_menos_antiga"] = bootstrap_dif_medianas(
        por_caixa["nova"]["max_cos"], por_caixa["nova"]["imagem"], por_caixa["antiga"]["max_cos"], por_caixa["antiga"]["imagem"])
    res["_por_caixa"] = por_caixa
    return res


def _sha256(caminho) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def extrair(caminho_zip: str, pasta_rotulos: str, saida_npz: str, lote: int = 64) -> None:
    import cv2
    import torch
    from transformers import AutoModel

    from scripts.embeddings_citra import INTERNOS, MEDIA, DP, MODELO, nomes_reais, l2, _commit_modelo

    achados = [p for p in Path(pasta_rotulos).rglob("*.txt") if p.parent.name == "labels_final"]
    rotulos = {p.stem: p for p in achados}
    if len(rotulos) != len(achados):
        raise ValueError("nomes de rótulo repetidos em labels_final")
    print(len(rotulos), "arquivos de rótulo em labels_final", flush=True)
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    modelo = AutoModel.from_pretrained(MODELO).eval().to(dev)
    ext = zipfile.ZipFile(caminho_zip)
    meta, vetores, faltando = [], [], []
    for split in ("train", "val", "test"):
        with ext.open(INTERNOS[split]) as f:
            z = zipfile.ZipFile(io.BytesIO(f.read()))
        buffer, info = [], []

        def descarregar():
            with torch.no_grad():
                h = modelo(pixel_values=torch.from_numpy(np.stack(buffer)).to(dev)).last_hidden_state
            vetores.append(h[:, 0].cpu().numpy())
            meta.extend(info)
            buffer.clear()
            info.clear()

        for caminho, nome in nomes_reais(z.namelist()):
            if nome not in rotulos:
                faltando.append(nome)
                continue
            im = cv2.imdecode(np.frombuffer(z.read(caminho), np.uint8), cv2.IMREAD_COLOR)
            alt, larg = im.shape[:2]
            for k, (cx, cy, w, h) in enumerate(ler_rotulo_yolo(rotulos[nome].read_text())):
                x0, y0, x1, y1 = caixa_pixels(larg, alt, cx, cy, w, h)
                rec = cv2.cvtColor(cv2.resize(im[y0:y1, x0:x1], (LADO, LADO), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
                buffer.append(((rec.astype(np.float32) / 255.0 - MEDIA) / DP).transpose(2, 0, 1))
                info.append((split, nome, k, larg, alt, w * larg, h * alt))
                if len(buffer) == lote:
                    descarregar()
        if buffer:
            descarregar()
        print(split, "ok", flush=True)
    emb = l2(np.concatenate(vetores))
    cols = list(zip(*meta))
    np.savez(saida_npz, split=np.array(cols[0]), nome=np.array(cols[1]), caixa=np.array(cols[2]),
             largura=np.array(cols[3]), altura=np.array(cols[4]), w_px=np.array(cols[5], np.float32),
             h_px=np.array(cols[6], np.float32), cls=emb)
    prov = {"modelo": MODELO, "modelo_commit": _commit_modelo(), "margem": MARGEM, "lado_px": LADO,
            "n_caixas": int(len(meta)), "caixas_esperadas_d12": CAIXAS_ESPERADAS,
            "imagens_sem_rotulo": faltando, "npz_sha256": _sha256(saida_npz)}
    Path(saida_npz.replace(".npz", "_proveniencia.json")).write_text(json.dumps(prov, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(prov, ensure_ascii=False, indent=2))


def analise(npz: str, divisao_csv: str, pasta_saida: str) -> dict:
    d = np.load(npz, allow_pickle=False)
    with open(divisao_csv, newline="", encoding="utf-8") as f:
        div = {r["nome"]: (r["dia"], r["divisao"]) for r in csv.DictReader(f)}
    nomes = d["nome"]
    faltam = sorted({n for n in set(nomes.tolist()) if n not in div})
    if faltam:
        raise ValueError(f"{len(faltam)} imagens do .npz fora da divisão nova, ex.: {faltam[:3]}")
    dias = np.array([div[n][0] for n in nomes])
    split_novo = np.array([div[n][1] for n in nomes])
    res = analisar_recortes(d["cls"], nomes, dias, d["split"], split_novo, d["w_px"] * d["h_px"])
    por_caixa = res.pop("_por_caixa")
    saida = Path(pasta_saida)
    saida.mkdir(parents=True, exist_ok=True)
    res["npz_sha256"] = _sha256(npz)
    res["divisao_sha256"] = _sha256(divisao_csv)
    (saida / "semelhanca_recortes_resumo.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    for rotulo, c in por_caixa.items():
        with open(saida / f"semelhanca_recortes_{rotulo}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["imagem_teste", "vizinho_treino", "max_cos", "mesmo_dia", "faixa"])
            for i in range(len(c["max_cos"])):
                w.writerow([c["imagem"][i], c["vizinho"][i], round(float(c["max_cos"][i]), 4), int(c["mesmo_dia"][i]), c["faixa"][i]])
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 4 and a[0] == "extrair":
        extrair(a[1], a[2], a[3])
    elif len(a) == 4 and a[0] == "analise":
        analise(a[1], a[2], a[3])
    else:
        sys.exit(__doc__)
