"""Auditoria do piloto iflens com as definições v4: junta as respostas originais das 60 folhas com a reavaliação v4 de cada avaliador.

Para cada avaliador, a categoria de cada caixa é a da auditoria original, exceto nas 30 caixas reavaliadas (todas as que algum dos
dois marcou como diferente de `valida`), que passam a ter a categoria da reavaliação v4; idem para as imagens A024, A029 e A030.
Desfecho primário (D-adendo 4a): imagem reprovada se alguma caixa é apagada, deslocada ou alterada, ou se há embarcação adicionada.
Sensibilidade: `degradada` também conta como falha. Dois avaliadores: regra "qualquer um" (primária) e "ambos" (sensibilidade).
Uso: python -m scripts.analise_reavaliacao_v4 <pasta data/auditoria_piloto_iflens> <saida.json>
"""
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

INV = {"apagada", "deslocada", "alterada"}
PROMPTS = {"5437d06c": "v1", "e96659f9": "v2"}


def eh_embarcacao(tipo):
    t = (tipo or "").strip().lower()
    return "embarc" in t or t.startswith(("barco", "navio", "lancha"))


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    return po, ((po - pe) / (1 - pe) if pe < 1 else float("nan"))


def boot_kappa(cods, get, B=2000, semente=2026):
    rnd = random.Random(semente)
    ks = []
    for _ in range(B):
        a, b = [], []
        for c in [rnd.choice(cods) for _ in cods]:
            x, y = get(c)
            a += x
            b += y
        k = kappa(a, b)[1]
        if k == k:
            ks.append(k)
    ks.sort()
    return ks[int(0.025 * len(ks))], ks[int(0.975 * len(ks))]


def wilson(x, n, z=1.96):
    p = x / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return c - m, c + m


