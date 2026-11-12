# Inventário dos pacotes em _zips (Colab, CPU). NÃO extrai nada; só lê os índices.
# Saída: texto na tela + /content/inventario_zips.json
import collections, json, os, subprocess, tarfile, zipfile

ZIPS = "/content/drive/MyDrive/PROJETO_MARINHA/Datasets/_zips"
SAIDA = "/content/inventario_zips.json"
IMG = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")


def listar(caminho):
    """Retorna lista de nomes internos do arquivo compactado."""
    low = caminho.lower()
    if low.endswith(".zip"):
        with zipfile.ZipFile(caminho) as z:
            return [i.filename for i in z.infolist() if not i.is_dir()]
    if low.endswith((".tar", ".tar.gz", ".tgz")):
        with tarfile.open(caminho) as t:
            return [m.name for m in t.getmembers() if m.isfile()]
    if low.endswith(".rar"):
        saida = subprocess.run(["unrar", "lb", caminho], capture_output=True, text=True).stdout
        return [l for l in saida.splitlines() if l and not l.endswith("/")]
    return None


def resumir(nomes):
    ext = collections.Counter(os.path.splitext(n)[1].lower() for n in nomes)
    n_img = sum(c for e, c in ext.items() if e in IMG)
    topo = collections.Counter("/".join(n.replace("\\", "/").split("/")[:2]) for n in nomes)
    return {"n_arquivos": len(nomes), "n_imagens": n_img, "extensoes": dict(ext.most_common(8)),
            "pastas_2_niveis": dict(topo.most_common(25)), "exemplos": nomes[:5]}


def main():
    res = {}
    for nome in sorted(os.listdir(ZIPS)):
        p = os.path.join(ZIPS, nome)
        if not os.path.isfile(p):
            continue
        info = {"tamanho_gb": round(os.path.getsize(p) / 1e9, 3)}
        try:
            nomes = listar(p)
            info.update(resumir(nomes) if nomes is not None else {"erro": "formato não tratado"})
        except Exception as e:  # pacote corrompido ou unrar ausente
            info["erro"] = repr(e)
        res[nome] = info
        print(f"\n== {nome}  ({info['tamanho_gb']} GB)")
        for k, v in info.items():
            if k != "tamanho_gb":
                print(f"  {k}: {v}")
    json.dump(res, open(SAIDA, "w"), indent=1, ensure_ascii=False)
    print("\nSalvo em", SAIDA)


if __name__ == "__main__":
    main()
