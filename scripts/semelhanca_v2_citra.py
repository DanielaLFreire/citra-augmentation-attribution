"""Passo 2 da medida de semelhança v2 (D25): limiar por regra objetiva e semelhança teste/validação contra treino.

Lê o .npz de embeddings (scripts/embeddings_citra.py), NÃO precisa das imagens. Faz, sem alterar nenhuma divisão:
1. Pares positivos: quadros reais do mesmo dia com diferença de tempo <= 60 s (todas as divisões juntas).
   Limiar tau = percentil 5 do cosseno (CLS) desses pares; sensibilidade: percentis 1 e 10 (regra da D25).
   Imprime quantos pares há, por tipo de divisão, e AVISA se forem menos de 100 (percentil instável): nesse caso
   a regra da D25 precisa ser revista com Daniela antes de seguir.
2. Para cada quadro de val/test: maior semelhança com o treino, qual quadro, se é do mesmo dia, diferença de tempo.
3. Fração de val/test com semelhança >= tau (e >= percentis 1 e 10).
Saídas: semelhanca_v2_por_quadro.csv e semelhanca_v2_resumo.json (com hash do .npz e commit do repositório).
Uso: python -m scripts.semelhanca_v2_citra analise <embeddings.npz> <pasta_saida>
     python -m scripts.semelhanca_v2_citra distribuicao <embeddings.npz>   (D26: histograma dos pares positivos e limiar de Otsu)
"""
import csv
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

LIMITE_S = 60
MIN_PARES = 100
PERCENTIS = {"p5": 5, "p1": 1, "p10": 10}


def tempo(nome):
    """Segundos desde a época para um nome dd.mm.aaaa-hh-mm-ss (hora local, sem fuso: só diferenças importam)."""
    d, m, resto = nome.split(".", 2)
    a, h = resto.split("-", 1)
    hh, mm, ss = h.split("-")
    return datetime.datetime(int(a), int(m), int(d), int(hh), int(mm), int(ss)).timestamp()


def dia(nome):
    return nome[:10]


def pares_positivos(nomes, limite_s=LIMITE_S):
    """Índices (i, j), i < j, de quadros do mesmo dia com |diferença de tempo| <= limite_s."""
    t = np.array([tempo(n) for n in nomes])
    d = np.array([dia(n) for n in nomes])
    m = (d[:, None] == d[None, :]) & (np.abs(t[:, None] - t[None, :]) <= limite_s)
    return np.argwhere(np.triu(m, k=1))


def limiares(sims):
    return {k: float(np.percentile(sims, p)) for k, p in PERCENTIS.items()}


def normalizar_resposta(valor):
    """Minúsculas, sem espaços nas pontas e 'não' (com acento) tratado como 'nao'; não altera o arquivo de origem."""
    v = (valor or "").strip().lower()
    return "nao" if v == "não" else v


def aplicar_divisao(split, nomes, csv_divisao):
    """Substitui a divisão do .npz (a antiga) pela de um CSV nome,dia,divisao (ex.: blocos de dias, D31). Exige os mesmos nomes."""
    mapa = {r["nome"]: r["divisao"] for r in csv.DictReader(open(csv_divisao, encoding="utf-8"))}
    if set(mapa) != set(nomes):
        raise ValueError("os nomes do CSV de divisão não coincidem com os do .npz")
    return np.array([mapa[n] for n in nomes])


def wilson(x, n, z=1.96):
    """Intervalo de Wilson para uma proporção."""
    p = x / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    meia = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return float(centro - meia), float(centro + meia)