def mcnemar_exato(b, c):
    """p bilateral exato; b e c = pares discordantes."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def ler_csv_daniela(caminho):
    cx, im = {}, {}
    for r in csv.DictReader(open(caminho, encoding="utf-8")):
        if r["tipo"] == "caixa":
            cx[(r["codigo"], int(r["item"]))] = r["categoria"].strip()
        elif r["tipo"] == "imagem":
            im[r["codigo"]] = (r["classe"].strip(), r.get("tipo_objeto_adicionado", "").strip())
    return cx, im


def ler_xlsx_jose(caminho):
    import openpyxl
    cx, im = {}, {}
    for r in list(openpyxl.load_workbook(caminho, data_only=True).active.iter_rows(values_only=True))[1:]:
        c, t, i, cl, cat, _, tp = r
        if t == "caixa":
            cx[(c, int(i))] = (str(cat).strip() if cat else "")
        elif t == "imagem":
            im[c] = (str(int(cl)), (tp or "").strip())
    return cx, im


def reavaliacao(caminho_cx, caminho_im):
    cx = {(r["codigo"], int(r["caixa"])): r["categoria_v4"].strip() for r in csv.DictReader(open(caminho_cx, encoding="utf-8")) if r["codigo"]}
    im = {r["codigo"]: (r["objeto_adicionado_0_ou_1"].strip(), r["tipo_objeto_adicionado"].strip())
          for r in csv.DictReader(open(caminho_im, encoding="utf-8")) if r["codigo"]}
    return cx, im


def juntar(orig, reav):
    (ocx, oim), (rcx, rim) = orig, reav
    cx = dict(ocx)
    cx.update(rcx)
    im = dict(oim)
    im.update(rim)
    return cx, im


def reprovada(cx, im, codigo, contar_degradada=False):
    falhas = INV | ({"degradada"} if contar_degradada else set())
    caixa = any(v in falhas for (c, _), v in cx.items() if c == codigo)
    adic = im[codigo][0] == "1" and eh_embarcacao(im[codigo][1])
    return caixa or adic


def principal(pasta, saida):
    d = Path(pasta)
    chave = {r["codigo"]: r for r in csv.DictReader(open(d / "chave_cega.csv", encoding="utf-8"))}
    prompt = {c: PROMPTS[chave[c]["base_prompt_sha256"][:8]] for c in chave}
    cods = sorted(chave)
    D0 = ler_csv_daniela(d / "auditoria_daniela_v3_com_tipo.csv")
    J0 = ler_xlsx_jose(d / "auditoria_jose_com_tipo.xlsx")
    Dr = reavaliacao(d / "reavaliacao_v4_daniela_caixas_corrigida.csv", d / "reavaliacao_v4_daniela_imagens.csv")
    Jr = reavaliacao(d / "reavaliacao_v4_jose_caixas.csv", d / "reavaliacao_v4_jose_imagens.csv")
    D, J = juntar(D0, Dr), juntar(J0, Jr)
    # conferência: toda caixa não reavaliada é `valida` nos dois?
    fora = {k for k in D[0] if k not in Dr[0]}
    nao_valida_fora = [(k, D[0][k], J[0].get(k)) for k in sorted(fora) if D[0][k] != "valida" or J[0].get(k) != "valida"]
    saida_json = {"conferencia": {"n_caixas": len(D[0]), "n_caixas_iguais_nas_duas_planilhas": len(set(D[0]) & set(J[0])),
                                   "n_reavaliadas": len(Dr[0]), "caixas_nao_reavaliadas_com_marca_diferente_de_valida": nao_valida_fora,
                                   "tipos_objeto_adicionado": {"daniela": sorted({v[1] for v in D[1].values() if v[0] == "1"}),
                                                               "jose": sorted({v[1] for v in J[1].values() if v[0] == "1"})}}}
    # concordância nas 30 caixas reavaliadas
    ks = sorted(Dr[0])
    a, b = [Dr[0][k] for k in ks], [Jr[0][k] for k in ks]
    fb = lambda v: "falha" if v in INV else ("degradada" if v == "degradada" else ("nao_avaliavel" if v == "nao_avaliavel" else "valida"))
    po6, k6 = kappa(a, b)
    po4, k4 = kappa([fb(v) for v in a], [fb(v) for v in b])
    saida_json["nas_30_caixas_reavaliadas"] = {
        "concordancia_6_categorias": po6, "kappa_6_categorias": k6, "concordancia_4_grupos": po4, "kappa_4_grupos": k4,
        "matriz_daniela_jose": {f"{x}|{y}": n for (x, y), n in sorted(Counter(zip(a, b)).items())},
        "divergencias": [(f"{c}#{i}", Dr[0][(c, i)], Jr[0][(c, i)]) for (c, i) in ks if Dr[0][(c, i)] != Jr[0][(c, i)]]}
    # concordância sobre todas as caixas das 60 folhas
    todas = sorted(set(D[0]) & set(J[0]))
    por_folha = defaultdict(list)
    for k in todas:
        por_folha[k[0]].append(k)
    get6 = lambda c: ([D[0][k] for k in por_folha[c]], [J[0][k] for k in por_folha[c]])
    get3 = lambda c: ([fb(D[0][k]) for k in por_folha[c]], [fb(J[0][k]) for k in por_folha[c]])
    A6 = [D[0][k] for k in todas]; B6 = [J[0][k] for k in todas]
    saida_json["todas_as_caixas_60_folhas"] = {
        "n": len(todas), "concordancia_6": kappa(A6, B6)[0], "kappa_6": kappa(A6, B6)[1], "ic95_kappa_6": boot_kappa(cods, get6),
        "kappa_4_grupos": kappa([fb(v) for v in A6], [fb(v) for v in B6])[1], "ic95_kappa_4_grupos": boot_kappa(cods, get3),
        "referencia_antes_da_v4": {"kappa_6": 0.27, "kappa_3_grupos": 0.35}}
    # desfecho por imagem
    res = {}
    for nome, deg in (("primario", False), ("sensibilidade_degradada_conta", True)):
        fD = {c: reprovada(*D, c, deg) for c in cods}
        fJ = {c: reprovada(*J, c, deg) for c in cods}
        regra = {"qualquer_um": {c: fD[c] or fJ[c] for c in cods}, "ambos": {c: fD[c] and fJ[c] for c in cods},
                 "daniela": fD, "jose": fJ}
        bloco = {"kappa_entre_avaliadores_imagem_reprovada": kappa([int(fD[c]) for c in cods], [int(fJ[c]) for c in cods]),
                 "ic95_kappa": boot_kappa(cods, lambda c: ([int(fD[c])], [int(fJ[c])]))}
        for rn, f in regra.items():
            por_p = {}
            for p in ("v1", "v2"):
                cs = [c for c in cods if prompt[c] == p]
                x = sum(f[c] for c in cs)
                por_p[p] = {"reprovadas": x, "n": len(cs), "wilson95": wilson(x, len(cs))}
            pares = defaultdict(dict)
            for c in cods:
                pares[chave[c]["imagem"]][prompt[c]] = f[c]
            pc = Counter((v["v1"], v["v2"]) for v in pares.values())
            por_p["pareado_v1_v2"] = {"nenhuma": pc[(False, False)], "ambas": pc[(True, True)], "so_v2": pc[(False, True)],
                                     "so_v1": pc[(True, False)], "mcnemar_exato_p": mcnemar_exato(pc[(False, True)], pc[(True, False)])}
            bloco[rn] = por_p
        res[nome] = bloco
    saida_json["desfecho_por_imagem"] = res
    json.dump(saida_json, open(saida, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=lambda o: list(o))
    print(json.dumps(saida_json, ensure_ascii=False, indent=2, default=lambda o: list(o)))


if __name__ == "__main__":
    principal(sys.argv[1], sys.argv[2])
