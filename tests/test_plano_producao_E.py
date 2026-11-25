import csv

from scripts import plano_producao_E as pl


def nomes(n=1370):
    return [f"img{i:04d}" for i in range(n)]


def test_plano_basico():
    p = pl.montar_plano(nomes())
    assert len(p) == 2740
    for passagem in (1, 2):
        q = [r for r in p if r["passagem"] == passagem]
        assert len({r["nome"] for r in q}) == 1370
        assert sum(r["estrato"] == "risco" for r in q) == 274
    # mesma ordem nas duas passagens; estratos e sementes diferem
    o1 = [r["nome"] for r in p if r["passagem"] == 1]
    o2 = [r["nome"] for r in p if r["passagem"] == 2]
    assert o1 == o2
    assert [r["estrato"] for r in p if r["passagem"] == 1] != [r["estrato"] for r in p if r["passagem"] == 2]
    assert {r["semente_mestra"] for r in p if r["passagem"] == 1} == {20261208}


def test_deterministico_e_independe_da_ordem_da_lista():
    a = pl.montar_plano(nomes())
    b = pl.montar_plano(list(reversed(nomes())))
    assert a == b


def test_recusa_sobrescrever(tmp_path):
    lista = tmp_path / "l.csv"
    with open(lista, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["nome"]); [w.writerow([n]) for n in nomes()]
    saida = tmp_path / "p.csv"
    assert pl.principal(["--lista", str(lista), "--saida", str(saida)]) == 0
    assert pl.principal(["--lista", str(lista), "--saida", str(saida)]) == 2
