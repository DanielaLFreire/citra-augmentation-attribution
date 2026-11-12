# Perfil estrutural (letterbox 640) do Genship 3D e do iflens + inspeção do iflens.rar
# CPU apenas. Extrai para /content (nunca para o Drive). Saída: texto + um JSON.
import collections, json, os, subprocess, sys
from pathlib import Path

DRIVE = "/content/drive/MyDrive/PROJETO_MARINHA"
ZIPS = f"{DRIVE}/Datasets/_zips"
CITRA = f"{DRIVE}/Datasets/CITRA-3D-Real"
REPO = "/content/synth-detection-attribution"
TAG = "v1.1-fase5-fechada"
DEST = {"genship": "/content/inv_genship", "iflens": "/content/inv_iflens"}
ARQ = {"genship": f"{ZIPS}/Genship_3D.zip", "iflens": f"{ZIPS}/iflens.rar"}
SAIDA_JSON = "/content/perfil_sinteticos.json"
IMG_EXT = (".png", ".jpg", ".jpeg")


def preparar():
    if not os.path.isdir(REPO):
        subprocess.run(f"git clone -q --depth 1 --branch {TAG} "
                       f"https://github.com/DanielaLFreire/synth-detection-attribution {REPO}",
                       shell=True, check=True)
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    for nome, dst in DEST.items():
        if os.path.isdir(dst) and os.listdir(dst):
            continue
        os.makedirs(dst, exist_ok=True)
        subprocess.run("apt-get -qq install -y p7zip-full unrar > /dev/null", shell=True)
        arq = ARQ[nome]
        cmd = (f'unrar x -o+ -inul "{arq}" "{dst}/"' if arq.endswith(".rar")
               else f'7z x -y -o"{dst}" "{arq}" > /dev/null')
        subprocess.run(cmd, shell=True, check=True)


def resumo(p):
    d = p["coco_size_distribution"]
    return (f"{p['n_imagens']:6d} img  {p['n_bboxes_total']:7d} caixas  "
            f"small={d['small_pct']:5.1f}%  medium={d['medium_pct']:5.1f}%  large={d['large_pct']:5.1f}%")


def perfilar_pastas(pares, perfilar_dataset):
    """pares: lista de (rotulo, imagens_dir, labels_dir). Devolve {rotulo: perfil}."""
    out = {}
    for rotulo, imgs, labs in pares:
        if not (os.path.isdir(imgs) and os.path.isdir(labs)):
            print(f"  [ausente] {rotulo}")
            continue
        p = perfilar_dataset(Path(imgs), Path(labs))
        if p["n_bboxes_total"] == 0:
            print(f"  [sem caixas] {rotulo}")
            continue
        out[rotulo] = p
        print(f"  {rotulo:38s} {resumo(p)}")
    return out


def total(perfis):
    n_img = sum(p["n_imagens"] for p in perfis.values())
    n_box = sum(p["n_bboxes_total"] for p in perfis.values())
    cont = collections.Counter()
    for p in perfis.values():
        d = p["coco_size_distribution"]
        for k in ("small", "medium", "large"):
            cont[k] += round(d[f"{k}_pct"] * p["n_bboxes_total"] / 100)
    if n_box:
        print(f"  {'TOTAL':38s} {n_img:6d} img  {n_box:7d} caixas  "
              + "  ".join(f"{k}={100*cont[k]/n_box:5.1f}%" for k in ("small", "medium", "large")))
    return {"n_imagens": n_img, "n_bboxes": n_box, "contagem": dict(cont)}


