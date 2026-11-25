import csv

import pytest

from scripts import analisar_4a as an

AMOSTRA = an.AMOSTRA


def nomes_amostra():
    return [(r["nome"], r["estrato"]) for r in csv.DictReader(open(AMOSTRA, encoding="utf-8"))]


def escrever(tmp_path, reprov_a, reprov_b, adic_b=None, obs_b=None, flags=None):
    """150 folhas, 1 caixa cada. Daniela e José marcam 'apagada' conforme as listas; opcionalmente José marca adição."""
    nomes = nomes_amostra()
    cods = [f"A{i + 1:03d}" for i in range(len(nomes))]
    with open(tmp_path / "chave.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["codigo", "imagem"])
        for c, (n, _) in zip(cods, nomes):
            w.writerow([c, n + ".png"])
    for arq, rep in (("a.csv", reprov_a), ("b.csv", reprov_b)):
        with open(tmp_path / arq, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["codigo", "tipo", "item", "classe", "categoria", "observacao"])
            for i, c in enumerate(cods):
                w.writerow([c, "caixa", 1, 0, "apagada" if i in rep else "valida", ""])
                ad = adic_b is not None and arq == "b.csv" and i in adic_b
                w.writerow([c, "imagem", 0, "", 1 if ad else 0, (obs_b or {}).get(i, "") if ad else ""])
                w.writerow([c, "original", 0, "", 0, ""])
    if flags is not None:
        with open(tmp_path / "f.csv", "w", newline="") as f:
            w = csv.writer(f); w.writerow(["codigo", "sinalizada", "falha_leitura"])
            for i, c in enumerate(cods):
                w.writerow([c, int(i in flags), 0])
    return tmp_path


def test_kappa_conhecido():
    assert an.cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0]) == pytest.approx(0.5)
    assert an.cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == pytest.approx(1.0)


def test_adicao_nao_embarcacao():
    assert an.adicao_nao_embarcacao("uma boia laranja")
    assert an.adicao_nao_embarcacao("Gaivota")
    assert not an.adicao_nao_embarcacao("barco novo")
    assert not an.adicao_nao_embarcacao("")
    assert not an.adicao_nao_embarcacao("boia e uma lancha")


def test_analise_completa(tmp_path):
    p = escrever(tmp_path, reprov_a=set(range(0, 10)), reprov_b=set(range(5, 17)), flags=set(range(0, 15)) | {100})
    s = an.analisar(p / "a.csv", p / "b.csv", p / "chave.csv", filtro=p / "f.csv", nomes=("D", "J"))
    prim = s["secao5"]["primaria_qualquer_avaliador"]
    assert (prim["k"], prim["n"]) == (17, 150)                      # 0..16
    assert s["secao5"]["sensibilidade_ambos"]["k"] == 5              # 5..9
    m = s["filtro"]["secao5"]
    assert (m["tp"], m["fn"], m["fp"], m["tn"]) == (15, 2, 1, 132)   # sinalizadas 0..14 e 100; positivos 0..16
    assert m["taxa_residual"]["k"] == 2 and m["taxa_residual"]["n"] == 134
    assert m["regra_uso_E"]["sensibilidade_ok"] is True and m["regra_uso_E"]["E_pode_treinar"] is True
    est = s["secao5"]["por_estrato_qualquer"]
    assert sum(v["n"] for v in est.values()) == 150
    assert "Primária" in an.texto(s)


def test_regra_residual_falha(tmp_path):
    p = escrever(tmp_path, reprov_a=set(range(0, 20)), reprov_b=set(range(0, 20)), flags=set(range(0, 15)))
    m = an.analisar(p / "a.csv", p / "b.csv", p / "chave.csv", filtro=p / "f.csv")["filtro"]["secao5"]
    assert m["regra_uso_E"]["sensibilidade_ok"] is False and m["regra_uso_E"]["E_pode_treinar"] is False


def test_adicao_por_tipo(tmp_path):
    p = escrever(tmp_path, reprov_a=set(), reprov_b=set(), adic_b={1, 2, 3}, obs_b={1: "boia", 2: "barco", 3: ""})
    s = an.analisar(p / "a.csv", p / "b.csv", p / "chave.csv")
    assert s["secao5"]["primaria_qualquer_avaliador"]["k"] == 2          # a boia fica de fora
    assert s["qualquer_objeto"]["primaria_qualquer_avaliador"]["k"] == 3
    assert s["imagens_com_adicao_nao_embarcacao"]["A"] == 0 and s["imagens_com_adicao_nao_embarcacao"]["B"] == 1
    assert s["adicao_sem_tipo_na_observacao"]["B"] == 1


def test_csv_incompleto_recusa(tmp_path):
    p = escrever(tmp_path, set(), set())
    linhas = list(csv.reader(open(p / "a.csv")))
    linhas[1][4] = ""
    csv.writer(open(p / "a.csv", "w", newline="")).writerows(linhas)
    with pytest.raises(ValueError):
        an.analisar(p / "a.csv", p / "b.csv", p / "chave.csv")
