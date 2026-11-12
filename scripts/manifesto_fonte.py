"""Constrói o manifesto de uma fonte pública lendo DIRETO do pacote (sem extrair).

Por imagem: hash dos pixels e do arquivo, dHash (quase-duplicata), tamanho, nº de caixas e nº de
caixas small no letterbox 640 (mesma regra do repositório das Fases 0–5: área < 32² px; COCO).
Detecta, SEM remover nada do manifesto (a decisão de excluir é do adendo):
  - duplicata por nome-base Roboflow (regra herdada: mantém o 1º em ordem alfabética);
  - duplicata exata de conteúdo dentro da fonte;
  - agrupamento de quase-duplicatas (dHash, distância de Hamming <= limiar) em clusters;
  - colisão com train/val/test do CITRA (exata ou quase), se uma tabela de hashes do CITRA for dada.

Formatos tratados (conforme docs/fontes/INVENTARIO_zips_2026-11-11.txt):
  yolo  : <split>/images/N.jpg + <split>/labels/N.txt   (SMD: smd_clean.zip; InaTechShips: dataset_25k_v2.zip)
  voc   : N.jpg + N.xml na mesma pasta                  (SeaShips: SeaShips_voc.zip)
  abocsv: Seaships/<data>/N.png + Labels/*.csv          (ABOships: ABOships.zip; colunas filename,xmin,xmax,ymin,ymax,...)

Uso (Colab, CPU):
  python -m scripts.manifesto_fonte construir --fonte smd --formato yolo \\
      --zip /content/drive/.../_zips/smd_clean.zip --saida manifests/manifesto_smd.csv
  python -m scripts.manifesto_fonte hashes-citra --raiz /content/drive/.../CITRA-3D-Real --saida /content/citra_hashes.csv
  (e passe --citra-hashes /content/citra_hashes.csv ao construir)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath

import numpy as np
from PIL import Image

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp")
LIMIAR_SMALL_PX = 32
EVAL_SIZE = 640
LIMIAR_HAMMING = 4
_ROBOFLOW = re.compile(r"^(.*)_jpg\.rf\.[a-f0-9]+\.(jpg|jpeg|png)$", re.IGNORECASE)

CAMPOS = ["id_imagem", "fonte", "caminho_relativo", "sha256_conteudo", "sha256_arquivo", "largura", "altura",
          "n_caixas", "n_small_640", "split_origem", "id_original", "parametros_json", "status_auditoria",
          "base_roboflow", "dup_base_de", "dup_conteudo_de", "cluster_quase_dup", "dhash_hex", "colide_citra",
          "erro_leitura", "tamanho_bytes"]


# ---------- hashes ----------
def dhash(img: Image.Image) -> int:
    """dHash 64 bits (9x8 em tons de cinza; compara pixels vizinhos)."""
    g = np.asarray(img.convert("L").resize((9, 8), Image.LANCZOS), dtype=np.int16)
    bits = (g[:, 1:] > g[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def hashes_imagem(dados: bytes) -> dict:
    with Image.open(io.BytesIO(dados)) as im:
        rgb = im.convert("RGB")
        return {"sha256_arquivo": hashlib.sha256(dados).hexdigest(),
                "sha256_conteudo": hashlib.sha256(rgb.tobytes() + str(rgb.size).encode()).hexdigest(),
                "largura": rgb.size[0], "altura": rgb.size[1], "dhash": dhash(rgb)}


def small_letterbox(bw: float, bh: float, W: int, H: int, eval_size: int = EVAL_SIZE) -> bool:
    s = eval_size / max(W, H)
    return (bw * s) * (bh * s) < LIMIAR_SMALL_PX ** 2


# ---------- leitores de rótulos (todas as classes colapsadas; devolvem caixas em pixels x0,y0,x1,y1) ----------
def caixas_yolo(texto: str, W: int, H: int) -> list[tuple[float, float, float, float]]:
    out = []
    for linha in texto.splitlines():
        p = linha.split()
        if len(p) < 5:
            continue
        cx, cy, w, h = (float(v) for v in p[1:5])
        out.append(((cx - w / 2) * W, (cy - h / 2) * H, (cx + w / 2) * W, (cy + h / 2) * H))
    return out


def caixas_voc(dados: bytes) -> list[tuple[float, float, float, float]]:
    out = []
    for obj in ET.fromstring(dados).findall("object"):
        b = obj.find("bndbox")
        if b is not None:
            out.append(tuple(float(b.find(k).text) for k in ("xmin", "ymin", "xmax", "ymax")))
    return out


def _stem(nome: str) -> str:
    return PurePosixPath(nome).stem


# ---------- varredura do pacote ----------
def itens_do_pacote(z: zipfile.ZipFile, formato: str):
    """Gera (caminho_imagem, funcao_rotulo(W,H)->caixas|None, split_origem)."""
    nomes = [i.filename for i in z.infolist() if not i.is_dir()]
    imgs = sorted(n for n in nomes if n.lower().endswith(IMG_EXT))
    conjunto = set(nomes)
    if formato == "yolo":
        for n in imgs:
            partes = PurePosixPath(n).parts
            if "images" not in partes:
                continue
            k = partes.index("images")
            rot = str(PurePosixPath(*partes[:k], "labels", *partes[k + 1:-1], _stem(n) + ".txt"))
            split = partes[k - 1] if k >= 1 else ""
            yield n, (lambda W, H, rot=rot: caixas_yolo(z.read(rot).decode("utf-8", "replace"), W, H)
                      if rot in conjunto else None), split
    elif formato == "voc":
        for n in imgs:
            xml = str(PurePosixPath(n).with_suffix(".xml"))
            partes = PurePosixPath(n).parts
            split = partes[-2] if len(partes) >= 3 else ""
            yield n, (lambda W, H, xml=xml: caixas_voc(z.read(xml)) if xml in conjunto else None), split
    elif formato == "abocsv":
        linhas = defaultdict(list)
        for c in (n for n in nomes if n.lower().endswith(".csv") and "label" in n.lower()):
            for r in csv.DictReader(io.StringIO(z.read(c).decode("utf-8", "replace"))):
                linhas[r["filename"]].append((float(r["xmin"]), float(r["ymin"]), float(r["xmax"]), float(r["ymax"])))
        for n in imgs:
            yield n, (lambda W, H, s=_stem(n): linhas.get(s) if s in linhas else None), PurePosixPath(n).parent.name
    else:
        raise ValueError(f"formato desconhecido: {formato}")


def agrupar_quase_duplicatas(hashes: list[int], limiar: int = LIMIAR_HAMMING) -> list[int]:
    """Union-find sobre pares com distância de Hamming <= limiar. Devolve o id de cluster por item."""
    n = len(hashes)
    pai = list(range(n))

    def achar(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i

    h = np.array(hashes, dtype=np.uint64)
    tabela = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
    for i0 in range(0, n, 512):
        bloco = h[i0:i0 + 512]
        x = (bloco[:, None] ^ h[None, :]).view(np.uint8).reshape(len(bloco), n, 8)
        dist = tabela[x].sum(axis=2)
        for a, b in zip(*np.where(dist <= limiar)):
            ia, ib = i0 + int(a), int(b)
            if ia < ib:
                pai[achar(ia)] = achar(ib)
    return [achar(i) for i in range(n)]


def sha256_arquivo_grande(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 24), b""):
            h.update(bloco)
    return h.hexdigest()


def construir(fonte: str, formato: str, caminho_zip: Path, citra: list[dict] | None = None, limite: int | None = None,
              progresso: int = 1000, hash_pacote: bool = False) -> tuple[list[dict], dict]:
    linhas: list[dict] = []
    sem_rotulo = 0
    ilegiveis: list[str] = []
    with zipfile.ZipFile(caminho_zip) as z:
        for k, (n, rotulo, split) in enumerate(itens_do_pacote(z, formato)):
            if limite and k >= limite:
                break
            if progresso and k % progresso == 0:
                print(f"  {fonte}: {k} imagens...", file=sys.stderr)
            dados = z.read(n)
            try:
                h = hashes_imagem(dados)
            except Exception as e:  # arquivo corrompido ou não-imagem: registra e segue
                ilegiveis.append(n)
                linhas.append({c: "" for c in CAMPOS} | {
                    "id_imagem": f"{fonte}:{n}", "fonte": fonte, "caminho_relativo": n,
                    "sha256_arquivo": hashlib.sha256(dados).hexdigest(), "n_caixas": 0, "n_small_640": 0,
                    "split_origem": split, "status_auditoria": "ilegivel", "cluster_quase_dup": -1,
                    "erro_leitura": f"{type(e).__name__}: {e}"[:200], "tamanho_bytes": len(dados)})
                continue
            caixas = rotulo(h["largura"], h["altura"])
            if caixas is None:
                sem_rotulo += 1
                caixas = []
            m = _ROBOFLOW.match(PurePosixPath(n).name)
            linhas.append({
                "id_imagem": f"{fonte}:{n}", "fonte": fonte, "caminho_relativo": n,
                "sha256_conteudo": h["sha256_conteudo"], "sha256_arquivo": h["sha256_arquivo"],
                "largura": h["largura"], "altura": h["altura"], "n_caixas": len(caixas),
                "n_small_640": sum(small_letterbox(x1 - x0, y1 - y0, h["largura"], h["altura"]) for x0, y0, x1, y1 in caixas),
                "split_origem": split, "id_original": "", "parametros_json": "",
                "status_auditoria": "nao_auditada", "erro_leitura": "", "tamanho_bytes": len(dados),
                "base_roboflow": m.group(1) if m else "", "dup_base_de": "", "dup_conteudo_de": "",
                "cluster_quase_dup": -1, "dhash_hex": f"{h['dhash']:016x}", "colide_citra": "",
            })
    # duplicatas
    primeiro_base, primeiro_cont = {}, {}
    ok = [r for r in linhas if not r["erro_leitura"]]
    for r in sorted(ok, key=lambda r: r["caminho_relativo"]):
        if r["base_roboflow"]:
            r["dup_base_de"] = primeiro_base.setdefault(r["base_roboflow"], r["id_imagem"])
            if r["dup_base_de"] == r["id_imagem"]:
                r["dup_base_de"] = ""
        r["dup_conteudo_de"] = primeiro_cont.setdefault(r["sha256_conteudo"], r["id_imagem"])
        if r["dup_conteudo_de"] == r["id_imagem"]:
            r["dup_conteudo_de"] = ""
    if ok:
        cl = agrupar_quase_duplicatas([int(r["dhash_hex"], 16) for r in ok])
        for r, c in zip(ok, cl):
            r["cluster_quase_dup"] = c
    if citra:
        por_hash = {c["sha256_conteudo"]: c["split"] for c in citra}
        ch = np.array([int(c["dhash_hex"], 16) for c in citra], dtype=np.uint64)
        tabela = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
        for r in ok:
            if r["sha256_conteudo"] in por_hash:
                r["colide_citra"] = f"exata:{por_hash[r['sha256_conteudo']]}"
                continue
            d = tabela[(ch ^ np.uint64(int(r["dhash_hex"], 16))).view(np.uint8).reshape(-1, 8)].sum(axis=1)
            j = int(np.argmin(d))
            if d[j] <= LIMIAR_HAMMING:
                r["colide_citra"] = f"quase:{citra[j]['split']}"
    unicas_base = [r for r in ok if not r["dup_base_de"]]
    rel = {
        "fonte": fonte, "formato": formato, "pacote": Path(caminho_zip).name,
        "sha256_pacote": sha256_arquivo_grande(Path(caminho_zip)) if hash_pacote else "nao_calculado(use --hash-pacote ou sha256sum)",
        "n_imagens": len(linhas), "n_legiveis": len(ok), "n_sem_rotulo": sem_rotulo,
        "n_dup_base_roboflow": sum(bool(r["dup_base_de"]) for r in linhas),
        "n_dup_conteudo_exato": sum(bool(r["dup_conteudo_de"]) for r in linhas),
        "n_clusters_quase_dup": len({r["cluster_quase_dup"] for r in ok}),
        "n_ilegiveis": len(ilegiveis), "ilegiveis_primeiros": ilegiveis[:20],
        "n_unicas_pela_regra_herdada": len(unicas_base),
        "n_caixas": sum(r["n_caixas"] for r in linhas), "n_small_640": sum(r["n_small_640"] for r in linhas),
        "n_colide_citra_exata": sum(r["colide_citra"].startswith("exata") for r in linhas),
        "n_colide_citra_quase": sum(r["colide_citra"].startswith("quase") for r in linhas),
        "limiar_hamming": LIMIAR_HAMMING,
    }
    return linhas, rel


def hashes_citra(raiz: Path) -> list[dict]:
    saida = []
    for p in sorted(Path(raiz).rglob("*")):
        if p.suffix.lower() in IMG_EXT:
            if "report" in p.stem.lower():   # figuras de relatório, não imagens do dataset
                continue
            if any(q in p.parts for q in ("_quarantine", "quarantine")):
                split = "quarentena"
            else:
                split = next((s for s in ("train", "valid", "val", "test") if s in p.parts), "desconhecido")
            h = hashes_imagem(p.read_bytes())
            saida.append({"split": "val" if split == "valid" else split, "caminho": str(p),
                          "sha256_conteudo": h["sha256_conteudo"], "dhash_hex": f"{h['dhash']:016x}"})
    return saida


def vizinho_citra(dhash_hex: str, citra: list[dict]) -> tuple[int, dict]:
    ch = np.array([int(c["dhash_hex"], 16) for c in citra], dtype=np.uint64)
    tabela = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
    d = tabela[(ch ^ np.uint64(int(dhash_hex, 16))).view(np.uint8).reshape(-1, 8)].sum(axis=1)
    j = int(np.argmin(d))
    return int(d[j]), citra[j]


def montar_colisoes(manifesto: Path, caminho_zip: Path, citra: list[dict], saida: Path, altura: int = 240) -> list[dict]:
    """Para cada linha marcada como colisão, grava um par lado a lado (fonte | CITRA) e devolve a tabela."""
    from PIL import ImageDraw
    saida = Path(saida); saida.mkdir(parents=True, exist_ok=True)
    marcadas = [r for r in csv.DictReader(open(manifesto, encoding="utf-8")) if r["colide_citra"]]
    tabela = []
    with zipfile.ZipFile(caminho_zip) as z:
        for k, r in enumerate(marcadas):
            d, c = vizinho_citra(r["dhash_hex"], citra)
            a = Image.open(io.BytesIO(z.read(r["caminho_relativo"]))).convert("RGB")
            b = Image.open(c["caminho"]).convert("RGB")
            a = a.resize((int(a.width * altura / a.height), altura)); b = b.resize((int(b.width * altura / b.height), altura))
            tela = Image.new("RGB", (a.width + b.width + 10, altura + 18), "white")
            tela.paste(a, (0, 18)); tela.paste(b, (a.width + 10, 18))
            ImageDraw.Draw(tela).text((2, 2), f"{r['caminho_relativo'][-40:]} | CITRA {c['split']} d={d}", fill="black")
            nome = f"col_{k:03d}.png"; tela.save(saida / nome)
            tabela.append({"arquivo": nome, "fonte_caminho": r["caminho_relativo"], "citra": c["caminho"],
                           "citra_split": c["split"], "dist_hamming": d, "marca": r["colide_citra"]})
    with open(saida / "colisoes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["arquivo", "fonte_caminho", "citra", "citra_split", "dist_hamming", "marca"])
        w.writeheader(); w.writerows(tabela)
    return tabela


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("construir")
    c.add_argument("--fonte", required=True)
    c.add_argument("--formato", required=True, choices=["yolo", "voc", "abocsv"])
    c.add_argument("--zip", required=True, type=Path)
    c.add_argument("--saida", required=True, type=Path)
    c.add_argument("--citra-hashes", type=Path)
    c.add_argument("--limite", type=int)
    c.add_argument("--hash-pacote", action="store_true", help="calcula o SHA-256 do pacote (lento em pacotes grandes)")
    k = sub.add_parser("colisoes", help="grava pares lado a lado das imagens marcadas como colisão com o CITRA")
    k.add_argument("--manifesto", required=True, type=Path)
    k.add_argument("--zip", required=True, type=Path)
    k.add_argument("--citra-hashes", required=True, type=Path)
    k.add_argument("--saida", required=True, type=Path)
    h = sub.add_parser("hashes-citra")
    h.add_argument("--raiz", required=True, type=Path)
    h.add_argument("--saida", required=True, type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "hashes-citra":
        linhas = hashes_citra(a.raiz)
        with open(a.saida, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["split", "caminho", "sha256_conteudo", "dhash_hex"])
            w.writeheader(); w.writerows(linhas)
        contagem = defaultdict(int)
        for r in linhas: contagem[r["split"]] += 1
        print(f"{len(linhas)} imagens do CITRA por split: {dict(contagem)}")
        if contagem.get("desconhecido"):
            print("ATENÇÃO: imagens sem split reconhecível no caminho; confira a estrutura antes de usar.")
        return
    citra = list(csv.DictReader(open(a.citra_hashes, encoding="utf-8"))) if a.citra_hashes else None
    if a.cmd == "colisoes":
        t = montar_colisoes(a.manifesto, a.zip, citra, a.saida)
        print(f"{len(t)} pares em {a.saida}; distâncias: {sorted(x['dist_hamming'] for x in t)}")
        return
    linhas, rel = construir(a.fonte, a.formato, a.zip, citra, a.limite, hash_pacote=a.hash_pacote)
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    with open(a.saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader(); w.writerows(linhas)
    a.saida.with_suffix(".relatorio.json").write_text(json.dumps(rel, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(rel, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
