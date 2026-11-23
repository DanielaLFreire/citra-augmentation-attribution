"""Sensibilidade ao hardware (adendo 4b, seção 5.2): R−C com o controle inteiro treinado na L4.

C_L4 = para cada semente, a réplica de C na L4 (`C_principalL4_...`, sementes 7, 42, 123, 2024, 31415) quando existe, e senão o C do plano
principal, que nas outras cinco sementes (101, 1001, 2025, 4242, 27182) já foi treinado na L4 (confere-se pelo registro). R foi todo treinado na L4.
Também mede o efeito do hardware em si: réplica L4 menos C original (A100), pareado por semente, nas 5 sementes que têm os dois.
É descritivo. A conclusão primária do adendo 4 continua sendo a do C original com os 10 pares.

Uso: python -m scripts.analisar_hardware --avaliacao <csv> --registro runs/REGISTRO_EXECUCOES.csv --saida <json>
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from scripts.analisar_principal import MARGEM, contraste_pareado, ler_avaliacao, por_braco, semente

SEMENTES_REPLICA = [7, 42, 123, 2024, 31415]
METRICA = "mAP50_ultralytics"


def _valores_por_prefixo(av: dict, prefixo: str, metrica: str) -> dict[int, float]:
    return {semente(i): float(r[metrica]) for i, r in av.items() if i.startswith(prefixo)}


def montar_C_L4(av: dict, gpu: dict[str, str], metrica: str = METRICA) -> tuple[dict[int, float], dict[int, str]]:
    replica = _valores_por_prefixo(av, "C_principalL4_", metrica)
    original = por_braco(av, "C", metrica)
    c_l4, origem = {}, {}
    for s in sorted(set(replica) | set(original)):
        if s in replica:
            c_l4[s], origem[s] = replica[s], "replica_L4"
        elif "L4" in gpu.get(f"C_principal_yolo11n_seed{s}", ""):
            c_l4[s], origem[s] = original[s], "original_L4"
    return c_l4, origem


def analisar(av: dict, gpu: dict[str, str], metrica: str = METRICA, margem: float = MARGEM) -> dict:
    r = por_braco(av, "R", metrica)
    c_l4, origem = montar_C_L4(av, gpu, metrica)
    comuns = sorted(set(r) & set(c_l4))
    res = {"metrica": metrica, "sementes_R_C_L4": comuns, "origem_C_L4": {str(s): origem[s] for s in comuns}}
    if len(comuns) >= 3:
        res["R_menos_C_L4"] = contraste_pareado([r[s] for s in comuns], [c_l4[s] for s in comuns], margem)
    replica = _valores_por_prefixo(av, "C_principalL4_", metrica)
    original = por_braco(av, "C", metrica)
    par = sorted(set(replica) & set(original))
    if len(par) >= 3:
        res["efeito_hardware_L4_menos_A100"] = {"sementes": par, **contraste_pareado([replica[s] for s in par], [original[s] for s in par], margem)}
    return res


def principal(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--avaliacao", required=True)
    p.add_argument("--registro", required=True)
    p.add_argument("--saida", required=True)
    a = p.parse_args(argv)
    with open(a.registro, newline="", encoding="utf-8") as f:
        gpu = {r["id_execucao"]: r["gpu"] for r in csv.DictReader(f)}
    res = analisar(ler_avaliacao(Path(a.avaliacao)), gpu)
    Path(a.saida).write_text(json.dumps(res, indent=2, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    out = {k: {"diferenca_pp": round(100 * v["diferenca"], 3), "ic95_pp": [round(100 * x, 3) for x in v["ic95"]],
               "conclusao": v["conclusao"], "n": v["n"]} for k, v in res.items() if isinstance(v, dict) and "diferenca" in v}
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    principal()
