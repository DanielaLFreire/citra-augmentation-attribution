"""Divisão do CITRA real em blocos de dias (D23): sorteio de dias para teste, validação e treino.

Procedimento (fixado antes de qualquer sorteio definitivo):
1. Unidade = dia (dd.mm.aaaa do nome). Usa as imagens reais rotuladas: nomes reais do inventário menos as 2 da quarentena.
2. Alvos de imagens: teste 401, validação 332, treino 1348 (tamanhos da divisão antiga); cada divisão deve ficar dentro de ±10% do alvo.
3. Sorteio: embaralha os dias com numpy default_rng(semente). Testa: toma o prefixo cuja soma de imagens é a mais
   próxima de 401. Validação: do restante, o prefixo mais próximo de 332. Treino: o que sobra.
   Aceita se as três divisões estão dentro de ±10%; senão descarta e tira o próximo embaralhamento do MESMO gerador.
   Vale o primeiro sorteio aceito. Nenhum ajuste, troca de dias ou novo sorteio por outro motivo.
4. Os 3 quadros da D10 ficam na divisão em que caírem (a quarentena vale só se caírem no treino).
Saída: CSV nome,dia,divisao + resumo (dias e imagens por divisão, tentativas até aceitar).
Uso: python -m scripts.dividir_citra_dias <nomes_zip_citra3d.csv> <semente> <saida.csv>
"""
import csv
import json
import re
import sys
from collections import Counter

import numpy as np

REAL = re.compile(r"^\d{2}\.\d{2}\.\d{4}-\d{2}-\d{2}-\d{2}\.png$")
QUARENTENA = {"29.04.2022-14-59-27", "14.04.2022-13-48-55"}
ALVOS = {"test": 401, "val": 332, "train": 1348}
TOLERANCIA = 0.10


def contagens_por_dia(caminho_csv):
    nomes = []
    for r in csv.DictReader(open(caminho_csv, encoding="utf-8")):
        if r["tipo"] == "real" and REAL.match(r["nome"]) and r["nome"][:-4] not in QUARENTENA:
            nomes.append(r["nome"][:-4])
    c = Counter(n[:10] for n in nomes)
    return nomes, dict(sorted(c.items(), key=lambda kv: (kv[0][6:], kv[0][3:5], kv[0][:2])))


def _prefixo_mais_proximo(dias, cont, alvo):
    soma, melhor, k_melhor = 0, None, 0
    for k, d in enumerate(dias, start=1):
        soma += cont[d]
        if melhor is None or abs(soma - alvo) < abs(melhor - alvo):
            melhor, k_melhor = soma, k
    return k_melhor, melhor


def dentro(n, alvo):
    return abs(n - alvo) <= TOLERANCIA * alvo


def sortear(cont, semente, max_tentativas=100000):
    """Devolve (dias por divisão, nº de tentativas). Determinístico dada a semente."""
    rng = np.random.default_rng(semente)
    dias = sorted(cont)
    for t in range(1, max_tentativas + 1):
        ordem = [dias[i] for i in rng.permutation(len(dias))]
        k, n_test = _prefixo_mais_proximo(ordem, cont, ALVOS["test"])
        teste, resto = ordem[:k], ordem[k:]
        k2, n_val = _prefixo_mais_proximo(resto, cont, ALVOS["val"])
        val, treino = resto[:k2], resto[k2:]
        n_train = sum(cont[d] for d in treino)
        if dentro(n_test, ALVOS["test"]) and dentro(n_val, ALVOS["val"]) and dentro(n_train, ALVOS["train"]):
            return {"test": sorted(teste), "val": sorted(val), "train": sorted(treino)}, t
    raise RuntimeError("nenhum sorteio aceito dentro do limite de tentativas")


def principal(csv_nomes, semente, saida_csv):
    nomes, cont = contagens_por_dia(csv_nomes)
    div, tentativas = sortear(cont, semente)
    de = {d: s for s, ds in div.items() for d in ds}
    with open(saida_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nome", "dia", "divisao"])
        for n in sorted(nomes):
            w.writerow([n, n[:10], de[n[:10]]])
    resumo = {"semente": semente, "tentativas_ate_aceitar": tentativas, "n_imagens": len(nomes), "n_dias": len(cont),
              "por_divisao": {s: {"dias": len(ds), "imagens": sum(cont[d] for d in ds), "alvo": ALVOS[s], "lista_dias": ds}
                              for s, ds in div.items()}}
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    principal(sys.argv[1], int(sys.argv[2]), sys.argv[3])
