"""Filtro automático de qualidade das edições do iflens (adendo 4a, seção 7).

O filtro lê a MESMA folha cega que os avaliadores humanos leem (original | gerada, caixas numeradas, recortes por caixa),
aplica as definições da auditoria v4 e devolve uma categoria por caixa e se há objeto adicionado. Uma regra de decisão
transforma isso em "sinalizada" (descartar) ou não. Tudo o que decide é fixado em `configs/filtro_iflens_v1.json` e
registrado com hash antes de o filtro tocar as 150 imagens.

Fases:
  desenvolver  roda as configurações candidatas nas 60 folhas do piloto, compara com a referência humana ("qualquer avaliador",
               desfecho primário) e aplica a regra de seleção pré-declarada. Só usa o piloto.
  aplicar      aplica a configuração congelada a um conjunto de folhas (as 150 da amostra, depois as edições do E).

Regra de seleção (declarada antes de ver os resultados): entre as configurações com sensibilidade pontual >= 0,85 no piloto,
a de maior especificidade; empate: a de provedor de família diferente do gerador (Groq), depois a regra de decisão mais simples
(R1 < R2 < R3). Se nenhuma atinge 0,85, a de maior sensibilidade (empate: maior especificidade). No máximo 3 rodadas de ajuste
do prompt, todas registradas.

Falha de leitura (resposta que não é JSON válido, categoria desconhecida, caixas faltando) = imagem sinalizada, e a falha é contada.
Regras de decisão:
  R1  alguma caixa apagada/deslocada/alterada, ou objeto adicionado do tipo embarcacao   (a mesma do desfecho primário humano)
  R2  R1, ou alguma caixa degradada
  R3  R1, ou alguma caixa nao_avaliavel
"""
from __future__ import annotations

import argparse
import base64
import csv
import io
import json
import re
import sys
from math import sqrt
from pathlib import Path

from scripts._hashes import RAIZ, sha256

CATEGORIAS = ("valida", "degradada", "apagada", "deslocada", "alterada", "sem_objeto_original", "nao_avaliavel")
INVALIDAS = {"apagada", "deslocada", "alterada"}
REGRAS = ("R1", "R2", "R3")
PROMPT = RAIZ / "prompts" / "filtro_v1.txt"
LIMITE_BYTES = 3_500_000  # Groq: base64 de até 4 MB por imagem
LIMIAR_SENSIBILIDADE = 0.85


# ----------------------------------------------------------------------------- leitura e decisão
def preparar_imagem(caminho: Path) -> tuple[bytes, str]:
    """PNG da folha; se passar do limite, JPEG qualidade 90 e, se preciso, reduzido (deterministicamente)."""
    dados = Path(caminho).read_bytes()
    if len(dados) <= LIMITE_BYTES:
        return dados, "image/png"
    from PIL import Image
    im = Image.open(io.BytesIO(dados)).convert("RGB")
    escala = 1.0
    while True:
        im2 = im if escala == 1.0 else im.resize((int(im.width * escala), int(im.height * escala)), Image.LANCZOS)
        buf = io.BytesIO()
        im2.save(buf, "JPEG", quality=90)
        if buf.tell() <= LIMITE_BYTES or escala < 0.3:
            return buf.getvalue(), "image/jpeg"
        escala *= 0.85


def parse_resposta(texto: str | None, n_caixas: int) -> dict | None:
    """Extrai o JSON da resposta (ignora <think> e cercas ```). Devolve None se inválida."""
    if not texto:
        return None
    t = re.sub(r"<think>.*?</think>", "", texto, flags=re.S)
    t = t.replace("```json", "").replace("```", "")
    ini = t.find("{")
    if ini < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(t[ini:])
    except ValueError:
        return None
    try:
        caixas = {int(c["caixa"]): str(c["categoria"]).strip() for c in obj["caixas"]}
        add = obj["objeto_adicionado"]
        presente, tipo = bool(add["presente"]), str(add.get("tipo", "")).strip().lower()
    except (KeyError, TypeError, ValueError):
        return None
    if set(caixas) != set(range(1, n_caixas + 1)) or any(v not in CATEGORIAS for v in caixas.values()):
        return None
    return {"caixas": caixas, "adicionado": presente, "tipo": tipo}


