"""Produção do braço E (adendo 4a, seção 10; plano D78). Executa as gerações do plano, na ordem do plano, de forma retomável.

Reutiliza, sem alterar, o que gerou as 150 (D72, D74): `geracao_4a.executar` para o estrato padrão e `geracao_4a_v3.executar_risco` para o
de risco (classificação da original com o esquema padrão; variação só entre valores de risco; céu mantido quando a original já é `overcast`).
Mesmos: iflens no commit fixado, `gemini-3.1-flash-lite-image`, classificador Groq `qwen/qwen3.8-27b`, prompt v1, falha técnica repetida até 3 vezes,
imagem não devolvida (bloqueio) não repetida e não válida.

O que muda em relação às 150: a lista de fontes, o estrato e a semente mestra vêm do plano registrado (`manifests/plano_producao_E_seed20261202.csv`),
e cada passagem tem pasta própria (`<trabalho>/E/passagem<N>`).
Passagem 2: só roda com `--contagem-passagem1` apontando para um JSON `{"validas": N}` com N < 1.370 (a contagem usa o filtro congelado, se aprovado,
e fica registrada em decisão antes de gerar). O script não conta validade: a contagem (modelo devolvido, SHA único, filtro) é etapa posterior.
Janela: o 4a fixa 20/12/2026 como fim da geração; o script recusa gerar depois de 21/12/2026 00:00 em Brasília.

Uso (Colab, com GEMINI_API_KEY e GROQ_API_KEY no ambiente e o iflens no commit fixado):
  python -m scripts.producao_E --passagem 1 --citra-raiz RAIZ --iflens-dir DIR --trabalho DIR [--max-lotes N]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts import geracao_4a as g
from scripts import geracao_4a_v3 as v3
from scripts._hashes import RAIZ, sha256

PLANO = RAIZ / "manifests" / "plano_producao_E_seed20261202.csv"
TAMANHO_LOTE = 30
N_ALVO = 1370
LIMITE_JANELA_UTC = datetime(2026, 12, 21, 3, 0, tzinfo=timezone.utc)  # 21/12/2026 00:00 em Brasília (UTC-3)


def ler_plano(caminho: Path = PLANO) -> list[dict]:
    return list(csv.DictReader(open(caminho, encoding="utf-8", newline="")))


def parametros_passagem(plano: list[dict], passagem: int, base: dict, tamanho: int = TAMANHO_LOTE) -> dict:
    """Parâmetros no formato do `geracao_4a`, com lotes por estrato na ordem do plano. `base` = manifests/parametros_geracao_4a.json."""
    linhas = [r for r in plano if int(r["passagem"]) == passagem]
    if not linhas:
        raise ValueError(f"passagem {passagem} ausente no plano")
    sementes = {int(r["semente_mestra"]) for r in linhas}
    if len(sementes) != 1:
        raise ValueError("a passagem tem mais de uma semente mestra")
    lotes: dict[str, list[str]] = {}
    for estrato in ("padrao", "risco"):
        nomes = [r["nome"] for r in sorted(linhas, key=lambda r: int(r["posicao"])) if r["estrato"] == estrato]
        for k in range(0, len(nomes), tamanho):
            lotes[f"{estrato}_{k // tamanho + 1:03d}"] = nomes[k:k + tamanho]
    P = dict(base)
    P.update({"semente_mestra": sementes.pop(), "lotes": lotes, "n_imagens": len(linhas),
              "amostra_arquivo": str(PLANO.relative_to(RAIZ)), "amostra_sha256": sha256(PLANO), "tamanho_lote": tamanho,
              "por_estrato": {e: sum(r["estrato"] == e for r in linhas) for e in ("padrao", "risco")}})
    return P


def principal(argv=None, agora=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--passagem", type=int, choices=(1, 2), required=True)
    ap.add_argument("--citra-raiz", required=True)
    ap.add_argument("--iflens-dir", required=True)
    ap.add_argument("--trabalho", required=True)
    ap.add_argument("--max-lotes", type=int, default=None, help="processa só os N primeiros lotes ainda incompletos de cada estrato")
    ap.add_argument("--contagem-passagem1", help="obrigatório na passagem 2: JSON com {'validas': N}, N < 1370")
    ap.add_argument("--parametros-base", default=str(g.SAIDA_PARAMETROS))
    a = ap.parse_args(argv)
    agora = agora or datetime.now(timezone.utc)
    if agora >= LIMITE_JANELA_UTC:
        print("A janela de geração do 4a (até 20/12/2026) terminou; recuso gerar.", file=sys.stderr)
        return 2
    if a.passagem == 2:
        if not a.contagem_passagem1:
            print("A passagem 2 exige --contagem-passagem1 (4a, seção 10).", file=sys.stderr)
            return 2
        n = json.loads(Path(a.contagem_passagem1).read_text(encoding="utf-8")).get("validas")
        if not isinstance(n, int) or n >= N_ALVO:
            print(f"A passagem 2 só roda com menos de {N_ALVO} válidas na passagem 1 (contagem: {n}).", file=sys.stderr)
            return 2
    base = json.loads(Path(a.parametros_base).read_text(encoding="utf-8"))
    if sha256(Path(a.parametros_base)) != json.loads((RAIZ / "docs/pre_registro/hashes.json").read_text())["artefatos"]["manifests/parametros_geracao_4a.json"]["sha256"]:
        print("parametros_geracao_4a.json difere do registrado", file=sys.stderr)
        return 1
    P = parametros_passagem(ler_plano(), a.passagem, base)
    trab = Path(a.trabalho) / "E" / f"passagem{a.passagem}"
    trab.mkdir(parents=True, exist_ok=True)
    if a.max_lotes is not None:
        def incompletos(prefixo):
            ks = [k for k in P["lotes"] if k.startswith(prefixo)]
            falta = [k for k in ks if sum(n in g.registros_ok(trab / "saidas" / k) for n in P["lotes"][k]) < len(P["lotes"][k])]
            return falta[:a.max_lotes]
        manter = set(incompletos("padrao")) | set(incompletos("risco"))
        P["lotes"] = {k: v for k, v in P["lotes"].items() if k in manter}
    padrao = dict(P, lotes={k: v for k, v in P["lotes"].items() if k.startswith("padrao")}, condicoes={"padrao": P["condicoes"]["padrao"]})
    tmp = trab / "parametros_padrao_tmp.json"
    tmp.write_text(json.dumps(padrao))
    rp = g.executar(tmp, Path(a.citra_raiz), Path(a.iflens_dir), trab) if padrao["lotes"] else {"lotes": {}}
    rr = v3.executar_risco(P, Path(a.citra_raiz), Path(a.iflens_dir), trab)
    todos = {}
    for lote in json.loads(tmp.read_text())["lotes"] | {k: 0 for k in P["lotes"] if k.startswith("risco")}:
        todos.update(g.registros_ok(trab / "saidas" / lote))
    print(json.dumps({"passagem": a.passagem, "padrao": rp["lotes"], "risco": rr, "ok_nesta_chamada": len(todos),
                      "modelos_retornados": sorted({r.get("generation_model_returned") or "" for r in todos.values()})}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
