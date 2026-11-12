"""Inspeciona citra-mirror.zip sem extrair e compara com a raiz do CITRA usada no experimento.

Responde: o que há no espelho (pastas, versões de rótulos, links simbólicos), qual o tamanho do quadro
`11.05.2022-14-13-13` ali, quais relatórios de auditoria existem, e em que o espelho difere da raiz.
Comparação por chave (split/pasta/nome) = últimos 3 componentes do caminho; rótulos por SHA-256,
imagens por tamanho (e por SHA-256 só quando o tamanho coincide e o item do zip não é link).

Uso (Colab):
  python -m scripts.inspecionar_citra_mirror --zip <_zips>/citra-mirror.zip \\
      --raiz /content/drive/MyDrive/PROJETO_MARINHA/Datasets/CITRA-3D-Real --saida <pasta>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

IMG = (".png", ".jpg", ".jpeg", ".bmp")
ALVO = "11.05.2022-14-13-13"
LIMITE_COPIA = 5 * 1024 * 1024


def _link(info: zipfile.ZipInfo) -> bool:
    return stat.S_ISLNK(info.external_attr >> 16)


def _chave(nome: str) -> str:
    return "/".join(PurePosixPath(nome).parts[-3:])


def inspecionar(caminho_zip: Path, raiz: Path | None, saida: Path) -> dict:
    saida.mkdir(parents=True, exist_ok=True)
    res: dict = {}
    with zipfile.ZipFile(caminho_zip) as z:
        itens = [i for i in z.infolist() if not i.is_dir()]
        res["n_itens"] = len(itens)
        res["extensoes"] = dict(Counter(PurePosixPath(i.filename).suffix.lower() for i in itens))
        res["pastas_2_niveis"] = dict(Counter("/".join(PurePosixPath(i.filename).parts[:2]) for i in itens).most_common(40))
        res["n_links_simbolicos"] = sum(1 for i in itens if _link(i))
        res["exemplo_links"] = [{"nome": i.filename, "alvo": z.read(i).decode("utf-8", "replace")}
                                for i in itens if _link(i)][:3]
        res["pastas_de_rotulo"] = dict(Counter(PurePosixPath(i.filename).parts[-2] for i in itens
                                               if i.filename.endswith(".txt") and "label" in i.filename.lower()))
        res["alvo"] = []
        for i in itens:
            if ALVO in i.filename:
                dado = z.read(i)
                res["alvo"].append({"nome": i.filename, "bytes": i.file_size, "link": _link(i),
                                    "sha256": hashlib.sha256(dado).hexdigest(),
                                    "conteudo_se_pequeno": dado.decode("utf-8", "replace") if i.file_size < 400 else None})
        res["relatorios"] = []
        for i in itens:
            n = PurePosixPath(i.filename).name.lower()
            if n.endswith((".json", ".csv", ".md", ".py")) and "label" not in i.filename.lower().split("/")[-2]:
                if i.file_size <= LIMITE_COPIA:
                    (saida / PurePosixPath(i.filename).name).write_bytes(z.read(i))
                res["relatorios"].append({"nome": i.filename, "bytes": i.file_size})
        res["quarentena"] = [i.filename for i in itens if "quarantine" in i.filename.lower()][:40]

        if raiz is not None:
            raiz = Path(raiz)
            local = {_chave(p.as_posix()): p for p in raiz.rglob("*") if p.is_file()}
            dif = Counter()
            exemplos: dict[str, list] = {}
            for i in itens:
                k = _chave(i.filename)
                if not (i.filename.endswith(".txt") and "label" in i.filename.lower()) and not i.filename.lower().endswith(IMG):
                    continue
                tipo = "rotulo" if i.filename.endswith(".txt") else "imagem"
                p = local.get(k)
                if p is None:
                    cat = "so_no_espelho"
                elif tipo == "rotulo":
                    cat = "igual" if hashlib.sha256(p.read_bytes()).hexdigest() == hashlib.sha256(z.read(i)).hexdigest() else "difere"
                elif _link(i):
                    cat = "link_no_zip"
                elif p.stat().st_size != i.file_size:
                    cat = "difere_tamanho"
                else:
                    cat = "igual" if hashlib.sha256(p.read_bytes()).hexdigest() == hashlib.sha256(z.read(i)).hexdigest() else "difere"
                dif[f"{tipo}:{cat}"] += 1
                if cat not in ("igual", "link_no_zip") and len(exemplos.setdefault(f"{tipo}:{cat}", [])) < 10:
                    exemplos[f"{tipo}:{cat}"].append(k)
            chaves_zip = {_chave(i.filename) for i in itens}
            res["comparacao_com_raiz"] = dict(dif)
            res["exemplos"] = exemplos
            res["so_na_raiz_rotulos"] = sum(1 for k in local if k.endswith(".txt") and "label" in k.lower() and k not in chaves_zip)
            res["so_na_raiz_imagens"] = sum(1 for k in local if k.lower().endswith(IMG) and "report" not in k.lower() and k not in chaves_zip)
    (saida / "resumo_citra_mirror.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.make_archive(str(saida), "zip", saida)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", required=True, type=Path)
    ap.add_argument("--raiz", type=Path)
    ap.add_argument("--saida", required=True, type=Path)
    a = ap.parse_args()
    r = inspecionar(a.zip, a.raiz, a.saida)
    print(json.dumps(r, indent=2, ensure_ascii=False)[:7000])
    print(f"\nPronto. Anexe: {a.saida}.zip")
