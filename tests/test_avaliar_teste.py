import json

import numpy as np
import pytest

from scripts import avaliar_teste as at
from scripts._hashes import sha256


def test_iou_e_area():
    m = at.iou_matriz([[0, 0, 10, 10]], [[0, 0, 10, 10], [5, 0, 15, 10], [20, 20, 30, 30]])
    assert m[0, 0] == pytest.approx(1.0) and m[0, 1] == pytest.approx(1 / 3, rel=1e-6) and m[0, 2] == 0
    assert at.iou_matriz(np.zeros((0, 4)), [[0, 0, 1, 1]]).shape == (0, 1)
    # 32x32 px a 640 não é small (< 32²); 31x31 é; imagem 1280x720 reduz pela metade
    assert at.area_640([[0, 0, 32, 32]], 640, 360)[0] == 1024
    assert at.area_640([[0, 0, 31, 31]], 640, 360)[0] < at.LIMITE_SMALL
    assert at.area_640([[0, 0, 64, 64]], 1280, 720)[0] == pytest.approx(1024)


def test_ap_de_curva():
    assert np.isnan(at.ap_de_curva([0.9], [True], 0))
    perfeito = at.ap_de_curva([0.9], [True], 1)
    metade = at.ap_de_curva([0.9], [True], 2)
    assert perfeito >= 0.99 and 0.6 < metade < 0.9 and perfeito > metade
    assert at.ap_de_curva([0.9, 0.5], [False, False], 1) == pytest.approx(0.0, abs=1e-9)


def test_casar_imagem_basico_e_ignorados():
    gt = [[0, 0, 10, 10]]
    c, tp, v, cas = at.casar_imagem([[0, 0, 10, 10], [0, 0, 10, 10]], [0.5, 0.9], gt, [False], [False, False])
    assert list(c) == [0.9, 0.5] and list(tp) == [True, False] and all(v) and list(cas) == [True]
    # casou com caixa ignorada: predição ignorada e caixa não conta como casada
    c, tp, v, cas = at.casar_imagem([[0, 0, 10, 10]], [0.9], gt, [True], [True])
    assert not v[0] and not tp[0] and not cas[0]
    # solta e fora do estrato: ignorada; solta e dentro do estrato: falso positivo válido
    _, tp, v, _ = at.casar_imagem([[50, 50, 60, 60]], [0.9], gt, [False], [True])
    assert not v[0]
    _, tp, v, _ = at.casar_imagem([[50, 50, 60, 60]], [0.9], gt, [False], [False])
    assert v[0] and not tp[0]
    # sem predições
    c, tp, v, cas = at.casar_imagem(np.zeros((0, 4)), [], gt, [False], [])
    assert len(c) == 0 and list(cas) == [False]


def _imagem(preds, confs, gts):
    return {"pred_xyxy": preds, "pred_conf": confs, "gt_xyxy": gts, "largura": 640, "altura": 640}


def test_medidas_proprias_small():
    gts = [[0, 0, 20, 20], [100, 100, 200, 200]]  # uma small (400 px²), uma grande
    im = _imagem([[0, 0, 20, 20], [100, 100, 200, 200], [300, 300, 320, 320]], [0.9, 0.8, 0.5], gts)
    m = at.medidas_proprias([im])
    assert m["n_caixas"] == 2 and m["n_caixas_small"] == 1
    assert m["recall_small_conf025"] == 1.0
    assert m["AP50_small"] >= 0.7 and m["AP50_propria"] >= 0.7  # o falso positivo small vem depois dos acertos
    # acerto com confiança abaixo de 0,25 não conta no recall, mas conta no AP
    im2 = _imagem([[0, 0, 20, 20]], [0.1], [[0, 0, 20, 20]])
    m2 = at.medidas_proprias([im2])
    assert m2["recall_small_conf025"] == 0.0 and m2["AP50_small"] >= 0.99
    # sem caixas small: recall e AP small indefinidos
    m3 = at.medidas_proprias([_imagem([[100, 100, 200, 200]], [0.9], [[100, 100, 200, 200]])])
    assert np.isnan(m3["recall_small_conf025"]) and np.isnan(m3["AP50_small"])
    # imagem sem nada
    m4 = at.medidas_proprias([_imagem(np.zeros((0, 4)), [], np.zeros((0, 4)))])
    assert m4["n_caixas"] == 0


