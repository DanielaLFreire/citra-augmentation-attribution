"""Geração das 150 edições da amostra do adendo 4a (lacrado, D64) com o iflens fixado no commit 0bd983f.

Duas etapas:
  parametros  Constrói `manifests/parametros_geracao_4a.json` a partir da amostra sorteada (D65) e dos arquivos do iflens no commit
              fixado. É determinístico, não precisa das imagens e é registrado com hash ANTES de qualquer geração.
  executar    (Colab ou local, com as imagens do CITRA e as chaves GEMINI_API_KEY e GROQ_API_KEY no ambiente) prepara os lotes
              e chama `python -m iflens.main` por lote, gerando só o que falta. Pode ser repetido depois de uma queda.

Desenho: o estrato padrão (120 imagens) usa `conditions-citra.yaml`; o de risco (30), `conditions-citra-risk.yaml` (seção 4 do 4a,
README do iflens). Cada estrato é dividido em lotes de 30 imagens. A variação de condições depende só da semente mestra e do nome da
imagem (`derive_seed`), então a divisão em lotes e as retomadas não a alteram. A geração em si não é determinística (sem semente na API).

Falha técnica (erro de rede, HTTP, tempo esgotado) pode ser repetida até 3 tentativas por imagem, com a mesma condição. Ausência de
imagem devolvida (bloqueio) não é repetida e fica como não válida (adendo 4a, seção 10). O número de tentativas fica em
`tentativas.json`.

Uso:
  python -m scripts.geracao_4a parametros --iflens-dir /caminho/iflens
  python -m scripts.geracao_4a executar --parametros manifests/parametros_geracao_4a.json --citra-raiz RAIZ --iflens-dir DIR --trabalho DIR
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

from scripts._hashes import RAIZ, sha256

COMMIT_IFLENS = "0bd983f30ecabd8aa1d1682faafe318e1d096e4c"
SEMENTE_MESTRA = 20261205
SEMENTE_FOLHAS_CEGAS = 20261206
MODELO_GERACAO = "gemini-3.1-flash-lite-image"
MODELO_VISAO = "qwen/qwen3.8-27b"
TAMANHO_LOTE = 30
MAX_TENTATIVAS = 3
AMOSTRA = RAIZ / "manifests" / "amostra_4a_seed20261201.csv"
PROMPT_V1 = RAIZ / "prompts" / "prompt_v1.txt"
PROMPT_V1_SHA = "5437d06c0fc6daa06cd0b09782fcbd6aca0f5ad87c4a27dbc78b2d7144404f64"
SAIDA_PARAMETROS = RAIZ / "manifests" / "parametros_geracao_4a.json"
CONDICOES = {"padrao": "conditions-citra.yaml", "risco": "conditions-citra-risk.yaml"}


def lotes_de(amostra: list[dict], tamanho: int = TAMANHO_LOTE) -> dict[str, list[str]]:
    """Divide cada estrato, na ordem da amostra, em lotes de `tamanho`: {'padrao_01': [nomes], ...}."""
    por_estrato: dict[str, list[str]] = {}
    for r in sorted(amostra, key=lambda r: int(r["ordem"])):
        por_estrato.setdefault(r["estrato"], []).append(r["nome"])
    lotes = {}
    for estrato, nomes in sorted(por_estrato.items()):
        for k in range(0, len(nomes), tamanho):
            lotes[f"{estrato}_{k // tamanho + 1:02d}"] = nomes[k:k + tamanho]
    return lotes


def eh_falha_tecnica(erro: str | None) -> bool:
    """Falha técnica = erro de rede/HTTP/tempo. Imagem não devolvida (AssertionError do iflens) não é técnica."""
    if not erro:
        return False
    return "AssertionError" not in erro and "Generated image is None" not in erro


def construir_parametros(iflens_dir: Path) -> dict:
    iflens_dir = Path(iflens_dir)
    head = subprocess.run(["git", "-C", str(iflens_dir), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != COMMIT_IFLENS:
        raise RuntimeError(f"iflens em {head}, esperado {COMMIT_IFLENS}")
    with open(AMOSTRA, encoding="utf-8", newline="") as f:
        amostra = list(csv.DictReader(f))
    if sha256(PROMPT_V1) != PROMPT_V1_SHA:
        raise RuntimeError("prompt_v1.txt difere do hash do adendo 4a")
    lotes = lotes_de(amostra)
    return {
        "adendo": "adendo4a_fidelidade_iflens.md (seções 3 e 4)",
        "iflens_commit": COMMIT_IFLENS,
        "semente_mestra": SEMENTE_MESTRA,
        "semente_folhas_cegas": SEMENTE_FOLHAS_CEGAS,
        "modelo_geracao_solicitado": MODELO_GERACAO,
        "modelo_visao_classificacao": MODELO_VISAO,
        "prompt_arquivo": "prompts/prompt_v1.txt", "prompt_sha256": PROMPT_V1_SHA,
        "condicoes": {e: {"arquivo": a, "sha256": sha256(iflens_dir / a)} for e, a in CONDICOES.items()},
        "amostra_arquivo": "manifests/amostra_4a_seed20261201.csv", "amostra_sha256": sha256(AMOSTRA),
        "tamanho_lote": TAMANHO_LOTE, "max_tentativas_falha_tecnica": MAX_TENTATIVAS,
        "n_imagens": len(amostra), "por_estrato": {e: sum(r["estrato"] == e for r in amostra) for e in CONDICOES},
        "lotes": lotes,
    }


# ----------------------------------------------------------------------------- execução
def encontrar(raiz: Path, nome: str, subpasta: str, ext: str | None = None) -> Path:
    achados = sorted(p for p in Path(raiz).glob(f"*/{subpasta}/{nome}.*") if ext is None or p.suffix.lower() == ext)
    if len(achados) != 1:
        raise FileNotFoundError(f"{nome} em {raiz}/*/{subpasta}: {len(achados)} arquivos")
    return achados[0]


def registros_ok(pasta_saidas: Path) -> dict[str, dict]:
    """Registros AUG_*.json com status ok em `pasta_saidas/*/`, por nome de imagem (stem)."""
    ok = {}
    for j in sorted(Path(pasta_saidas).glob("*/AUG_*.json")):
        r = json.loads(j.read_text(encoding="utf-8"))
        if r.get("status") == "ok":
            ok[Path(r["image"]).stem] = r
    return ok


def ultimo_erro(pasta_saidas: Path) -> dict[str, str]:
    erros = {}
    for j in sorted(Path(pasta_saidas).glob("*/AUG_*.json")):
        r = json.loads(j.read_text(encoding="utf-8"))
        if r.get("status") == "error":
            erros[Path(r["image"]).stem] = r.get("error", "")
    return erros


def executar(params_json: Path, citra_raiz: Path, iflens_dir: Path, trabalho: Path, chamar=None, limite_lotes: int | None = None) -> dict:
    P = json.loads(Path(params_json).read_text(encoding="utf-8"))
    iflens_dir, trabalho = Path(iflens_dir), Path(trabalho)
    head = subprocess.run(["git", "-C", str(iflens_dir), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if head != P["iflens_commit"]:
        raise RuntimeError(f"iflens em {head}, esperado {P['iflens_commit']}")
    for e, c in P["condicoes"].items():
        if sha256(iflens_dir / c["arquivo"]) != c["sha256"]:
            raise RuntimeError(f"{c['arquivo']} difere do registrado")
    if sha256(RAIZ / P["prompt_arquivo"]) != P["prompt_sha256"] or sha256(RAIZ / P["amostra_arquivo"]) != P["amostra_sha256"]:
        raise RuntimeError("prompt ou amostra diferem dos parâmetros registrados")
    estrato_de = {n: e for e, nomes in ((l.split("_")[0], ns) for l, ns in P["lotes"].items()) for n in nomes}
    (trabalho / "saidas").mkdir(parents=True, exist_ok=True)
    originais = trabalho / "originais_150"
    originais.mkdir(exist_ok=True)
    tent_arq = trabalho / "tentativas.json"
    tentativas: dict[str, int] = json.loads(tent_arq.read_text()) if tent_arq.exists() else {}
    cache = trabalho / "cache_classificacao.json"
    resumo = {"lotes": {}}
    for k, (lote, nomes) in enumerate(P["lotes"].items()):
        if limite_lotes is not None and k >= limite_lotes:
            break
        saidas = trabalho / "saidas" / lote
        saidas.mkdir(parents=True, exist_ok=True)
        feitos = registros_ok(saidas)
        erros = ultimo_erro(saidas)
        pend = []
        for n in nomes:
            if n in feitos:
                continue
            if n in erros and not eh_falha_tecnica(erros[n]):
                continue  # bloqueio: não é repetido
            if tentativas.get(n, 0) >= P["max_tentativas_falha_tecnica"]:
                continue
            pend.append(n)
        if pend:
            ds = trabalho / "pendentes" / lote
            shutil.rmtree(ds, ignore_errors=True)
            ds.mkdir(parents=True)
            for n in pend:
                img, lab = encontrar(citra_raiz, n, "images"), encontrar(citra_raiz, n, "labels_final", ".txt")
                for src in (img, lab):
                    shutil.copy(src, ds / src.name)
                    shutil.copy(src, originais / src.name)
                tentativas[n] = tentativas.get(n, 0) + 1
            tent_arq.write_text(json.dumps(tentativas, indent=1, sort_keys=True))
            cmd = [sys.executable, "-m", "iflens.main", "--dataset", str(ds), "--conditions", P["condicoes"][estrato_de[nomes[0]]]["arquivo"],
                   "--n", str(len(pend)), "--seed", str(P["semente_mestra"]), "--model", P["modelo_geracao_solicitado"],
                   "--vision-model", P["modelo_visao_classificacao"], "--prompt-file", str(RAIZ / P["prompt_arquivo"]), "--classification-cache", str(cache), "--output", str(saidas)]
            (chamar or subprocess.run)(cmd, cwd=str(iflens_dir), check=False)
        feitos = registros_ok(saidas)
        resumo["lotes"][lote] = {"n": len(nomes), "ok": sum(n in feitos for n in nomes), "tentadas_agora": len(pend)}
    todos = {}
    for lote in P["lotes"]:
        todos.update(registros_ok(trabalho / "saidas" / lote))
    resumo.update({"ok_total": len(todos),
                   "modelos_retornados": sorted({r.get("generation_model_returned") or "" for r in todos.values()}),
                   "mesma_proporcao": sum(bool(r.get("same_aspect_ratio")) for r in todos.values())})
    return resumo


def principal(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a1 = sub.add_parser("parametros")
    a1.add_argument("--iflens-dir", required=True)
    a1.add_argument("--saida", default=str(SAIDA_PARAMETROS))
    a2 = sub.add_parser("executar")
    a2.add_argument("--parametros", default=str(SAIDA_PARAMETROS))
    a2.add_argument("--citra-raiz", required=True)
    a2.add_argument("--iflens-dir", required=True)
    a2.add_argument("--trabalho", required=True)
    a2.add_argument("--limite-lotes", type=int, default=None, help="só para teste: processa os N primeiros lotes")
    a = ap.parse_args(argv)
    if a.cmd == "parametros":
        if Path(a.saida).exists():
            print(f"{a.saida} já existe; recuso sobrescrever.", file=sys.stderr)
            return 2
        P = construir_parametros(Path(a.iflens_dir))
        Path(a.saida).write_text(json.dumps(P, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: P[k] for k in ("iflens_commit", "semente_mestra", "n_imagens", "por_estrato", "amostra_sha256")}, indent=1))
        print({l: len(n) for l, n in P["lotes"].items()})
        return 0
    res = executar(Path(a.parametros), Path(a.citra_raiz), Path(a.iflens_dir), Path(a.trabalho), limite_lotes=a.limite_lotes)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