def newcombe(x1, n1, x2, n2, z=1.96):
    """Intervalo de Newcombe (método 10) para a diferença de duas proporções independentes p1 - p2."""
    p1, p2 = x1 / n1, x2 / n2
    l1, u1 = wilson(x1, n1, z)
    l2, u2 = wilson(x2, n2, z)
    d = p1 - p2
    return float(d - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)), float(d + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def vazamento_residual(chave_csv, folha_csv, antigo_x=26, antigo_n=40):
    """Proporção de pares com as mesmas embarcações (sim ou mesmo_alvo) na divisão nova, com Wilson 95%, e diferença para a antiga (D29)."""
    ch = {r["codigo"]: r for r in csv.DictReader(open(chave_csv, encoding="utf-8"))}
    resp = {r["codigo"]: normalizar_resposta(r["resposta_sim_cena_nao"]) for r in csv.DictReader(open(folha_csv, encoding="utf-8"))}
    cod = sorted(ch)
    validas = ("sim", "mesmo_alvo", "cena", "nao")
    faltam = [c for c in cod if resp.get(c) not in validas]
    if faltam:
        sys.exit(f"respostas ausentes ou inválidas (use sim, mesmo_alvo, cena ou nao): {faltam}")
    r = [resp[c] for c in cod]
    x = sum(1 for a in r if a in ("sim", "mesmo_alvo"))
    n = len(r)
    por_estrato = {}
    for c in cod:
        por_estrato.setdefault(int(ch[c]["estrato_octil"]), []).append(resp[c])
    saida = {"n_pares": n, "respostas_totais": {k: r.count(k) for k in validas},
             "mesmas_embarcacoes_nova": {"x": x, "n": n, "proporcao": x / n, "wilson95": wilson(x, n)},
             "mesmas_embarcacoes_antiga": {"x": antigo_x, "n": antigo_n, "proporcao": antigo_x / antigo_n, "wilson95": wilson(antigo_x, antigo_n)},
             "diferenca_nova_menos_antiga": {"valor": x / n - antigo_x / antigo_n, "newcombe95": newcombe(x, n, antigo_x, antigo_n)},
             "mesmo_dia_entre_pares": sum(1 for c in cod if ch[c]["nome_esq"][:10] == ch[c]["nome_dir_treino"][:10]),
             "respostas_por_estrato": {str(e): {k: v.count(k) for k in validas} for e, v in sorted(por_estrato.items())},
             "faixa_cosseno_por_estrato": {str(e): [min(float(ch[c]["cosseno_cls"]) for c in cod if int(ch[c]["estrato_octil"]) == e),
                                                   max(float(ch[c]["cosseno_cls"]) for c in cod if int(ch[c]["estrato_octil"]) == e)]
                                           for e in sorted(por_estrato)}}
    print(json.dumps(saida, ensure_ascii=False, indent=2))


def otsu(valores, n_bins=100):
    """Limiar de Otsu (máxima variância entre classes) de valores 1-D; regra objetiva, sem parâmetros livres além de n_bins."""
    v = np.asarray(valores, float)
    cont, bordas = np.histogram(v, bins=n_bins)
    centros = (bordas[:-1] + bordas[1:]) / 2
    p = cont / cont.sum()
    w0 = np.cumsum(p)
    m = np.cumsum(p * centros)
    mt = m[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        var = (mt * w0 - m) ** 2 / (w0 * (1 - w0))
    return float(centros[np.nanargmax(var)])


def distribuicao(npz):
    """Descreve a distribuição do cosseno nos pares positivos (mesmo dia, <= 60 s) e o limiar de Otsu (D26)."""
    d = np.load(npz)
    split, nomes = d["split"].astype(str), d["nome"].astype(str)
    z = d["cls"].astype(np.float32)
    z /= np.linalg.norm(z, axis=1, keepdims=True)
    s = z @ z.T
    par = pares_positivos(nomes)
    v = s[par[:, 0], par[:, 1]]
    tr = np.where(split == "train")[0]
    t_otsu = otsu(v)
    cont, bordas = np.histogram(v, bins=20, range=(0.0, 1.0))
    saida = {
        "n_pares_positivos": int(len(v)),
        "percentis_cosseno_pares_positivos": {str(q): float(np.percentile(v, q)) for q in (1, 5, 10, 25, 50, 75, 90, 95, 99)},
        "histograma_20_faixas_de_0_a_1": {f"{bordas[i]:.2f}-{bordas[i + 1]:.2f}": int(cont[i]) for i in range(20)},
        "limiar_otsu": t_otsu,
        "fracao_pares_positivos_acima_otsu": float(np.mean(v >= t_otsu)),
        "fracao_acima_otsu_por_split": {
            sp: float(np.mean([s[i, tr].max() >= t_otsu for i in np.where(split == sp)[0]])) for sp in ("val", "test")},
    }
    print(json.dumps(saida, ensure_ascii=False, indent=2))


def amostrar_pares(sims, n_estratos=8, por_estrato=5, semente=2026):
    """Estratos = faixas de igual tamanho (quantis) da semelhança; sorteia por_estrato pares em cada. Devolve (índice, estrato)."""
    sims = np.asarray(sims, float)
    ordem = np.argsort(sims)
    rng = np.random.default_rng(semente)
    saida = []
    for e, bloco in enumerate(np.array_split(ordem, n_estratos)):
        for i in rng.choice(bloco, por_estrato, replace=False):
            saida.append((int(i), e))
    return saida


def tau_de_rotulos(sims, rotulos, precisao=0.9, min_pares=5):
    """Menor valor s tal que, entre os pares com semelhança >= s, a fração rotulada 'sim' é >= precisao (com >= min_pares pares).
    Devolve None se nenhum valor satisfaz (a semelhança CLS não define quase-cópia neste conjunto)."""
    sims = np.asarray(sims, float)
    sim = np.array([r == "sim" for r in rotulos])
    melhor = None
    for v in sorted(set(sims.tolist()), reverse=True):
        m = sims >= v
        if m.sum() >= min_pares and sim[m].mean() >= precisao:
            melhor = v
    return melhor


def pares(npz, zip_imagens, pasta_saida, semente=2026, csv_divisao=None):
    """Gera os 40 pares da calibração humana (D27): imagens lado a lado SEM pontuação, folha em branco e chave separada."""
    import io
    import zipfile

    import cv2

    from scripts.embeddings_citra import INTERNOS, nomes_reais

    d = np.load(npz)
    split, nomes = d["split"].astype(str), d["nome"].astype(str)
    if csv_divisao:
        split = aplicar_divisao(split, nomes, csv_divisao)
    z = d["cls"].astype(np.float32)
    z /= np.linalg.norm(z, axis=1, keepdims=True)
    s = z @ z.T
    tr = np.where(split == "train")[0]
    cand = np.array([i for i in range(len(nomes)) if split[i] in ("val", "test")])
    viz = np.array([tr[np.argmax(s[i, tr])] for i in cand])
    sims = np.array([s[i, j] for i, j in zip(cand, viz)])
    escolhidos = amostrar_pares(sims, semente=semente)
    rng = np.random.default_rng(semente + 1)
    ordem = rng.permutation(len(escolhidos))
    pasta = Path(pasta_saida)
    (pasta / "pares_conferencia").mkdir(parents=True, exist_ok=True)
    (pasta / "_NAO_ABRIR_chave").mkdir(parents=True, exist_ok=True)
    ext = zipfile.ZipFile(zip_imagens)
    acervo = {}
    for sp in ("train", "val", "test"):
        with ext.open(INTERNOS[sp]) as f:
            zz = zipfile.ZipFile(io.BytesIO(f.read()))
        acervo[sp] = (zz, {b: c for c, b in nomes_reais(zz.namelist())})

    original = dict(zip(nomes, d["split"].astype(str)))

    def ler(nome, sp):
        zz, idx = acervo[original[nome]]
        im = cv2.imdecode(np.frombuffer(zz.read(idx[nome]), np.uint8), cv2.IMREAD_COLOR)
        return cv2.resize(im, (960, 531), interpolation=cv2.INTER_AREA)

    chave = []
    for k, pos in enumerate(ordem, start=1):
        idx, estrato = escolhidos[pos]
        i, j = cand[idx], viz[idx]
        codigo = f"P{k:02d}"
        cv2.imwrite(str(pasta / "pares_conferencia" / f"{codigo}.jpg"),
                    np.hstack([ler(nomes[i], split[i]), ler(nomes[j], split[j])]), [cv2.IMWRITE_JPEG_QUALITY, 92])
        chave.append({"codigo": codigo, "split_esq": split[i], "nome_esq": nomes[i], "nome_dir_treino": nomes[j],
                      "cosseno_cls": float(sims[idx]), "estrato_octil": estrato})
    with open(pasta / "_NAO_ABRIR_chave" / "chave_pares.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(chave[0]))
        w.writeheader()
        w.writerows(chave)
    with open(pasta / "folha_resposta_pares.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["codigo", "resposta_sim_cena_nao", "observacao"])
        w.writerows([[c["codigo"], "", ""] for c in chave])
    print(f"{len(chave)} pares gerados em {pasta}/pares_conferencia; folha em branco: folha_resposta_pares.csv")


def calibrar(chave_csv, folha_csv):
    """Aplica a regra da D27/D28 às respostas de Daniela. Respostas: sim, mesmo_alvo, cena, nao.
    tau_objeto (principal) conta sim + mesmo_alvo (mesmas embarcações); tau_estrito só sim; tau_fundo conta também cena."""
    ch = {r["codigo"]: r for r in csv.DictReader(open(chave_csv, encoding="utf-8"))}
    resp = {r["codigo"]: normalizar_resposta(r["resposta_sim_cena_nao"]) for r in csv.DictReader(open(folha_csv, encoding="utf-8"))}
    cod = sorted(ch)
    validas = ("sim", "mesmo_alvo", "cena", "nao")
    faltam = [c for c in cod if resp.get(c) not in validas]
    if faltam:
        sys.exit(f"respostas ausentes ou inválidas (use sim, mesmo_alvo, cena ou nao): {faltam}")
    sims = [float(ch[c]["cosseno_cls"]) for c in cod]
    r = [resp[c] for c in cod]

    def binario(aceitas):
        return ["sim" if x in aceitas else "nao" for x in r]

    por_estrato = {}
    for c in cod:
        por_estrato.setdefault(int(ch[c]["estrato_octil"]), []).append(resp[c])
    saida = {"n_pares": len(cod),
             "tau_objeto_principal": tau_de_rotulos(sims, binario(("sim", "mesmo_alvo"))),
             "tau_estrito_so_sim": tau_de_rotulos(sims, binario(("sim",))),
             "tau_fundo_sim_mesmo_alvo_cena": tau_de_rotulos(sims, binario(("sim", "mesmo_alvo", "cena"))),
             "respostas_totais": {k: r.count(k) for k in validas},
             "respostas_por_estrato": {str(e): {k: v.count(k) for k in validas} for e, v in sorted(por_estrato.items())},
             "faixa_cosseno_por_estrato": {str(e): [min(float(ch[c]["cosseno_cls"]) for c in cod if int(ch[c]["estrato_octil"]) == e),
                                                   max(float(ch[c]["cosseno_cls"]) for c in cod if int(ch[c]["estrato_octil"]) == e)]
                                           for e in sorted(por_estrato)}}
    print(json.dumps(saida, ensure_ascii=False, indent=2))

def fracoes(por_quadro_csv, *taus):
    """Quantos quadros de val/test têm a maior semelhança com o treino >= cada tau (os que ficam fora do subconjunto 'sem quase-cópias')."""
    linhas = list(csv.DictReader(open(por_quadro_csv, encoding="utf-8")))
    saida = {}
    for sp in ("val", "test"):
        v = np.array([float(l["max_sim_treino"]) for l in linhas if l["split"] == sp])
        saida[sp] = {"n": int(len(v)), **{f"tau_{t:.4f}": {"acima": int((v >= t).sum()), "abaixo_ficam_no_subconjunto": int((v < t).sum()),
                                                            "fracao_acima": float((v >= t).mean())} for t in taus}}
    print(json.dumps(saida, ensure_ascii=False, indent=2))


def _sha256(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _commit():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def analisar(npz, pasta_saida, csv_divisao=None):
    d = np.load(npz)
    split, nomes = d["split"].astype(str), d["nome"].astype(str)
    if csv_divisao:
        split = aplicar_divisao(split, nomes, csv_divisao)
    z = d["cls"].astype(np.float32)
    z /= np.linalg.norm(z, axis=1, keepdims=True)
    s = z @ z.T
    par = pares_positivos(nomes)
    tipos = {}
    for i, j in par:
        k = "-".join(sorted((split[i], split[j])))
        tipos[k] = tipos.get(k, 0) + 1
    tau = limiares(s[par[:, 0], par[:, 1]]) if len(par) else {}
    aviso = None
    if len(par) < MIN_PARES:
        aviso = f"apenas {len(par)} pares positivos (< {MIN_PARES}): percentil instável; rever a regra da D25 com Daniela antes de usar"
    tr = np.where(split == "train")[0]
    t_all = np.array([tempo(n) for n in nomes])
    linhas = []
    for sp in ("val", "test"):
        for i in np.where(split == sp)[0]:
            j = tr[np.argmax(s[i, tr])]
            mesmo = dia(nomes[i]) == dia(nomes[j])
            linhas.append({
                "split": sp, "nome": nomes[i], "max_sim_treino": float(s[i, j]), "vizinho_treino": nomes[j],
                "mesmo_dia": mesmo, "delta_t_s": abs(t_all[i] - t_all[j]) if mesmo else "",
                **{f"acima_{k}": bool(s[i, j] >= v) for k, v in tau.items()},
            })
    Path(pasta_saida).mkdir(parents=True, exist_ok=True)
    with open(Path(pasta_saida) / "semelhanca_v2_por_quadro.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    resumo = {"npz_sha256": _sha256(npz), "repositorio_commit": _commit(), "limite_tempo_s": LIMITE_S,
              "n_imagens": int(len(nomes)), "n_pares_positivos": int(len(par)), "n_pares_por_tipo": tipos,
              "limiares": tau, "aviso": aviso, "por_split": {}}
    for sp in ("val", "test"):
        x = [l for l in linhas if l["split"] == sp]
        v = np.array([l["max_sim_treino"] for l in x])
        resumo["por_split"][sp] = {
            "n": len(x),
            "quantis_max_sim": {q: float(np.percentile(v, q)) for q in (5, 25, 50, 75, 95)},
            "fracao_acima": {k: float(np.mean([l[f"acima_{k}"] for l in x])) for k in tau},
            "fracao_vizinho_mesmo_dia_entre_acima_p5": (
                float(np.mean([l["mesmo_dia"] for l in x if l.get("acima_p5")])) if any(l.get("acima_p5") for l in x) else None),
        }
    with open(Path(pasta_saida) / "semelhanca_v2_resumo.json", "w", encoding="utf-8") as f:
        json.dump(resumo, f, ensure_ascii=False, indent=2)
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) in (4, 5) and sys.argv[1] == "analise":
        analisar(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) == 5 else None)
    elif len(sys.argv) == 3 and sys.argv[1] == "distribuicao":
        distribuicao(sys.argv[2])
    elif len(sys.argv) in (5, 7) and sys.argv[1] == "pares":
        if len(sys.argv) == 7:
            pares(sys.argv[2], sys.argv[3], sys.argv[4], semente=int(sys.argv[5]), csv_divisao=sys.argv[6])
        else:
            pares(sys.argv[2], sys.argv[3], sys.argv[4])
    elif len(sys.argv) == 4 and sys.argv[1] == "residual":
        vazamento_residual(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 4 and sys.argv[1] == "calibrar":
        calibrar(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 4 and sys.argv[1] == "fracoes":
        fracoes(sys.argv[2], *[float(x) for x in sys.argv[3:]])
    else:
        sys.exit("uso: python -m scripts.semelhanca_v2_citra analise <npz> <saida> | distribuicao <npz> | pares <npz> <CITRA-3D.zip> <saida> [<semente> <divisao.csv>] | residual <chave.csv> <folha.csv> | calibrar <chave.csv> <folha.csv> | fracoes <por_quadro.csv> <tau> [tau ...]")
