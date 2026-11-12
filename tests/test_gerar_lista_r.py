import random

from scripts.gerar_lista_r import cotas, elegiveis, sortear, unidade


def _r(i, cam, cl="", caixas="1", dup="", st="ok"):
    return {"id_imagem": i, "caminho_relativo": cam, "cluster_quase_dup": cl, "n_caixas": caixas,
            "dup_base_de": dup, "dup_conteudo_de": "", "status_auditoria": st}


def test_cotas_redistribui():
    assert cotas({"a": 2, "b": 10, "c": 10}, 12) == {"a": 2, "b": 5, "c": 5}
    assert sum(cotas({"a": 3, "b": 3}, 10).values()) == 6


def test_unidades():
    assert unidade("aboships", "x/Seaships/20180626/201806260750_003.png") == "201806260750"
    assert unidade("smd", "smd_clean/test/images/MVI_1448_VIS_Haze_frame0.jpg") == "MVI_1448"


def test_elegiveis_um_por_cluster_e_exclusoes():
    L = [_r("1", "d/201806260750_001.png", cl="9"), _r("2", "d/201806260750_002.png", cl="9"),
         _r("3", "d/201806260750_003.png", cl="8"), _r("4", "d/201806260750_004.png", caixas="0"),
         _r("5", "d/201806260750_005.png", cl="7")]
    e = elegiveis("aboships", L, {"5"})
    assert sorted(r["id_imagem"] for r in e["201806260750"]) == ["1", "3"]


def test_sorteio_deterministico():
    p = {"u1": [_r(str(i), "x") for i in range(10)], "u2": [_r("z" + str(i), "x") for i in range(10)]}
    a = [r["id_imagem"] for _, r in sortear(p, 6, random.Random(1))]
    b = [r["id_imagem"] for _, r in sortear(p, 6, random.Random(1))]
    assert a == b and len(a) == 6