def inspecionar_iflens(raiz, citra):
    print("\n===== Inspeção do iflens.rar =====")
    topo = sorted(os.listdir(raiz))
    print("Topo:", topo)
    por_pasta, aug, pngs, saidas, scripts = collections.Counter(), [], [], [], []
    for r, ds, fs in os.walk(raiz):
        rel = os.path.relpath(r, raiz)
        for d in ds:
            if d.lower() in ("output", "outputs", "saida"):
                saidas.append(os.path.join(rel, d))
        for f in fs:
            ext = os.path.splitext(f)[1].lower()
            chave = "/".join(rel.split(os.sep)[:2])
            if ext in IMG_EXT:
                por_pasta[(chave, ext)] += 1
            if ext == ".png":
                pngs.append(os.path.join(rel, f))
            if f.upper().startswith("AUG_"):
                aug.append(os.path.join(rel, f))
            if ext == ".py":
                scripts.append(os.path.join(rel, f))
    print("Imagens por pasta (2 níveis) e extensão:")
    for (k, e), v in sorted(por_pasta.items()):
        print(f"  {v:7d}  {e:5s}  {k}")
    print(f"Arquivos com prefixo AUG_: {len(aug)}", aug[:5])
    print(f"Pastas de saída encontradas: {saidas}")
    print(f"PNG: {len(pngs)}; exemplos: {pngs[:8]}")
    print(f"Scripts .py: {scripts}")

    from PIL import Image
    res = collections.Counter()
    for p in pngs[:200]:
        with Image.open(os.path.join(raiz, p)) as im:
            res[im.size] += 1
    print("Resoluções dos PNG (até 200):", res.most_common(6))

    # nomes do iflens que coincidem com imagens do CITRA, por split
    coincid = {}
    stems = collections.defaultdict(list)
    for r, _, fs in os.walk(raiz):
        for f in fs:
            if f.lower().endswith(IMG_EXT):
                s = os.path.splitext(f)[0]
                stems[s[4:] if s.upper().startswith("AUG_") else s].append(os.path.relpath(r, raiz))
    for split in ("train", "val", "test"):
        d = os.path.join(citra, split, "images")
        if not os.path.isdir(d):
            print(f"  [CITRA ausente] {d}")
            continue
        alvo = {os.path.splitext(f)[0] for f in os.listdir(d)}
        comuns = sorted(alvo & set(stems))
        coincid[split] = len(comuns)
        print(f"Nomes em comum com CITRA/{split}: {len(comuns)} de {len(alvo)}",
              [(c, stems[c][0]) for c in comuns[:3]])
    return {"topo": topo, "n_png": len(pngs), "n_aug": len(aug), "pastas_saida": saidas,
            "coincidencias_citra": coincid,
            "por_pasta": {f"{k}|{e}": v for (k, e), v in por_pasta.items()}}


def main():
    preparar()
    from src.profiling import perfilar_dataset
    resultado = {}

    print("===== Genship 3D (por classe/condição) =====")
    g = DEST["genship"]
    pares = []
    for r, ds, fs in sorted(os.walk(g)):
        if any(f.lower().endswith(".txt") for f in fs) and any(f.lower().endswith(IMG_EXT) for f in fs):
            pares.append((os.path.relpath(r, g), r, r))
    pg = perfilar_pastas(pares, perfilar_dataset)
    resultado["genship"] = {"por_pasta": pg, "total": total(pg)}

    print("\n===== iflens: dataset/consolidado (por split) =====")
    c = os.path.join(DEST["iflens"], "dataset", "consolidado")
    pares = [(s, os.path.join(c, s, "images"), os.path.join(c, s, "labels")) for s in ("train", "valid", "test")]
    pi = perfilar_pastas(pares, perfilar_dataset)
    resultado["iflens_consolidado"] = {"por_split": pi, "total": total(pi)}

    print("\n===== iflens: input/ (originais sorteadas, por execução) =====")
    inp = os.path.join(DEST["iflens"], "input")
    pares = [(d, os.path.join(inp, d), os.path.join(inp, d)) for d in sorted(os.listdir(inp))] if os.path.isdir(inp) else []
    pin = perfilar_pastas(pares, perfilar_dataset)
    resultado["iflens_input"] = {"total": total(pin), "n_execucoes": len(pin)}

    resultado["iflens_inspecao"] = inspecionar_iflens(DEST["iflens"], CITRA)

    with open(SAIDA_JSON, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=1, default=str)
    print(f"\nJSON salvo em {SAIDA_JSON}")
    print("Referência do alvo: CITRA-3D-Real = 82,2% small (letterbox 640).")


main()