def test_ler_rotulo_yolo(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("0 0.5 0.5 0.25 0.5\n\n", encoding="utf-8")
    caixas = at.ler_rotulo_yolo(f, 200, 100)
    assert caixas.tolist() == [[75.0, 25.0, 125.0, 75.0]]
    f.write_text("", encoding="utf-8")
    assert at.ler_rotulo_yolo(f, 200, 100).shape == (0, 4)


def _cenario(tmp_path, avaliado="nao"):
    aval = tmp_path / "avaliar_teste.py"
    aval.write_text("# script\n", encoding="utf-8")
    registro = []
    for s in (1, 2):
        w = tmp_path / f"w{s}.pt"
        w.write_bytes(b"pesos%d" % s)
        registro.append({"id_execucao": f"C_principal_yolo11n_seed{s}", "caminho_pesos": str(w), "sha256_pesos": sha256(w),
                         "avaliado_teste": avaliado})
    hashes = {"artefatos": {"avaliar_teste.py": {"sha256": sha256(aval)}},
              "adendos": {"adendo4_fontes_aumento.md": {}, "adendo4a_fidelidade_iflens.md": {}}}
    return aval, registro, hashes


def test_condicoes_teste_ok_e_falhas(tmp_path):
    aval, registro, hashes = _cenario(tmp_path)
    lacre = tmp_path / "lacre.json"
    ok = at.verificar_condicoes_teste(registro, hashes, aval, ["C"], lacre, sementes=[1, 2])
    assert [r["id_execucao"] for r in ok] == ["C_principal_yolo11n_seed1", "C_principal_yolo11n_seed2"]
    # lacre anterior
    lacre.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="já foi avaliado"):
        at.verificar_condicoes_teste(registro, hashes, aval, ["C"], lacre, sementes=[1, 2])
    lacre.unlink()
    # script alterado depois do registro
    aval.write_text("# alterado\n", encoding="utf-8")
    with pytest.raises(ValueError, match="alterado"):
        at.verificar_condicoes_teste(registro, hashes, aval, ["C"], lacre, sementes=[1, 2])
    aval.write_text("# script\n", encoding="utf-8")
    # adendo 4 não lacrado
    h2 = json.loads(json.dumps(hashes)); del h2["adendos"]["adendo4_fontes_aumento.md"]
    with pytest.raises(ValueError, match="adendo 4 não"):
        at.verificar_condicoes_teste(registro, h2, aval, ["C"], lacre, sementes=[1, 2])
    # execução ausente / já avaliada / pesos adulterados
    with pytest.raises(ValueError, match="ausente no registro"):
        at.verificar_condicoes_teste(registro[:1], hashes, aval, ["C"], lacre, sementes=[1, 2])
    _, reg2, _ = _cenario(tmp_path, avaliado="sim")
    with pytest.raises(ValueError, match="já consta"):
        at.verificar_condicoes_teste(reg2, hashes, aval, ["C"], lacre, sementes=[1, 2])
    registro[0]["sha256_pesos"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256"):
        at.verificar_condicoes_teste(registro, hashes, aval, ["C"], lacre, sementes=[1, 2])
    with pytest.raises(ValueError, match="nenhum braço"):
        at.verificar_condicoes_teste(registro, hashes, aval, [], lacre, sementes=[1, 2])


def test_condicoes_teste_sem_4a(tmp_path):
    aval, registro, hashes = _cenario(tmp_path)
    del hashes["adendos"]["adendo4a_fidelidade_iflens.md"]
    lacre, md = tmp_path / "l.json", tmp_path / "D.md"
    with pytest.raises(ValueError, match="4a não está lacrado"):
        at.verificar_condicoes_teste(registro, hashes, aval, ["C"], lacre, sementes=[1, 2], decisoes_md=md)
    md.write_text("| D70 | 2026-12-30 | E fora do experimento | ... |\n", encoding="utf-8")
    with pytest.raises(ValueError, match="não existe"):
        at.verificar_condicoes_teste(registro, hashes, aval, ["C"], lacre, "D99", md, [1, 2])
    assert len(at.verificar_condicoes_teste(registro, hashes, aval, ["C"], lacre, "D70", md, [1, 2])) == 2


def test_ids_principais():
    ids = at.ids_principais(["C", "R"])
    assert len(ids) == 20 and ids[0] == "C_principal_yolo11n_seed7" and ids[-1] == "R_principal_yolo11n_seed27182"
