import csv

import pytest

from scripts.construir_lista_treino import (PLANOS, QUARENTENA_D10, construir_lista, relatorio,
                                            treino_efetivo)


def ids(n, prefixo="c"):
    return [f"{prefixo}{i:04d}" for i in range(n)]


def externas(n):
    return [(i, "iflens") for i in ids(n, "e")]


def test_aritmetica_da_d35_com_tamanhos_reais():
    p = PLANOS["principal"]
    linhas = construir_lista(ids(1370), externas(1370), "E", fator_citra=p["fator_citra"], n_ext=p["n_ext"],
                             ciclos_por_epoca=p["ciclos_por_epoca"])
    r = relatorio(linhas, epocas=p["epocas"])
    assert r["linhas_por_epoca"] == 10960
    assert r["passos_por_epoca"] == 685
    assert r["passos_total"] == 25345
    assert r["fracao_externa"] == 0.25


def test_aritmetica_do_plano_reserva():
    p = PLANOS["reserva"]
    linhas = construir_lista(ids(1370), externas(454), "E", fator_citra=p["fator_citra"], n_ext=p["n_ext"],
                             ciclos_por_epoca=p["ciclos_por_epoca"])
    r = relatorio(linhas, epocas=p["epocas"])
    assert (r["linhas_por_epoca"], r["passos_por_epoca"], r["passos_total"]) == (1824, 114, 25308)
    assert r["fracao_externa"] == 0.2489


def test_contagem_por_imagem_miniatura():
    linhas = construir_lista(ids(8), externas(8), "R", fator_citra=3, n_ext=8, ciclos_por_epoca=2, lote=16)
    r = relatorio(linhas, epocas=1, lote=16)
    assert r["linhas_por_epoca"] == 64
    assert r["fracao_externa"] == 0.25
    vezes = {}
    for x in linhas:
        vezes[(x["fonte"], x["id_imagem"])] = vezes.get((x["fonte"], x["id_imagem"]), 0) + 1
    assert {v for (f, _), v in vezes.items() if f == "citra"} == {6}
    assert {v for (f, _), v in vezes.items() if f == "iflens"} == {2}


def test_braco_c_com_n_igual_ao_treino_e_citra_x4():
    linhas = construir_lista(ids(8), None, "C", fator_citra=3, n_ext=8, ciclos_por_epoca=2, lote=16)
    vezes = {}
    for x in linhas:
        vezes[x["id_imagem"]] = vezes.get(x["id_imagem"], 0) + 1
    assert set(vezes.values()) == {8}
    assert sum(1 for x in linhas if x["fonte"] == "citra_extra") == 16


def test_braco_c_reserva_sorteio_sem_repeticao_e_pela_semente():
    kw = dict(fator_citra=1, n_ext=4, ciclos_por_epoca=1, lote=4)
    a = construir_lista(ids(12), None, "C", semente=1, **kw)
    b = construir_lista(ids(12), None, "C", semente=1, **kw)
    c = construir_lista(ids(12), None, "C", semente=2, **kw)
    extras = lambda L: [x["id_imagem"] for x in L if x["fonte"] == "citra_extra"]
    assert a == b
    assert len(set(extras(a))) == 4
    assert extras(a) != extras(c)


def test_erros():
    kw = dict(fator_citra=3, ciclos_por_epoca=2, lote=16)
    with pytest.raises(ValueError, match="múltiplo"):
        construir_lista(ids(7), externas(7), "E", n_ext=7, **kw)
    with pytest.raises(ValueError, match="N igual"):
        construir_lista(ids(8), externas(7), "E", n_ext=8, **kw)
    with pytest.raises(ValueError, match="mesmo id"):
        construir_lista(ids(8), [(i, "x") for i in ids(8)], "E", n_ext=8, **kw)
    with pytest.raises(ValueError, match="repetidos"):
        construir_lista(ids(8), [("e1", "x")] * 8, "E", n_ext=8, **kw)
    with pytest.raises(ValueError, match="precisa"):
        construir_lista(ids(8), None, "E", n_ext=8, **kw)
    with pytest.raises(ValueError, match="não recebe"):
        construir_lista(ids(8), externas(8), "C", n_ext=8, **kw)


def test_treino_efetivo_tira_quarentena_e_so_train(tmp_path):
    f = tmp_path / "d.csv"
    with open(f, "w", newline="") as h:
        w = csv.writer(h)
        w.writerow(["nome", "dia", "divisao"])
        w.writerow(["a", "d1", "train"])
        w.writerow(["b", "d1", "test"])
        w.writerow(["c", "d2", "val"])
        w.writerow([QUARENTENA_D10[0], "d3", "train"])
    assert treino_efetivo(f) == ["a"]