def sinalizada(leitura: dict | None, regra: str) -> bool:
    if leitura is None:  # falha de leitura
        return True
    cats = set(leitura["caixas"].values())
    falha = bool(cats & INVALIDAS) or (leitura["adicionado"] and leitura["tipo"] == "embarcacao")
    if regra == "R1":
        return falha
    if regra == "R2":
        return falha or "degradada" in cats
    if regra == "R3":
        return falha or "nao_avaliavel" in cats
    raise ValueError(f"regra desconhecida: {regra}")


# ----------------------------------------------------------------------------- métricas e seleção
def wilson(x: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - m, c + m)


def metricas(flags: dict[str, bool], referencia: dict[str, bool]) -> dict:
    cods = sorted(referencia)
    tp = sum(flags[c] and referencia[c] for c in cods)
    fn = sum((not flags[c]) and referencia[c] for c in cods)
    tn = sum((not flags[c]) and (not referencia[c]) for c in cods)
    fp = sum(flags[c] and (not referencia[c]) for c in cods)
    npos, nneg = tp + fn, tn + fp
    nao_sinal = tn + fn
    return {"n": len(cods), "positivos": npos, "tp": tp, "fn": fn, "tn": tn, "fp": fp,
            "sensibilidade": tp / npos if npos else float("nan"), "ic_sensibilidade": wilson(tp, npos),
            "especificidade": tn / nneg if nneg else float("nan"), "ic_especificidade": wilson(tn, nneg),
            "taxa_descarte": (tp + fp) / len(cods),
            "taxa_residual": fn / nao_sinal if nao_sinal else float("nan"), "n_nao_sinalizadas": nao_sinal}


def selecionar(resultados: list[dict]) -> dict:
    """`resultados`: [{config, provedor, regra, sensibilidade, especificidade}, ...]. Regra pré-declarada no docstring."""
    ordem_regra = {r: i for i, r in enumerate(REGRAS)}
    prefer = lambda r: (0 if r["provedor"] == "groq" else 1, ordem_regra[r["regra"]])
    ok = [r for r in resultados if r["sensibilidade"] >= LIMIAR_SENSIBILIDADE]
    if ok:
        return sorted(ok, key=lambda r: (-r["especificidade"],) + prefer(r))[0]
    return sorted(resultados, key=lambda r: (-r["sensibilidade"], -r["especificidade"]) + prefer(r))[0]


# ----------------------------------------------------------------------------- provedores
def chamar_groq(modelo: str, prompt: str, dados: bytes, mime: str) -> dict:
    from groq import Groq
    cli = Groq()
    url = f"data:{mime};base64,{base64.b64encode(dados).decode()}"
    r = cli.chat.completions.create(
        model=modelo, temperature=0, max_tokens=4096,
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt},
                                               {"type": "image_url", "image_url": {"url": url}}]}])
    return {"texto": r.choices[0].message.content, "modelo_retornado": getattr(r, "model", None), "id": getattr(r, "id", None)}


def chamar_gemini(modelo: str, prompt: str, dados: bytes, mime: str) -> dict:  # não testado contra a API neste repositório
    from google import genai
    from google.genai import types
    cli = genai.Client()
    r = cli.models.generate_content(
        model=modelo, contents=[types.Part.from_bytes(data=dados, mime_type=mime), prompt],
        config=types.GenerateContentConfig(temperature=0))
    return {"texto": r.text, "modelo_retornado": getattr(r, "model_version", None), "id": getattr(r, "response_id", None)}


CHAMADAS = {"groq": chamar_groq, "gemini": chamar_gemini}


