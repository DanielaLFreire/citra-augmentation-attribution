"""Extrai de zips (sem descompactar) os poucos arquivos pequenos que faltam para fechar A09, A11 e A12.

Lê só o que precisa de dentro dos pacotes; não escreve nada nos zips. Saída: uma pasta com
cópias dos arquivos pequenos e um `resumo_pendencias.json`, mais um .zip dessa pasta para anexar.

Uso (Colab):
  python -m scripts.coletar_pendencias --zips /content/drive/MyDrive/PROJETO_MARINHA/Datasets/_zips \\
      --saida /content/drive/MyDrive/PROJETO_MARINHA/EXPERIMENTO_ATRIBUICAO_CAUSAL/pendencias
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath

LIMITE_COPIA = 5 * 1024 * 1024  # arquivos maiores que isso só são resumidos, não copiados


def _achar(z: zipfile.ZipFile, sufixo: str) -> str | None:
    for n in z.namelist():
        if n.replace("\\", "/").endswith(sufixo):
            return n
    return None


def _copiar(z: zipfile.ZipFile, nome: str, pasta: Path) -> dict:
    info = z.getinfo(nome)
    destino = pasta / PurePosixPath(nome).name
    if info.file_size <= LIMITE_COPIA:
        destino.write_bytes(z.read(nome))
    return {"arquivo": nome, "bytes": info.file_size, "copiado": info.file_size <= LIMITE_COPIA}


def resumo_csv(dados: bytes, coluna_nome: tuple[str, ...] = ("filename", "image", "image_id", "file", "name")) -> dict:
    texto = dados.decode("utf-8", "replace")
    linhas = texto.splitlines()
    leitor = csv.DictReader(io.StringIO(texto))
    colunas = leitor.fieldnames or []
    registros = list(leitor)
    r = {"colunas": colunas, "n_linhas_dados": len(registros), "primeiras_linhas": linhas[:8]}
    col = next((c for c in colunas if c.lower() in coluna_nome), None)
    if col:
        nomes = [x[col] for x in registros]
        stems = {PurePosixPath(n).stem for n in nomes}
        r["coluna_nome"] = col
        r["n_nomes_distintos"] = len(set(nomes))
        r["n_stems_distintos"] = len(stems)
    return r


def coletar(pasta_zips: Path, saida: Path) -> dict:
    saida.mkdir(parents=True, exist_ok=True)
    res: dict = {}

    def abrir(nome):
        p = pasta_zips / nome
        return zipfile.ZipFile(p) if p.is_file() else None

    # A09: seaship.zip
    z = abrir("seaship.zip")
    if z:
        with z:
            nomes = z.namelist()
            r = {"n_train_images": sum(1 for n in nomes if "/train_images/" in n),
                 "n_test_images": sum(1 for n in nomes if "/test_images/" in n)}
            for alvo in ("train.csv", "test.csv"):
                n = _achar(z, "SeaShip/" + alvo)
                if n:
                    r[alvo] = resumo_csv(z.read(n))
            res["seaship.zip"] = r
    else:
        res["seaship.zip"] = "NAO ENCONTRADO"

    # A11: genship3d-mirror.zip
    z = abrir("genship3d-mirror.zip")
    if z:
        with z:
            r = {"arquivos": []}
            for alvo in ("audit_report.json", "confirmation_report.csv", "detection_report.csv"):
                n = _achar(z, alvo)
                r["arquivos"].append(_copiar(z, n, saida) if n else {"arquivo": alvo, "erro": "nao encontrado"})
            r["n_por_pasta"] = {}
            for n in z.namelist():
                p = PurePosixPath(n).parts
                if len(p) >= 2 and not n.endswith("/"):
                    r["n_por_pasta"][p[1]] = r["n_por_pasta"].get(p[1], 0) + 1
            res["genship3d-mirror.zip"] = r
    else:
        res["genship3d-mirror.zip"] = "NAO ENCONTRADO"

    # A12: dataset_25k_v2.zip (so um arquivo; o zip tem 10 GB mas so o indice e lido)
    z = abrir("dataset_25k_v2.zip")
    if z:
        with z:
            n = _achar(z, "reconstrucao_report.json")
            res["dataset_25k_v2.zip"] = _copiar(z, n, saida) if n else "reconstrucao_report.json nao encontrado"
    else:
        res["dataset_25k_v2.zip"] = "NAO ENCONTRADO"

    # ABOships.zip: nomes distintos no CSV x imagens
    z = abrir("ABOships.zip")
    if z:
        with z:
            n = _achar(z, "Labels/Vesibussi_Labels.csv")
            pngs = {PurePosixPath(x).stem for x in z.namelist() if x.lower().endswith(".png")}
            r = {"n_imagens_png": len(pngs)}
            if n:
                r["labels"] = resumo_csv(z.read(n))
                texto = z.read(n).decode("utf-8", "replace")
                col = r["labels"].get("coluna_nome")
                if col:
                    com_caixa = {PurePosixPath(x[col]).stem for x in csv.DictReader(io.StringIO(texto))}
                    r["n_imagens_sem_linha_no_csv"] = len(pngs - com_caixa)
                    r["n_stems_do_csv_sem_imagem"] = len(com_caixa - pngs)
            p = _achar(z, "parse_seaships.py")
            if p:
                r["parse_seaships.py"] = _copiar(z, p, saida)
            res["ABOships.zip"] = r
    else:
        res["ABOships.zip"] = "NAO ENCONTRADO"

    (saida / "resumo_pendencias.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    shutil.make_archive(str(saida), "zip", saida)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zips", required=True, type=Path)
    ap.add_argument("--saida", required=True, type=Path)
    a = ap.parse_args()
    r = coletar(a.zips, a.saida)
    print(json.dumps(r, indent=2, ensure_ascii=False)[:6000])
    print(f"\nPronto. Anexe: {a.saida}.zip")
