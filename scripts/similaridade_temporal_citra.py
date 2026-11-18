"""Semelhança visual entre quadros de teste/validação e quadros de treino do CITRA: mesmo dia contra outros dias.

Para cada imagem real de val/test, calcula (miniatura 64x36 em cinza, normalizada, cosseno) o máximo de semelhança
com o treino do MESMO dia e o compara com o máximo de k quadros de treino sorteados de OUTROS dias (k = nº de
quadros de treino daquele dia; 200 sorteios, semente 2026). A comparação com k igual é necessária: o máximo de um
conjunto maior é maior por acaso (a primeira versão, sem esse controle, estava viesada contra o mesmo dia).
Rodado no Colab sobre CITRA-3D.zip (zips internos train/val/test); exclui as 2 imagens da quarentena.
Resultado e leitura em docs/fontes/FICHA_publicas.md. Medida exploratória e grosseira.
"""
import csv
import datetime
import io
import re
import sys
import zipfile

import cv2
import numpy as np

REAL = re.compile(r"^\d{2}\.\d{2}\.\d{4}-\d{2}-\d{2}-\d{2}\.png$")
QUARENTENA = {"29.04.2022-14-59-27", "14.04.2022-13-48-55"}
INTERNOS = {
    "train": "CITRA-3D/train-20260103T082001Z-1-001.zip",
    "val": "CITRA-3D/val-20260103T104420Z-1-001.zip",
    "test": "CITRA-3D/test-20260103T110900Z-1-001.zip",
}


def carregar(ext, interno):
    with ext.open(interno) as f:
        z = zipfile.ZipFile(io.BytesIO(f.read()))
    nomes, vetores = [], []
    for n in z.namelist():
        b = n.split("/")[-1]
        if REAL.match(b) and b[:-4] not in QUARENTENA:
            im = cv2.imdecode(np.frombuffer(z.read(n), np.uint8), cv2.IMREAD_REDUCED_GRAYSCALE_4)
            v = cv2.resize(im, (64, 36), interpolation=cv2.INTER_AREA).astype(np.float32).ravel()
            vetores.append((v - v.mean()) / (v.std() + 1e-6))
            nomes.append(b[:-4])
    return nomes, np.array(vetores)


def principal(caminho_zip, saida_csv):
    ext = zipfile.ZipFile(caminho_zip)
    tr_n, tr_v = carregar(ext, INTERNOS["train"])
    tr_dia = np.array([n[:10] for n in tr_n])
    rng = np.random.default_rng(2026)
    linhas = []
    for split in ("test", "val"):
        n_, v_ = carregar(ext, INTERNOS[split])
        sim = (v_ @ tr_v.T) / v_.shape[1]
        for i, n in enumerate(n_):
            m = tr_dia == n[:10]
            k = int(m.sum())
            outros = np.where(~m)[0]
            mesmo = sim[i, m].max()
            sorteios = np.array([sim[i, rng.choice(outros, k, replace=False)].max() for _ in range(200)])
            linhas.append((split, n, k, mesmo, float(np.median(sorteios)), float((mesmo > sorteios).mean())))
    with open(saida_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["split", "nome", "k_treino_mesmo_dia", "sim_mesmo_dia", "mediana_sim_sorteio_outros_dias", "frac_sorteios_vencidos"])
        w.writerows(linhas)


if __name__ == "__main__":
    principal(sys.argv[1], sys.argv[2])
