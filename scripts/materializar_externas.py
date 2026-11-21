"""Materializa as imagens externas de uma lista (braço R, D15) para o treino: imagem + rótulo YOLO de classe única.

Lê os pacotes originais (ZIP), extrai só as imagens da lista, confere o `sha256_conteudo` de cada uma contra a lista
(a mesma função do manifesto; qualquer diferença interrompe), converte as caixas para YOLO normalizado com classe 0
("embarcacao"; todas as classes colapsadas, como nos manifestos) e escreve o mapa que o executor usa (`--mapa-externas`).
Caixas que ficam sem área depois de cortadas à imagem são descartadas e contadas no relatório.

Uso:
  python -m scripts.materializar_externas --lista manifests/lista_R_seed20261121.csv \\
      --pacote aboships=<ABOships.zip>:abocsv --pacote smd=<smd_clean.zip>:yolo --saida <pasta local> 
Escreve <saida>/images, <saida>/labels, <saida>/mapa_externas.csv e <saida>/relatorio_materializacao.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path

from scripts._nomes import nome_seguro
from scripts.manifesto_fonte import hashes_imagem, itens_do_pacote


def linha_yolo(x0: float, y0: float, x1: float, y1: float, W: int, H: int) -> str | None:
    x0, x1 = max(0.0, min(x0, x1)), min(float(W), max(x0, x1))
    y0, y1 = max(0.0, min(y0, y1)), min(float(H), max(y0, y1))
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        return None
    return f"0 {(x0 + x1) / 2 / W:.6f} {(y0 + y1) / 2 / H:.6f} {(x1 - x0) / W:.6f} {(y1 - y0) / H:.6f}"


def materializar(lista: Path, pacotes: dict[str, tuple[Path, str]], saida: Path) -> dict:
    with open(lista, newline="", encoding="utf-8") as f:
        itens = list(csv.DictReader(f))
    por_fonte: dict[str, list[dict]] = {}
    for r in itens:
        por_fonte.setdefault(r["fonte"], []).append(r)
    faltam = set(por_fonte) - set(pacotes)
    if faltam:
        raise ValueError(f"sem pacote para a(s) fonte(s): {sorted(faltam)}")
    (saida / "images").mkdir(parents=True, exist_ok=True)
    (saida / "labels").mkdir(parents=True, exist_ok=True)
    mapa, rel = [], {"lista": str(lista), "n_lista": len(itens), "fontes": {}}
    vistos: set[str] = set()
    for fonte, rows in por_fonte.items():
        caminho, formato = pacotes[fonte]
        pedidos = {r["caminho_relativo"]: r for r in rows}
        achados = descartadas = divergencia_n = 0
        with zipfile.ZipFile(caminho) as z:
            for n, rotulo, _split in itens_do_pacote(z, formato):
                r = pedidos.get(n)
                if r is None:
                    continue
                dados = z.read(n)
                h = hashes_imagem(dados)
                if h["sha256_conteudo"] != r["sha256_conteudo"]:
                    raise ValueError(f"conteúdo diferente do da lista: {r['id_imagem']}")
                caixas = rotulo(h["largura"], h["altura"]) or []
                linhas = [linha_yolo(*c, h["largura"], h["altura"]) for c in caixas]
                validas = [x for x in linhas if x]
                descartadas += len(linhas) - len(validas)
                divergencia_n += int(len(caixas) != int(r["n_caixas"]))
                nome = nome_seguro(r["id_imagem"])
                if nome in vistos:
                    raise ValueError(f"nome de arquivo repetido: {nome}")
                vistos.add(nome)
                img = saida / "images" / f"{nome}{Path(n).suffix.lower()}"
                img.write_bytes(dados)
                rot = saida / "labels" / f"{nome}.txt"
                rot.write_text("\n".join(validas) + ("\n" if validas else ""), encoding="utf-8")
                mapa.append({"id_imagem": r["id_imagem"], "caminho_imagem": str(img), "caminho_rotulo": str(rot)})
                achados += 1
        if achados != len(rows):
            raise ValueError(f"{fonte}: {achados} imagens achadas no pacote, {len(rows)} na lista")
        rel["fontes"][fonte] = {"n": achados, "caixas_descartadas": descartadas, "n_caixas_diferente_da_lista": divergencia_n}
    mapa.sort(key=lambda m: m["id_imagem"])
    with open(saida / "mapa_externas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id_imagem", "caminho_imagem", "caminho_rotulo"], lineterminator="\n")
        w.writeheader()
        w.writerows(mapa)
    (saida / "relatorio_materializacao.json").write_text(json.dumps(rel, indent=2), encoding="utf-8")
    return rel


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lista", required=True, type=Path)
    ap.add_argument("--pacote", action="append", required=True, help="fonte=caminho.zip:formato (yolo|voc|abocsv)")
    ap.add_argument("--saida", required=True, type=Path)
    a = ap.parse_args()
    pacotes = {}
    for p in a.pacote:
        fonte, resto = p.split("=", 1)
        caminho, formato = resto.rsplit(":", 1)
        pacotes[fonte] = (Path(caminho), formato)
    print(json.dumps(materializar(a.lista, pacotes, a.saida), indent=2), file=sys.stdout)


if __name__ == "__main__":
    main()
