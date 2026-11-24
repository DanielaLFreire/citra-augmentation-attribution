"""Sorteio da amostra de 150 imagens do adendo 4a (lacrado, D64). Protocolo da seção 4 do adendo.

Passos, na ordem em que o adendo os fixa:
1. População = split de treino de `divisao_blocos_dias.csv` (sha256 conferido contra o do adendo), menos os
   3 quadros da quarentena D10, com pelo menos 1 caixa em `labels_final` (manifestos por split). Essa é a LISTA
   ELEGÍVEL (também a lista de fontes do braço E, seção 10). Ela e o hash dela são gravados ANTES de sortear.
2. Pool da amostra = lista elegível menos as imagens do piloto (30 do `chave_cega.csv`).
3. Bloco = data + hora + dezena de minutos do nome (`DD.MM.AAAA-HH-MM-SS`; dezena = minuto // 10).
4. Sorteio com `random.Random(semente)`, na ordem fixa de chamadas: (a) `sample` de `n` blocos entre os blocos do pool
   em ordem lexicográfica; (b) `choice` de 1 imagem em cada bloco sorteado, na ordem lexicográfica do bloco;
   (c) `sample` de `n_risco` posições (entre as `n` imagens, na ordem do passo b) para o estrato de risco.
   Se houver menos de `n` blocos, usa-se 1 imagem em todos os blocos e o restante sai de `sample` entre as imagens
   que sobraram, sem restrição de bloco (o passo b então segue a mesma ordem).
5. Grava a amostra e o relatório (entradas com hash, contagens, semente, versão do Python). Recusa sobrescrever.

Uso:
  python -m scripts.sortear_amostra_4a --saida-lista manifests/lista_elegivel_4a.csv \\
      --saida-amostra manifests/amostra_4a_seed20261201.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

from scripts._hashes import RAIZ, sha256

SEMENTE = 20261201
N_AMOSTRA = 150
N_RISCO = 30
HASH_DIVISAO_4A = "1e7674fdef8dff8413e93f7e9562d830dfe792dd85d35fe9033282e4e2e3bea9"
QUARENTENA_D10 = ("11.05.2022-14-13-13", "07.07.2022-09-39-44", "11.07.2022-09-43-17")
DIVISAO = RAIZ / "data" / "divisao_citra_blocos_dias" / "divisao_blocos_dias.csv"
MANIFESTOS = [RAIZ / "data" / "labels_final_citra" / f"labels_final_manifest_{s}.json" for s in ("train", "val", "test")]
CHAVE_PILOTO = RAIZ / "data" / "auditoria_piloto_iflens" / "chave_cega.csv"


def bloco(nome: str) -> str:
    """`DD.MM.AAAA-HH-MM-SS` -> `DD.MM.AAAA-HH-D` (D = minuto // 10)."""
    data, hh, mm, _ss = nome.split("-")
    return f"{data}-{hh}-{int(mm) // 10}"


def ler_caixas(manifestos) -> dict[str, int]:
    caixas: dict[str, int] = {}
    for m in manifestos:
        for a in json.loads(Path(m).read_text(encoding="utf-8"))["arquivos"]:
            caixas[a["imagem_id"]] = int(a["n_boxes"])
    return caixas


def ler_piloto(chave: Path) -> set[str]:
    with open(chave, encoding="utf-8", newline="") as f:
        return {r["imagem"].removesuffix(".png") for r in csv.DictReader(f)}


def lista_elegivel(divisao: Path, caixas: dict[str, int], quarentena=QUARENTENA_D10) -> list[dict]:
    with open(divisao, encoding="utf-8", newline="") as f:
        treino = [r for r in csv.DictReader(f) if r["divisao"] == "train"]
    saida = []
    for r in sorted(treino, key=lambda r: r["nome"]):
        n = r["nome"]
        if n in quarentena:
            continue
        if caixas.get(n, 0) >= 1:
            saida.append({"nome": n, "dia": r["dia"], "bloco": bloco(n), "n_caixas": caixas[n]})
    return saida


def sortear(pool: list[str], semente: int = SEMENTE, n: int = N_AMOSTRA, n_risco: int = N_RISCO) -> list[dict]:
    """`pool`: nomes elegíveis (sem as exclusões da amostra). Devolve `n` linhas {nome, bloco, estrato}."""
    if len(pool) < n:
        raise ValueError(f"Pool com {len(pool)} imagens, menos que {n}.")
    rng = random.Random(semente)
    por_bloco: dict[str, list[str]] = {}
    for nome in sorted(pool):
        por_bloco.setdefault(bloco(nome), []).append(nome)
    blocos = sorted(por_bloco)
    if len(blocos) >= n:
        escolhidos = sorted(rng.sample(blocos, n))
        imagens = [rng.choice(por_bloco[b]) for b in escolhidos]
    else:
        escolhidos_b = list(blocos)
        imagens = [rng.choice(por_bloco[b]) for b in escolhidos_b]
        restantes = sorted(set(pool) - set(imagens))
        imagens += rng.sample(restantes, n - len(imagens))
        imagens = sorted(imagens)
    risco = set(rng.sample(range(len(imagens)), n_risco))
    return [{"ordem": i + 1, "nome": nome, "bloco": bloco(nome),
             "estrato": "risco" if i in risco else "padrao"} for i, nome in enumerate(imagens)]


def _gravar_csv(caminho: Path, linhas: list[dict]) -> None:
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


def principal(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--saida-lista", required=True)
    ap.add_argument("--saida-amostra", required=True)
    ap.add_argument("--semente", type=int, default=SEMENTE)
    ap.add_argument("--divisao", default=str(DIVISAO))
    ap.add_argument("--n", type=int, default=N_AMOSTRA)
    ap.add_argument("--n-risco", type=int, default=N_RISCO)
    ap.add_argument("--nao-conferir-hash-divisao", action="store_true", help="só para ensaios com dados sintéticos")
    a = ap.parse_args(argv)

    saida_lista, saida_amostra = Path(a.saida_lista), Path(a.saida_amostra)
    for p in (saida_lista, saida_amostra):
        if p.exists():
            print(f"{p} já existe; recuso sobrescrever.", file=sys.stderr)
            return 2
    h_div = sha256(Path(a.divisao))
    if not a.nao_conferir_hash_divisao and h_div != HASH_DIVISAO_4A:
        print(f"Hash da divisão ({h_div}) difere do fixado no adendo 4a ({HASH_DIVISAO_4A}).", file=sys.stderr)
        return 2

    caixas = ler_caixas(MANIFESTOS)
    elegiveis = lista_elegivel(Path(a.divisao), caixas)
    _gravar_csv(saida_lista, elegiveis)  # a lista e o hash dela existem antes do sorteio
    h_lista = sha256(saida_lista)

    piloto = ler_piloto(CHAVE_PILOTO)
    pool = [r["nome"] for r in elegiveis if r["nome"] not in piloto]
    amostra = sortear(pool, a.semente, a.n, a.n_risco)
    _gravar_csv(saida_amostra, amostra)

    relatorio = {
        "adendo": "adendo4a_fidelidade_iflens.md", "semente": a.semente, "n": a.n, "n_risco": a.n_risco,
        "python": sys.version.split()[0],
        "entradas": {"divisao_sha256": h_div,
                     "manifestos_sha256": {m.name: sha256(m) for m in MANIFESTOS},
                     "chave_piloto_sha256": sha256(CHAVE_PILOTO)},
        "lista_elegivel": {"arquivo": saida_lista.name, "sha256": h_lista, "n_imagens": len(elegiveis),
                           "n_blocos": len({r["bloco"] for r in elegiveis})},
        "pool_amostra": {"n_imagens": len(pool), "n_blocos": len({bloco(n) for n in pool}),
                         "excluidas_piloto_no_treino": sorted(set(piloto) & {r["nome"] for r in elegiveis})},
        "amostra": {"arquivo": saida_amostra.name, "sha256": sha256(saida_amostra), "n_imagens": len(amostra),
                    "n_blocos": len({r["bloco"] for r in amostra}),
                    "por_estrato": {e: sum(r["estrato"] == e for r in amostra) for e in ("padrao", "risco")}},
    }
    Path(str(saida_amostra) + ".relatorio.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"lista": relatorio["lista_elegivel"], "pool": {k: relatorio["pool_amostra"][k] for k in ("n_imagens", "n_blocos")},
                      "amostra": relatorio["amostra"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