def ler_folha(provedor: str, modelo: str, folha: Path, cache: Path, chamar=None) -> dict:
    """Uma chamada por (provedor, modelo, folha); guarda a resposta bruta em `cache` e não chama de novo."""
    chave = cache / f"{provedor}__{modelo.replace('/', '_')}__p{sha256(PROMPT)[:8]}__{Path(folha).stem}.json"
    if chave.exists():
        return json.loads(chave.read_text(encoding="utf-8"))
    dados, mime = preparar_imagem(folha)
    prompt = PROMPT.read_text(encoding="utf-8")
    resp = (chamar or CHAMADAS[provedor])(modelo, prompt, dados, mime)
    resp.update({"provedor": provedor, "modelo_solicitado": modelo, "folha": Path(folha).name,
                 "prompt_sha256": sha256(PROMPT), "imagem_mime": mime, "imagem_bytes": len(dados)})
    cache.mkdir(parents=True, exist_ok=True)
    chave.write_text(json.dumps(resp, ensure_ascii=False, indent=1), encoding="utf-8")
    return resp


# ----------------------------------------------------------------------------- piloto (referência humana)
def referencia_piloto(pasta: Path) -> tuple[dict[str, bool], dict[str, int]]:
    """Referência = reprovada por qualquer avaliador (primário, `degradada` não conta), e nº de caixas por folha."""
    from scripts import analise_reavaliacao_v4 as an
    pasta = Path(pasta)
    chave = {r["codigo"] for r in csv.DictReader(open(pasta / "chave_cega.csv", encoding="utf-8"))}
    D0 = an.ler_csv_daniela(pasta / "auditoria_daniela_v3_com_tipo.csv")
    J0 = an.ler_xlsx_jose(pasta / "auditoria_jose_com_tipo.xlsx")
    Dr = an.reavaliacao(pasta / "reavaliacao_v4_daniela_caixas_corrigida.csv", pasta / "reavaliacao_v4_daniela_imagens.csv")
    Jr = an.reavaliacao(pasta / "reavaliacao_v4_jose_caixas.csv", pasta / "reavaliacao_v4_jose_imagens.csv")
    D, J = an.juntar(D0, Dr), an.juntar(J0, Jr)
    ref = {c: bool(an.reprovada(*D, c) or an.reprovada(*J, c)) for c in sorted(chave)}
    ncx: dict[str, int] = {}
    for (c, _i) in D[0]:
        ncx[c] = ncx.get(c, 0) + 1
    return ref, ncx


def categorias_humanas(pasta: Path) -> dict[str, dict]:
    """Por folha: categorias por caixa e objeto adicionado de cada avaliador (D = Daniela, J = José), após a reavaliação v4."""
    from scripts import analise_reavaliacao_v4 as an
    pasta = Path(pasta)
    D0 = an.ler_csv_daniela(pasta / "auditoria_daniela_v3_com_tipo.csv")
    J0 = an.ler_xlsx_jose(pasta / "auditoria_jose_com_tipo.xlsx")
    Dr = an.reavaliacao(pasta / "reavaliacao_v4_daniela_caixas_corrigida.csv", pasta / "reavaliacao_v4_daniela_imagens.csv")
    Jr = an.reavaliacao(pasta / "reavaliacao_v4_jose_caixas.csv", pasta / "reavaliacao_v4_jose_imagens.csv")
    out: dict[str, dict] = {}
    for nome, (cx, im) in (("D", an.juntar(D0, Dr)), ("J", an.juntar(J0, Jr))):
        for (c, i), cat in sorted(cx.items()):
            out.setdefault(c, {"D": {}, "J": {}, "adD": "", "adJ": ""})[nome][i] = cat
        for c, (flag, tipo) in im.items():
            out.setdefault(c, {"D": {}, "J": {}, "adD": "", "adJ": ""})["ad" + nome] = tipo if flag == "1" else ""
    return out


