"""Análise principal e de sensibilidade do experimento (adendo 4, seção 7, e adendo 4b), a partir da saída do avaliador.

Entrada: CSV da `avaliar_teste_v2` (uma linha por modelo) e, para as análises por dia e por subconjunto, as predições gravadas por ela.
Nada aqui lê imagens nem toca no teste: só lê o CSV e os .npz. Pode e deve ser ensaiado na validação antes do teste.

Contraste primário: Δ = métrica(A) − métrica(B), pareado por semente, t de Student com n−1 gl; IC95% e IC90%; margem de equivalência
(padrão ±1 pp = 0,01). Conclusão pela regra do adendo 4: melhora (IC95 > 0), piora (IC95 < 0), equivalente (IC90 dentro da margem),
inconclusivo; se "melhora" ou "piora" coincidir com "equivalente", relata-se as duas. Robustez: t de Welch (sem pareamento) e teste de
permutação por troca de sinais (exato para n ≤ 16). Contrastes secundários: correção de Holm.

Uso: python -m scripts.analisar_principal --avaliacao <csv> --saida <json> [--registro runs/REGISTRO_EXECUCOES.csv]
        [--pasta-predicoes <pasta> --divisao-nova <csv> --divisao-antiga <csv>]
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path

import numpy as np
from scipy import stats

MARGEM = 0.01
METRICAS = ("mAP50_ultralytics", "recall_small_conf025", "AP50_small", "AP50_propria")


def contraste_pareado(a: list[float], b: list[float], margem: float = MARGEM) -> dict:
    """a e b na mesma ordem de sementes. Devolve estatísticas e a conclusão pela regra do adendo 4."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if len(a) != len(b) or len(a) < 3:
        raise ValueError("são precisos pelo menos 3 pares com o mesmo número de valores")
    d = a - b
    n = len(d)
    m, sd = float(d.mean()), float(d.std(ddof=1))
    ep = sd / np.sqrt(n)
    t95, t90 = stats.t.ppf(0.975, n - 1), stats.t.ppf(0.95, n - 1)
    ic95, ic90 = (m - t95 * ep, m + t95 * ep), (m - t90 * ep, m + t90 * ep)
    melhora, piora = ic95[0] > 0, ic95[1] < 0
    equivalente = ic90[0] > -margem and ic90[1] < margem
    conclusoes = []
    if melhora:
        conclusoes.append("melhora")
    if piora:
        conclusoes.append("piora")
    if equivalente:
        conclusoes.append("equivalente")
    if not conclusoes:
        conclusoes.append("inconclusivo")
    welch = stats.ttest_ind(a, b, equal_var=False)
    if n <= 16:
        sinais = np.array(list(itertools.product((1, -1), repeat=n)))
        p_perm = float(np.mean(np.abs((sinais * d).mean(axis=1)) >= abs(m) - 1e-12))
    else:
        p_perm = None
    return {"n": n, "diferenca": m, "dp_diferenca": sd, "ic95": ic95, "ic90": ic90, "margem": margem,
            "t": float(m / ep) if ep > 0 else float("inf"), "p_t_pareado": float(2 * stats.t.sf(abs(m / ep), n - 1)) if ep > 0 else 0.0,
            "p_welch": float(welch.pvalue), "p_permutacao": p_perm, "conclusao": conclusoes}


def holm(p: list[float]) -> list[float]:
    """Valores p ajustados por Holm (mesma ordem da entrada)."""
    ordem = np.argsort(p)
    m = len(p)
    aj = np.empty(m)
    maximo = 0.0
    for k, i in enumerate(ordem):
        maximo = max(maximo, (m - k) * p[i])
        aj[i] = min(1.0, maximo)
    return aj.tolist()


def ler_avaliacao(caminho: Path) -> dict[str, dict]:
    with open(caminho, newline="", encoding="utf-8") as f:
        return {r["id_execucao"]: r for r in csv.DictReader(f)}


def semente(id_execucao: str) -> int:
    return int(id_execucao.rsplit("seed", 1)[1])


def por_braco(avaliacao: dict[str, dict], braco: str, metrica: str) -> dict[int, float]:
    return {semente(i): float(r[metrica]) for i, r in avaliacao.items() if i.startswith(f"{braco}_principal_")}


