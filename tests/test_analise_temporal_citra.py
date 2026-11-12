import datetime as dt

from scripts.analise_temporal_citra import analisar, intervalos


def test_intervalos_e_dias():
    t = lambda h, m, s=0: dt.datetime(2022, 5, 1, h, m, s)
    T = {"train": [t(10, 0), t(12, 0)], "val": [t(10, 1)], "test": [t(11, 59, 30)]}
    assert intervalos(T["train"], T["val"]) == [60.0]
    r = analisar(T)
    assert r["dias_nos_tres_splits"] == 1 and r["test"]["minimo_s"] == 30 and r["val"]["ate_60s"] == 1.0
