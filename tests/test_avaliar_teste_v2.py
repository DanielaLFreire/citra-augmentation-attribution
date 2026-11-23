import numpy as np

from scripts import avaliar_teste_v2 as v2


def test_ida_e_volta_das_predicoes(tmp_path):
    itens = [
        {"pred_xyxy": [[0, 0, 10, 10], [5, 5, 20, 20]], "pred_conf": [0.9, 0.2], "gt_xyxy": [[0, 0, 10, 10]], "largura": 1920, "altura": 1080},
        {"pred_xyxy": np.zeros((0, 4)), "pred_conf": [], "gt_xyxy": [[1, 1, 3, 3], [4, 4, 9, 9]], "largura": 1920, "altura": 1061},
        {"pred_xyxy": [[7, 7, 8, 8]], "pred_conf": [0.5], "gt_xyxy": np.zeros((0, 4)), "largura": 1920, "altura": 1080},
    ]
    f = tmp_path / "m.npz"
    v2.salvar_predicoes(f, ["a", "b", "c"], itens)
    volta = v2.carregar_predicoes(f)
    assert [i["nome"] for i in volta] == ["a", "b", "c"]
    assert [len(i["pred_conf"]) for i in volta] == [2, 0, 1] and [len(i["gt_xyxy"]) for i in volta] == [1, 2, 0]
    assert volta[1]["altura"] == 1061 and volta[0]["pred_xyxy"].tolist() == [[0, 0, 10, 10], [5, 5, 20, 20]]
    assert np.allclose(volta[0]["pred_conf"], [0.9, 0.2], atol=1e-6)
    # as medidas sobre o que foi gravado são iguais às medidas sobre os itens originais
    from scripts.avaliar_teste import medidas_proprias
    a, b = medidas_proprias(itens), medidas_proprias(volta)
    assert a["n_caixas"] == b["n_caixas"] and a["n_caixas_small"] == b["n_caixas_small"]


def test_predicoes_vazias(tmp_path):
    f = tmp_path / "v.npz"
    v2.salvar_predicoes(f, [], [])
    assert v2.carregar_predicoes(f) == []