def analise_principal(avaliacao: dict[str, dict], braco_a: str = "R", braco_b: str = "C", metrica: str = "mAP50_ultralytics",
                      gpu_por_id: dict[str, str] | None = None, margem: float = MARGEM) -> dict:
    A, B = por_braco(avaliacao, braco_a, metrica), por_braco(avaliacao, braco_b, metrica)
    comuns = sorted(set(A) & set(B))
    if len(comuns) < 3:
        raise ValueError("menos de 3 sementes em comum entre os braços")
    saida = {"metrica": metrica, "contraste": f"{braco_a}-{braco_b}", "sementes": comuns,
             "principal": contraste_pareado([A[s] for s in comuns], [B[s] for s in comuns], margem),
             "margens": {str(m): contraste_pareado([A[s] for s in comuns], [B[s] for s in comuns], m)["conclusao"]
                         for m in (0.005, 0.01, 0.015)}}
    if gpu_por_id:  # sensibilidade ao hardware: só as sementes do braço B treinadas na L4
        l4 = [s for s in comuns if "L4" in gpu_por_id.get(f"{braco_b}_principal_yolo11n_seed{s}", "")]
        if len(l4) >= 3:
            saida["so_L4"] = {"sementes": l4, **contraste_pareado([A[s] for s in l4], [B[s] for s in l4], margem)}
    return saida


def dias_e_subconjunto(divisao_nova: Path, divisao_antiga: Path) -> dict[str, set[str]]:
    """Grupos de imagens do teste novo: um por dia e 'nunca_avaliadas' (eram treino na divisão antiga)."""
    antiga = {}
    with open(divisao_antiga, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            antiga[r["nome"]] = r["divisao"]
    grupos: dict[str, set[str]] = {"nunca_avaliadas": set()}
    with open(divisao_nova, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["divisao"] != "test":
                continue
            grupos.setdefault(f"dia_{r['dia']}", set()).add(r["nome"])
            if antiga.get(r["nome"]) == "train":
                grupos["nunca_avaliadas"].add(r["nome"])
    return grupos


def analise_por_grupo(pasta_predicoes: Path, avaliacao: dict[str, dict], grupos: dict[str, set[str]], braco_a: str = "R",
                      braco_b: str = "C", margem: float = MARGEM) -> dict:
    """Sensibilidade por dia e por subconjunto, com as medidas próprias (AP50 e recall small) sobre as predições gravadas.
    Descritivo: não substitui a métrica primária da API."""
    from scripts.avaliar_teste import medidas_proprias
    from scripts.avaliar_teste_v2 import carregar_predicoes

    saida = {}
    cache = {i: carregar_predicoes(Path(pasta_predicoes) / f"{i}.npz") for i in avaliacao}
    for g, nomes in sorted(grupos.items()):
        res = {}
        for metrica, chave in (("AP50_propria", "AP50_propria"), ("recall_small_conf025", "recall_small_conf025")):
            A, B = {}, {}
            for i, itens in cache.items():
                sub = [x for x in itens if x["nome"] in nomes]
                if not sub:
                    continue
                v = medidas_proprias(sub)[chave]
                if i.startswith(f"{braco_a}_principal_"):
                    A[semente(i)] = v
                elif i.startswith(f"{braco_b}_principal_"):
                    B[semente(i)] = v
            comuns = sorted(set(A) & set(B))
            ok = [s for s in comuns if np.isfinite(A[s]) and np.isfinite(B[s])]
            if len(ok) >= 3:
                res[metrica] = contraste_pareado([A[s] for s in ok], [B[s] for s in ok], margem)
        saida[g] = {"n_imagens": len(nomes), **res}
    return saida


def principal(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--avaliacao", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--registro", default=None)
    p.add_argument("--pasta-predicoes", default=None)
    p.add_argument("--divisao-nova", default=None)
    p.add_argument("--divisao-antiga", default=None)
    a = p.parse_args(argv)
    av = ler_avaliacao(Path(a.avaliacao))
    gpu = {}
    if a.registro:
        with open(a.registro, newline="", encoding="utf-8") as f:
            gpu = {r["id_execucao"]: r["gpu"] for r in csv.DictReader(f)}
    resultado = {"primaria": analise_principal(av, gpu_por_id=gpu)}
    sec = [analise_principal(av, metrica=m, gpu_por_id=gpu) for m in METRICAS[1:]]
    aj = holm([s["principal"]["p_t_pareado"] for s in sec])
    resultado["secundarias"] = [{**s, "p_holm": q} for s, q in zip(sec, aj)]
    if a.pasta_predicoes and a.divisao_nova and a.divisao_antiga:
        resultado["por_grupo"] = analise_por_grupo(Path(a.pasta_predicoes), av, dias_e_subconjunto(Path(a.divisao_nova), Path(a.divisao_antiga)))
    Path(a.saida).write_text(json.dumps(resultado, indent=2, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    pr = resultado["primaria"]["principal"]
    print(json.dumps({"primaria": {"diferenca_pp": round(100 * pr["diferenca"], 3), "ic95_pp": [round(100 * x, 3) for x in pr["ic95"]],
                                   "conclusao": pr["conclusao"]}}, ensure_ascii=False))


if __name__ == "__main__":
    principal()