def diagnostico(pasta_piloto: Path, folhas: Path, cache: Path, config: str, regra: str = "R1") -> list[str]:
    """Uma linha por folha em que a referência humana ou o filtro marca reprovada. Só lê o cache."""
    prov, modelo = parse_config(config)
    ref, ncx = referencia_piloto(pasta_piloto)
    hum = categorias_humanas(pasta_piloto)
    fmt = lambda d: " ".join(f"{i}{v[:4]}" for i, v in sorted(d.items()))
    linhas = []
    for c in sorted(ref):
        resp = ler_folha(prov, modelo, folhas / f"{c}.png", cache)
        lit = parse_resposta(resp["texto"], ncx[c])
        flag = sinalizada(lit, regra)
        if not (ref[c] or flag):
            continue
        h = hum[c]
        mod = "FALHA_LEITURA " + (resp["texto"] or "")[:80].replace("\n", " ") if lit is None else \
            f"{fmt(lit['caixas'])} add={lit['tipo'] if lit['adicionado'] else '-'}"
        tipo = "FN" if ref[c] and not flag else ("FP" if flag and not ref[c] else "TP")
        linhas.append(f"{c} {tipo} | D: {fmt(h['D'])} add={h['adD'] or '-'} | J: {fmt(h['J'])} add={h['adJ'] or '-'} | MODELO: {mod}")
    return linhas


def parse_config(s: str) -> tuple[str, str]:
    prov, _, modelo = s.partition(":")
    if prov not in CHAMADAS or not modelo:
        raise ValueError(f"configuração inválida '{s}' (use provedor:modelo, provedor em {sorted(CHAMADAS)})")
    return prov, modelo


def desenvolver(pasta_piloto: Path, folhas: Path, cache: Path, configs: list[str], chamar=None) -> dict:
    ref, ncx = referencia_piloto(pasta_piloto)
    resultados, leituras = [], {}
    for cfg in configs:
        prov, modelo = parse_config(cfg)
        lit = {}
        for c in sorted(ref):
            resp = ler_folha(prov, modelo, folhas / f"{c}.png", cache, chamar)
            lit[c] = parse_resposta(resp["texto"], ncx[c])
        leituras[cfg] = lit
        for regra in REGRAS:
            m = metricas({c: sinalizada(lit[c], regra) for c in ref}, ref)
            m.update({"config": f"{cfg}|{regra}", "provedor": prov, "regra": regra,
                      "falhas_de_leitura": sum(v is None for v in lit.values())})
            resultados.append(m)
    return {"n_folhas": len(ref), "positivos": sum(ref.values()), "prompt_sha256": sha256(PROMPT),
            "resultados": resultados, "escolhida": selecionar(resultados)}


def principal(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("desenvolver")
    d.add_argument("--pasta-piloto", default=str(RAIZ / "data" / "auditoria_piloto_iflens"))
    d.add_argument("--folhas", required=True, help="pasta com A001.png ... A060.png (folhas do piloto)")
    d.add_argument("--cache", required=True)
    d.add_argument("--saida", required=True)
    d.add_argument("--config", action="append", required=True, help="provedor:modelo (repetir)")
    g = sub.add_parser("diagnostico")
    g.add_argument("--pasta-piloto", default=str(RAIZ / "data" / "auditoria_piloto_iflens"))
    g.add_argument("--folhas", required=True)
    g.add_argument("--cache", required=True)
    g.add_argument("--config", required=True)
    g.add_argument("--regra", default="R1", choices=REGRAS)
    a = ap.parse_args(argv)
    if a.cmd == "diagnostico":
        for linha in diagnostico(Path(a.pasta_piloto), Path(a.folhas), Path(a.cache), a.config, a.regra):
            print(linha)
        return 0
    if Path(a.saida).exists():
        print(f"{a.saida} já existe; recuso sobrescrever.", file=sys.stderr)
        return 2
    res = desenvolver(Path(a.pasta_piloto), Path(a.folhas), Path(a.cache), a.config)
    Path(a.saida).write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for r in res["resultados"]:
        print(f"{r['config']:60s} sens {r['sensibilidade']:.2f} esp {r['especificidade']:.2f} "
              f"descarte {r['taxa_descarte']:.2f} residual {r['taxa_residual']:.3f} falhas {r['falhas_de_leitura']}")
    print("escolhida:", res["escolhida"]["config"])
    return 0


if __name__ == "__main__":
    sys.exit(principal())
