import numpy as np
import pytest

from scripts import analisar_principal_v2 as v2

SEM = [7, 42, 123, 2024, 31415]


def _av(valores):
    """valores: {(braco, metrica): lista por semente}"""
    av = {}
    for (braco, metrica), v in valores.items():
        for s, x in zip(SEM, v):
            av.setdefault(f"{braco}_principal_yolo11n_seed{s}", {})[metrica] = str(x)
    return av


def _base(extra=None):
    c = np.array([0.60, 0.61, 0.62, 0.63, 0.64])
    d = {}
    for m in ("mAP50_ultralytics", "recall_small_conf025", "AP50_small", "AP50_propria"):
        d[("C", m)] = c
        d[("R", m)] = c + 0.001 * np.array([1, -1, 1, -1, 0.5])
    d.update(extra or {})
    return _av(d)


def test_secundarias_sao_descritivas_sem_veredito_nem_p():
    r = v2.analisar(_base())
    for s in r["secundarias_descritivas"]:
        assert set(s) == {"metrica", "contraste", "n", "diferenca", "ic95"}
    assert [s["metrica"] for s in r["secundarias_descritivas"]] == ["recall_small_conf025", "AP50_small"]
    assert "p_holm" not in r["primaria"]["principal"]


def test_ap50_propria_so_verificacao():
    r = v2.analisar(_base())
    v = r["verificacao_AP50_propria"]
    assert v["metrica"] == "AP50_propria" and v["diferenca_do_mAP50_API"] == pytest.approx(0.0, abs=1e-12)


def test_holm_so_entre_contrastes_entre_bracos():
    c = np.array([0.60, 0.61, 0.62, 0.63, 0.64])
    extra = {("E", "mAP50_ultralytics"): c + 0.02 + 0.001 * np.array([1, -1, 0, 1, -1]),
             ("G", "mAP50_ultralytics"): c + 0.001 * np.array([1, -1, 0, 1, -1])}
    for b in ("E", "G"):
        for m in ("recall_small_conf025", "AP50_small", "AP50_propria"):
            extra[(b, m)] = c
    r = v2.analisar(_base(extra), contrastes=["E-C", "G-C"])
    cs = {x["contraste"]: x for x in r["contrastes_secundarios"]}
    assert set(cs) == {"E-C", "G-C"} and all(x["rotulo"] == "secundário" for x in cs.values())
    assert cs["E-C"]["p_holm"] >= cs["E-C"]["p_t_pareado"] and cs["G-C"]["p_holm"] <= 1.0
    assert "melhora" in cs["E-C"]["conclusao"]


def test_contraste_sem_braco_e_ignorado():
    assert v2.analisar(_base(), contrastes=["E-C"])["contrastes_secundarios"] == []
