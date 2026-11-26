"""(v3, D93.) Produção do braço E, estrato padrão, uma imagem por chamada do iflens e com tempo limite por chamada.

Por que existe: o iflens no commit fixado cria o cliente do Gemini sem tempo limite (`genai.Client()`); em 26/11/2026 três chamadas de
geração nunca voltaram e o lote inteiro ficou parado. O v2 conta a tentativa de todas as fontes do lote ao despachá-lo, antes de qualquer
chamada, então cada travamento gastava uma tentativa também das fontes que nunca foram chamadas (D92, D93).

O que muda em relação ao v2 (só a execução):
  - o estrato padrão é processado uma fonte por vez, na ordem do plano, cada uma num processo `iflens.main --n 1`;
  - cada processo tem tempo limite (padrão 180 s). Ao estourar, recebe SIGINT, e o iflens grava o registro com status `started`
    (bloco `finally`); se não sair em 15 s, é encerrado e a chamada fica anotada como `sem_registro` em `chamadas_v3.jsonl`;
  - tentativa = chamada com evidência: cada `AUG_<fonte>.json` da fonte (status started, error ou ok) e cada chamada `sem_registro`
    do log (desvio registrado em DESVIOS.md, 26/11/2026). O `tentativas.json` do v2 deixa de ser lido e não é alterado.
O que não muda: plano, ordem, semente mestra, iflens no commit fixado, conferência de hashes (parâmetros, condições, prompt, plano),
modelo de geração e de classificação, cache de classificação, limite de 3 tentativas por falha técnica, bloqueio (imagem não
devolvida) não repetido. A condição sorteada depende só da semente mestra e do nome da imagem (`derive_seed` no iflens), então
chamar uma imagem por vez dá a mesma condição que o lote.
O estrato de risco continua com `geracao_4a_v3.executar_risco` (via v2), sem tempo limite; na passagem 1 ele está completo (D91).

Uso (Colab):
  PYTHONUNBUFFERED=1 python -m scripts.producao_E_v3 --passagem 1 --citra-raiz RAIZ --iflens-dir DIR --trabalho DIR [--tempo-limite 180]
"""
from __future__ import annotations

import argparse
import json
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from scripts import geracao_4a as g
from scripts import producao_E_v2 as v2
from scripts._hashes import RAIZ, sha256

LOG = "chamadas_v3.jsonl"


