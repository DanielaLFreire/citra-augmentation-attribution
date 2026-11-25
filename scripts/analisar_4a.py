"""Análise do adendo 4a (lacrado, D64) sobre as 150 edições auditadas. Registrado ANTES de qualquer avaliação humana ser lida.

Entradas: os dois CSVs preenchidos (Daniela e José, `auditoria_modelo.csv`), a `chave_cega.csv` (código -> imagem), a amostra sorteada
(`manifests/amostra_4a_seed20261201.csv`: nome, bloco, estrato) e, para a segunda etapa, a saída do filtro congelado
(`filtro_llm_iflens aplicar`: codigo, sinalizada). A primeira etapa (sem o filtro) não precisa do filtro.

Definições (4a, seções 5, 6, 7, 8 e 9):
  reprovada (por avaliador)  alguma caixa apagada, deslocada ou alterada, OU objeto adicionado que seja embarcação (seção 5).
                             `objeto_adicionado = 1` com a observação nomeando só boia, ave, pessoa ou similar vale como adição NÃO embarcação
                             (secundário, seção 5). Sem tipo na observação, conta como embarcação (conservador). A versão que conta QUALQUER
                             objeto adicionado (a do piloto e a do desenvolvimento do filtro) é calculada ao lado, como sensibilidade.
  primária                   reprovada por QUALQUER avaliador. Sensibilidade: reprovada pelos DOIS.
  ruído herdado              sem_objeto_original, original_sem_rotulo e nao_avaliavel: contados à parte, fora da taxa.
  IC                         Wilson 95%; também bootstrap por blocos (seção 4), 10.000 reamostragens, semente 20261207.
  concordância               kappa de Cohen em "imagem reprovada" (limiar 0,60, seção 6), em objeto adicionado, original sem rótulo e na
                             categoria da caixa (6 categorias), IC95% por bootstrap de imagens (semente 20261207).
  filtro                     referência = reprovada por qualquer avaliador; sensibilidade, especificidade, taxa de descarte, taxa residual
                             (reprovadas e não sinalizadas / não sinalizadas), todas com Wilson. Regra de uso do E (seção 9): sensibilidade
                             pontual >= 0,80 E taxa residual pontual <= 0,07. Taxa por consenso e por estrato: descritivas.
Nada aqui decide nada sozinho: o script imprime os números e a regra da seção 9; a interpretação é registrada na DECISOES.md.

Uso:
  python -m scripts.analisar_4a --csv-a daniela.csv --csv-b jose.csv --chave chave_cega.csv [--filtro sinalizadas.csv] --saida analise_4a.json
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import Counter
from math import isnan, sqrt
from pathlib import Path

from scripts._hashes import RAIZ
from scripts.auditoria_recortes_iflens import CATEGORIAS, INVALIDAS

SEMENTE_BOOTSTRAP = 20261207
N_BOOTSTRAP = 10000
LIMIAR_KAPPA = 0.60
LIMIAR_SENSIBILIDADE = 0.80
LIMIAR_RESIDUAL = 0.07
AMOSTRA = RAIZ / "manifests" / "amostra_4a_seed20261201.csv"
NAO_EMBARCACAO = re.compile(r"\b(boia|boias|boi|ave|aves|gaivota|gaivotas|passaro|passaros|pessoa|pessoas|banhista|aviao|helicoptero|drone)\b")
EMBARCACAO = re.compile(r"\b(embarcacao|embarcacoes|barco|barcos|navio|navios|lancha|veleiro|bote|rebocador|balsa)\b")


def sem_acento(s: str) -> str:
    t = str.maketrans("áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ", "aaaaeeiooouc" "AAAAEEIOOOUC")
    return s.translate(t).lower()


def wilson(x: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = x / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    m = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - m, c + m)


def cohen_kappa(a: list, b: list) -> float:
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb.get(k, 0) for k in ca) / (n * n)
    return float("nan") if pe == 1 else (po - pe) / (1 - pe)


def percentis(valores: list[float], nivel: float = 0.95) -> tuple[float, float]:
    v = sorted(x for x in valores if not isnan(x))
    if not v:
        return (float("nan"), float("nan"))
    a = (1 - nivel) / 2
    return (v[int(a * (len(v) - 1))], v[int(round((1 - a) * (len(v) - 1)))])


def ic_kappa(a: list, b: list, semente: int = SEMENTE_BOOTSTRAP, b_rep: int = N_BOOTSTRAP) -> tuple[float, float]:
    rng = random.Random(semente)
    n = len(a)
    return percentis([cohen_kappa([a[i] for i in idx], [b[i] for i in idx]) for idx in ([rng.randrange(n) for _ in range(n)] for _ in range(b_rep))])


def ic_taxa_blocos(valores: list[int], blocos: list[str], semente: int = SEMENTE_BOOTSTRAP, b_rep: int = N_BOOTSTRAP) -> tuple[float, float]:
    """Bootstrap por blocos: reamostra blocos com reposição e calcula a taxa sobre todas as imagens dos blocos sorteados."""
    por_bloco: dict[str, list[int]] = {}
    for v, b in zip(valores, blocos):
        por_bloco.setdefault(b, []).append(v)
    chaves = sorted(por_bloco)
    rng = random.Random(semente)
    taxas = []
    for _ in range(b_rep):
        vs = [x for k in (chaves[rng.randrange(len(chaves))] for _ in chaves) for x in por_bloco[k]]
        taxas.append(sum(vs) / len(vs))
    return percentis(taxas)


# ----------------------------------------------------------------------------- leitura
def ler_avaliacao(caminho: Path) -> dict[str, dict]:
    """{codigo: {caixas: {item: categoria}, adicionado, obs_adicionado, orig_sem_rotulo}}; exige o preenchimento completo e válido."""
    av: dict[str, dict] = {}
    for r in csv.DictReader(open(caminho, encoding="utf-8", newline="")):
        d = av.setdefault(r["codigo"], {"caixas": {}, "adicionado": None, "obs_adicionado": "", "orig_sem_rotulo": None})
        v = str(r.get("categoria") or "").strip().lower()
        if v.endswith(".0"):
            v = v[:-2]
        if r["tipo"] == "caixa":
            if v not in CATEGORIAS:
                raise ValueError(f"{caminho.name}: categoria inválida ou vazia {v!r} em {r['codigo']} caixa {r['item']}")
            d["caixas"][int(r["item"])] = v
        else:
            if v not in {"0", "1"}:
                raise ValueError(f"{caminho.name}: {r['tipo']} deve ser 0 ou 1 em {r['codigo']} (veio {v!r})")
            if r["tipo"] == "imagem":
                d["adicionado"], d["obs_adicionado"] = int(v), str(r.get("observacao") or "")
            else:
                d["orig_sem_rotulo"] = int(v)
    incompletos = [c for c, d in av.items() if d["adicionado"] is None or d["orig_sem_rotulo"] is None]
    if incompletos:
        raise ValueError(f"{caminho.name}: linhas imagem/original ausentes em {incompletos[:5]}")
    return av


def adicao_nao_embarcacao(obs: str) -> bool:
    """Observação que nomeia só objeto que não é embarcação (secundário na seção 5). Sem tipo ou mencionando embarcação = embarcação."""
    t = sem_acento(obs)
    return bool(NAO_EMBARCACAO.search(t)) and not EMBARCACAO.search(t)


def reprovada(d: dict, modo: str = "embarcacao") -> bool:
    if any(c in INVALIDAS for c in d["caixas"].values()):
        return True
    if d["adicionado"] == 1:
        return True if modo == "qualquer" else not adicao_nao_embarcacao(d["obs_adicionado"])
    return False


def ler_mapas(chave: Path, amostra: Path) -> dict[str, dict]:
    am = {r["nome"]: r for r in csv.DictReader(open(amostra, encoding="utf-8", newline=""))}
    mapa = {}
    for r in csv.DictReader(open(chave, encoding="utf-8", newline="")):
        nome = Path(r["imagem"]).stem
        if nome not in am:
            raise ValueError(f"{nome} da chave não está na amostra sorteada")
        mapa[r["codigo"]] = {"nome": nome, "bloco": am[nome]["bloco"], "estrato": am[nome]["estrato"]}
    return mapa


# ----------------------------------------------------------------------------- métricas
def taxa(x: int, n: int) -> dict:
    lo, hi = wilson(x, n)
    return {"k": x, "n": n, "taxa": x / n if n else float("nan"), "wilson": [lo, hi]}


def metricas_filtro(flags: dict[str, bool], ref: dict[str, bool]) -> dict:
    cods = sorted(ref)
    tp = sum(flags[c] and ref[c] for c in cods)
    fn = sum((not flags[c]) and ref[c] for c in cods)
    tn = sum((not flags[c]) and (not ref[c]) for c in cods)
    fp = sum(flags[c] and (not ref[c]) for c in cods)
    return {"n": len(cods), "positivos": tp + fn, "tp": tp, "fn": fn, "tn": tn, "fp": fp,
            "sensibilidade": taxa(tp, tp + fn), "especificidade": taxa(tn, tn + fp),
            "taxa_descarte": taxa(tp + fp, len(cods)), "taxa_residual": taxa(fn, fn + tn)}


def regra_uso_E(m: dict) -> dict:
    s, r = m["sensibilidade"]["taxa"], m["taxa_residual"]["taxa"]
    return {"sensibilidade_ok": bool(s >= LIMIAR_SENSIBILIDADE), "residual_ok": bool(r <= LIMIAR_RESIDUAL),
            "E_pode_treinar": bool(s >= LIMIAR_SENSIBILIDADE and r <= LIMIAR_RESIDUAL),
            "sensibilidade": s, "taxa_residual": r, "limiares": {"sensibilidade": LIMIAR_SENSIBILIDADE, "taxa_residual": LIMIAR_RESIDUAL}}


def analisar(csv_a: Path, csv_b: Path, chave: Path, amostra: Path = AMOSTRA, filtro: Path | None = None,
             nomes: tuple[str, str] = ("A", "B")) -> dict:
    A, B = ler_avaliacao(Path(csv_a)), ler_avaliacao(Path(csv_b))
    mapa = ler_mapas(Path(chave), Path(amostra))
    if set(A) != set(mapa) or set(B) != set(mapa):
        raise ValueError(f"códigos diferentes: A {len(A)}, B {len(B)}, chave {len(mapa)}")
    for c in mapa:
        if set(A[c]["caixas"]) != set(B[c]["caixas"]):
            raise ValueError(f"{c}: as duas planilhas têm caixas diferentes")
    cods = sorted(mapa)
    blocos = [mapa[c]["bloco"] for c in cods]
    saida: dict = {"n": len(cods), "avaliadores": list(nomes), "semente_bootstrap": SEMENTE_BOOTSTRAP}
    for modo, rot in (("embarcacao", "secao5"), ("qualquer", "qualquer_objeto")):
        ra = [reprovada(A[c], modo) for c in cods]
        rb = [reprovada(B[c], modo) for c in cods]
        qualquer = [int(x or y) for x, y in zip(ra, rb)]
        ambos = [int(x and y) for x, y in zip(ra, rb)]
        est = {e: [q for q, c in zip(qualquer, cods) if mapa[c]["estrato"] == e] for e in sorted({m["estrato"] for m in mapa.values()})}
        saida[rot] = {
            "primaria_qualquer_avaliador": {**taxa(sum(qualquer), len(cods)), "ic_blocos": list(ic_taxa_blocos(qualquer, blocos))},
            "sensibilidade_ambos": {**taxa(sum(ambos), len(cods)), "ic_blocos": list(ic_taxa_blocos(ambos, blocos))},
            "por_avaliador": {nomes[0]: taxa(sum(ra), len(cods)), nomes[1]: taxa(sum(rb), len(cods))},
            "por_estrato_qualquer": {e: taxa(sum(v), len(v)) for e, v in est.items()},
            "kappa_imagem_reprovada": {"kappa": cohen_kappa(ra, rb), "ic_bootstrap": list(ic_kappa(ra, rb)),
                                       "atinge_limiar_0_60": bool(cohen_kappa(ra, rb) >= LIMIAR_KAPPA)},
        }
    # tipos de falha e ruído herdado
    saida["caixas"] = {}
    for nome, av in zip(nomes, (A, B)):
        cont = Counter(v for c in cods for v in av[c]["caixas"].values())
        saida["caixas"][nome] = {k: cont.get(k, 0) for k in CATEGORIAS}
    ca = [A[c]["caixas"][i] for c in cods for i in sorted(A[c]["caixas"])]
    cb = [B[c]["caixas"][i] for c in cods for i in sorted(B[c]["caixas"])]
    saida["kappa_caixa_6_categorias"] = {"kappa": cohen_kappa(ca, cb), "n_caixas": len(ca), "observacao": "caixas da mesma imagem não são independentes; descritivo"}
    saida["kappa_objeto_adicionado"] = cohen_kappa([A[c]["adicionado"] for c in cods], [B[c]["adicionado"] for c in cods])
    saida["kappa_original_sem_rotulo"] = cohen_kappa([A[c]["orig_sem_rotulo"] for c in cods], [B[c]["orig_sem_rotulo"] for c in cods])
    saida["imagens_com_adicao_nao_embarcacao"] = {nome: sum(av[c]["adicionado"] == 1 and adicao_nao_embarcacao(av[c]["obs_adicionado"]) for c in cods)
                                                 for nome, av in zip(nomes, (A, B))}
    saida["adicao_sem_tipo_na_observacao"] = {nome: sum(av[c]["adicionado"] == 1 and not (NAO_EMBARCACAO.search(sem_acento(av[c]["obs_adicionado"])) or EMBARCACAO.search(sem_acento(av[c]["obs_adicionado"]))) for c in cods)
                                              for nome, av in zip(nomes, (A, B))}
    saida["original_sem_rotulo_imagens"] = {nome: sum(av[c]["orig_sem_rotulo"] for c in cods) for nome, av in zip(nomes, (A, B))}
    # filtro
    if filtro is not None:
        flags_csv = {r["codigo"]: r for r in csv.DictReader(open(filtro, encoding="utf-8", newline=""))}
        if set(flags_csv) != set(cods):
            raise ValueError("o filtro não cobre exatamente as 150 folhas")
        flags = {c: bool(int(flags_csv[c]["sinalizada"])) for c in cods}
        saida["filtro"] = {"falhas_de_leitura": sum(int(r["falha_leitura"]) for r in flags_csv.values())}
        for modo, rot in (("embarcacao", "secao5"), ("qualquer", "qualquer_objeto")):
            ref = {c: reprovada(A[c], modo) or reprovada(B[c], modo) for c in cods}
            m = metricas_filtro(flags, ref)
            saida["filtro"][rot] = {**m, "regra_uso_E": regra_uso_E(m)}
        refc = {c: reprovada(A[c]) and reprovada(B[c]) for c in cods}
        saida["filtro"]["referencia_consenso_descritiva"] = metricas_filtro(flags, refc)
        saida["filtro"]["por_estrato_secao5"] = {
            e: metricas_filtro({c: flags[c] for c in cods if mapa[c]["estrato"] == e},
                               {c: reprovada(A[c]) or reprovada(B[c]) for c in cods if mapa[c]["estrato"] == e})
            for e in sorted({m["estrato"] for m in mapa.values()})}
    return saida


def texto(s: dict) -> str:
    f = lambda t: f"{t['k']}/{t['n']} = {t['taxa']:.1%} (Wilson {t['wilson'][0]:.1%} a {t['wilson'][1]:.1%})"
    L = [f"Imagens: {s['n']}  Avaliadores: {', '.join(s['avaliadores'])}"]
    for rot, tit in (("secao5", "DEFINIÇÃO DA SEÇÃO 5 (adição que seja embarcação)"), ("qualquer_objeto", "SENSIBILIDADE: qualquer objeto adicionado (como no piloto)")):
        d = s[rot]
        L += ["", tit, f"  Primária (qualquer avaliador): {f(d['primaria_qualquer_avaliador'])}  bootstrap blocos {d['primaria_qualquer_avaliador']['ic_blocos'][0]:.1%} a {d['primaria_qualquer_avaliador']['ic_blocos'][1]:.1%}",
              f"  Ambos os avaliadores:          {f(d['sensibilidade_ambos'])}"]
        for n, t in d["por_avaliador"].items():
            L.append(f"  {n}: {f(t)}")
        for e, t in d["por_estrato_qualquer"].items():
            L.append(f"  Estrato {e}: {f(t)}")
        k = d["kappa_imagem_reprovada"]
        L.append(f"  Kappa imagem reprovada: {k['kappa']:.2f} (IC95% {k['ic_bootstrap'][0]:.2f} a {k['ic_bootstrap'][1]:.2f}); limiar 0,60: {'atinge' if k['atinge_limiar_0_60'] else 'NÃO atinge'}")
    L += ["", f"Caixas por categoria: {json.dumps(s['caixas'], ensure_ascii=False)}",
          f"Kappa caixa (6 cat.): {s['kappa_caixa_6_categorias']['kappa']:.2f}; objeto adicionado: {s['kappa_objeto_adicionado']:.2f}; original sem rótulo: {s['kappa_original_sem_rotulo']:.2f}",
          f"Adição que não é embarcação: {s['imagens_com_adicao_nao_embarcacao']}; adição sem tipo na observação: {s['adicao_sem_tipo_na_observacao']}; originais sem rótulo: {s['original_sem_rotulo_imagens']}"]
    if "filtro" in s:
        for rot in ("secao5", "qualquer_objeto"):
            m = s["filtro"][rot]
            r = m["regra_uso_E"]
            L += ["", f"FILTRO ({rot}): positivos {m['positivos']}  sensibilidade {f(m['sensibilidade'])}", f"  especificidade {f(m['especificidade'])}",
                  f"  descarte {f(m['taxa_descarte'])}", f"  taxa residual {f(m['taxa_residual'])}",
                  f"  Regra seção 9: sensibilidade>=80% {'ok' if r['sensibilidade_ok'] else 'FALHA'}; residual<=7% {'ok' if r['residual_ok'] else 'FALHA'} -> E {'PODE' if r['E_pode_treinar'] else 'NÃO pode'} treinar"]
        L.append(f"Falhas de leitura do filtro: {s['filtro']['falhas_de_leitura']}")
    return "\n".join(L)


def principal(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv-a", required=True)
    ap.add_argument("--csv-b", required=True)
    ap.add_argument("--nomes", nargs=2, default=["Daniela", "Jose"])
    ap.add_argument("--chave", required=True)
    ap.add_argument("--amostra", default=str(AMOSTRA))
    ap.add_argument("--filtro")
    ap.add_argument("--saida", required=True)
    a = ap.parse_args(argv)
    if Path(a.saida).exists():
        print(f"{a.saida} já existe; recuso sobrescrever.", file=sys.stderr)
        return 2
    s = analisar(Path(a.csv_a), Path(a.csv_b), Path(a.chave), Path(a.amostra), Path(a.filtro) if a.filtro else None, tuple(a.nomes))
    Path(a.saida).write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print(texto(s))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