def conferir(P: dict, iflens_dir: Path) -> None:
    """As mesmas conferências de `geracao_4a.executar`."""
    head = subprocess.run(["git", "-C", str(iflens_dir), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != P["iflens_commit"]:
        raise RuntimeError(f"iflens em {head}, esperado {P['iflens_commit']}")
    for c in P["condicoes"].values():
        if sha256(iflens_dir / c["arquivo"]) != c["sha256"]:
            raise RuntimeError(f"{c['arquivo']} difere do registrado")
    if sha256(RAIZ / P["prompt_arquivo"]) != P["prompt_sha256"] or sha256(RAIZ / P["amostra_arquivo"]) != P["amostra_sha256"]:
        raise RuntimeError("prompt ou plano diferem dos parâmetros registrados")


def registros_da_fonte(saidas_lote: Path, nome: str) -> list[dict]:
    """Todos os registros AUG da fonte, em ordem de execução (pasta com carimbo de hora)."""
    return [json.loads(j.read_text(encoding="utf-8")) for j in sorted(Path(saidas_lote).glob(f"*/AUG_{nome}.json"))]


def ler_log(trab: Path) -> list[dict]:
    arq = trab / LOG
    return [json.loads(l) for l in arq.read_text(encoding="utf-8").splitlines() if l.strip()] if arq.exists() else []


def situacao(saidas_lote: Path, nome: str, log: list[dict], max_tent: int) -> tuple[str, int]:
    """('ok' | 'bloqueada' | 'esgotada' | 'pendente', tentativas com evidência)."""
    regs = registros_da_fonte(saidas_lote, nome)
    n = len(regs) + sum(1 for e in log if e["nome"] == nome and e["resultado"] == "sem_registro")
    if any(r.get("status") == "ok" for r in regs):
        return "ok", n
    ultimo = regs[-1] if regs else None
    if ultimo and ultimo.get("status") == "error" and not g.eh_falha_tecnica(ultimo.get("error", "")):
        return "bloqueada", n
    return ("esgotada" if n >= max_tent else "pendente"), n


def rodar_com_limite(cmd: list[str], cwd: str, limite_s: float) -> str:
    """'concluida' ou 'tempo_esgotado'. No tempo esgotado: SIGINT (o iflens grava o registro), depois kill."""
    p = subprocess.Popen(cmd, cwd=cwd)
    try:
        p.wait(timeout=limite_s)
        return "concluida"
    except subprocess.TimeoutExpired:
        p.send_signal(signal.SIGINT)
        try:
            p.wait(timeout=15)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
        return "tempo_esgotado"


def executar_padrao(P: dict, citra_raiz: Path, iflens_dir: Path, trab: Path, limite_s: float = 180, chamar=None) -> dict:
    conferir(P, iflens_dir)
    chamar = chamar or rodar_com_limite
    max_tent = P["max_tentativas_falha_tecnica"]
    cond = P["condicoes"]["padrao"]["arquivo"]
    cache = trab / "cache_classificacao.json"
    originais = trab / "originais_150"
    originais.mkdir(parents=True, exist_ok=True)
    resumo = {}
    for lote, nomes in P["lotes"].items():
        if not lote.startswith("padrao"):
            continue
        saidas = trab / "saidas" / lote
        saidas.mkdir(parents=True, exist_ok=True)
        chamadas = 0
        for nome in nomes:
            log = ler_log(trab)
            estado, n = situacao(saidas, nome, log, max_tent)
            if estado != "pendente":
                continue
            ds = trab / "pendentes" / lote
            shutil.rmtree(ds, ignore_errors=True)
            ds.mkdir(parents=True)
            for src in (g.encontrar(citra_raiz, nome, "images"), g.encontrar(citra_raiz, nome, "labels_final", ".txt")):
                shutil.copy(src, ds / src.name)
                shutil.copy(src, originais / src.name)
            antes = len(registros_da_fonte(saidas, nome))
            inicio = datetime.now(timezone.utc).isoformat()
            cmd = [sys.executable, "-m", "iflens.main", "--dataset", str(ds), "--conditions", cond, "--n", "1",
                   "--seed", str(P["semente_mestra"]), "--model", P["modelo_geracao_solicitado"],
                   "--vision-model", P["modelo_visao_classificacao"], "--prompt-file", str(RAIZ / P["prompt_arquivo"]),
                   "--classification-cache", str(cache), "--output", str(saidas)]
            fim_processo = chamar(cmd, str(iflens_dir), limite_s)
            depois = registros_da_fonte(saidas, nome)
            resultado = depois[-1].get("status") if len(depois) > antes else "sem_registro"
            entrada = {"lote": lote, "nome": nome, "tentativa": n + 1, "inicio_utc": inicio,
                       "fim_utc": datetime.now(timezone.utc).isoformat(), "processo": fim_processo, "resultado": resultado}
            with open(trab / LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
            print(json.dumps(entrada, ensure_ascii=False), flush=True)
            chamadas += 1
            time.sleep(1.1)  # o iflens cria a pasta de saída com carimbo em segundos: evita duas chamadas na mesma pasta
        log = ler_log(trab)
        estados = [situacao(saidas, n, log, max_tent)[0] for n in nomes]
        resumo[lote] = {"n": len(nomes), "ok": estados.count("ok"), "bloqueadas": estados.count("bloqueada"),
                        "esgotadas": estados.count("esgotada"), "pendentes": estados.count("pendente"), "chamadas_agora": chamadas}
    return resumo


def principal(argv=None, agora=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--passagem", type=int, choices=(1, 2), required=True)
    ap.add_argument("--citra-raiz", required=True)
    ap.add_argument("--iflens-dir", required=True)
    ap.add_argument("--trabalho", required=True)
    ap.add_argument("--tempo-limite", type=float, default=180)
    ap.add_argument("--contagem-passagem1")
    ap.add_argument("--parametros-base", default=str(g.SAIDA_PARAMETROS))
    a = ap.parse_args(argv)
    agora = agora or datetime.now(timezone.utc)
    if agora >= v2.LIMITE_JANELA_UTC:
        print("A janela de geração do 4a (até 20/12/2026) terminou; recuso gerar.", file=sys.stderr)
        return 2
    if a.passagem == 2:
        n = json.loads(Path(a.contagem_passagem1).read_text(encoding="utf-8")).get("validas") if a.contagem_passagem1 else None
        if not isinstance(n, int) or n >= v2.N_ALVO:
            print(f"A passagem 2 só roda com menos de {v2.N_ALVO} válidas na passagem 1 (contagem: {n}).", file=sys.stderr)
            return 2
    base_arq = Path(a.parametros_base)
    registrado = json.loads((RAIZ / "docs/pre_registro/hashes.json").read_text())["artefatos"]["parametros_geracao_4a.json"]["sha256"]
    if sha256(base_arq) != registrado:
        print("parametros_geracao_4a.json difere do registrado", file=sys.stderr)
        return 1
    P = v2.parametros_passagem(v2.ler_plano(), a.passagem, json.loads(base_arq.read_text(encoding="utf-8")))
    trab = Path(a.trabalho) / "E" / f"passagem{a.passagem}"
    trab.mkdir(parents=True, exist_ok=True)
    risco_incompleto = [k for k, ns in P["lotes"].items() if k.startswith("risco")
                        and sum(n in g.registros_ok(trab / "saidas" / k) for n in ns) < len(ns)]
    if risco_incompleto:
        print(f"Estrato de risco incompleto ({len(risco_incompleto)} lotes): o v3 só faz o padrão; use o v2 para o risco.", file=sys.stderr)
    rp = executar_padrao(P, Path(a.citra_raiz), Path(a.iflens_dir), trab, a.tempo_limite)
    todos = {}
    for lote in P["lotes"]:
        todos.update(g.registros_ok(trab / "saidas" / lote))
    rp = {k: v for k, v in rp.items() if v["chamadas_agora"] or v["ok"] < v["n"]}  # só lotes com chamada agora ou incompletos
    print(json.dumps({"passagem": a.passagem, "padrao": rp, "ok_total": len(todos),
                      "modelos_retornados": sorted({r.get("generation_model_returned") or "" for r in todos.values()})},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
