import numpy as np
import pytest

from scripts import analisar_principal as ap


def test_contraste_melhora_piora_equivalente_inconclusivo():
    base = np.array([0.60, 0.61, 0.62, 0.63, 0.64, 0.60, 0.61, 0.62, 0.63, 0.64])
    ruido = np.array([0.001, -0.001, 0.0005, -0.0005, 0.0, 0.001, -0.001, 0.0005, -0.0005, 0.0])
    melhora = ap.contraste_pareado(base + 0.02 + ruido, base)
    assert "melhora" in melhora["conclusao"] and "equivalente" not in melhora["conclusao"]
    piora = ap.contraste_pareado(base - 0.02 + ruido, base)
    assert piora["conclusao"] == ["piora"]
    equiv = ap.contraste_pareado(base + ruido, base)
    assert equiv["conclusao"] == ["equivalente"] and abs(equiv["diferenca"]) < 0.001
    # efeito pequeno e ruído grande: inconclusivo
    rng = np.random.default_rng(1)
    r = ap.contraste_pareado(base + rng.normal(0, 0.02, 10), base)
    assert r["conclusao"] == ["inconclusivo"] or "equivalente" not in r["conclusao"]


def test_sobreposicao_melhora_e_equivalente():
    base = np.linspace(0.60, 0.65, 10)
    d = np.array([0.004, 0.0045, 0.0042, 0.0041, 0.0043, 0.0044, 0.0042, 0.0043, 0.0041, 0.0042])
    r = ap.contraste_pareado(base + d, base)
    assert r["conclusao"] == ["melhora", "equivalente"]


def test_estatisticas_conhecidas():
    a = [1.0, 2.0, 3.0, 4.0]
    b = [0.5, 1.5, 2.0, 3.5]  # d = 0,5; 0,5; 1,0; 0,5 -> média 0,625
    r = ap.contraste_pareado(a, b, margem=1.0)
    assert r["diferenca"] == pytest.approx(0.625) and r["dp_diferenca"] == pytest.approx(0.25)
    assert r["ic95"][0] == pytest.approx(0.625 - 3.182446 * 0.125, rel=1e-4)
    assert r["p_permutacao"] == pytest.approx(2 / 16)  # só os dois sinais todos iguais têm |média| >= 0,625
    with pytest.raises(ValueError):
        ap.contraste_pareado([1, 2], [1, 2])


def test_holm():
    assert ap.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert ap.holm([0.5])[0] == 0.5 and max(ap.holm([0.9, 0.8])) <= 1.0


def _avaliacao(valores_r, valores_c):
    sem = [7, 42, 123, 2024, 31415]
    av = {}
    for s, v in zip(sem, valores_r):
        av[f"R_principal_yolo11n_seed{s}"] = {"mAP50_ultralytics": str(v)}
    for s, v in zip(sem, valores_c):
        av[f"C_principal_yolo11n_seed{s}"] = {"mAP50_ultralytics": str(v)}
    return av


def test_analise_principal_e_sensibilidade_gpu():
    av = _avaliacao([0.62, 0.63, 0.64, 0.65, 0.66], [0.61, 0.625, 0.63, 0.645, 0.65])
    gpu = {f"C_principal_yolo11n_seed{s}": ("NVIDIA L4" if s in (123, 2024, 31415) else "NVIDIA A100") for s in (7, 42, 123, 2024, 31415)}
    r = ap.analise_principal(av, gpu_por_id=gpu)
    assert r["sementes"] == [7, 42, 123, 2024, 31415] and r["principal"]["n"] == 5
    assert r["so_L4"]["sementes"] == [123, 2024, 31415]
    assert set(r["margens"]) == {"0.005", "0.01", "0.015"}


def test_dias_e_subconjunto(tmp_path):
    nova, antiga = tmp_path / "n.csv", tmp_path / "a.csv"
    nova.write_text("nome,dia,divisao\na,d1,test\nb,d1,test\nc,d2,test\nd,d3,train\n", encoding="utf-8")
    antiga.write_text("nome,dia,divisao\na,d1,train\nb,d1,val\nc,d2,test\nd,d3,train\n", encoding="utf-8")
    g = ap.dias_e_subconjunto(nova, antiga)
    assert g["nunca_avaliadas"] == {"a"} and g["dia_d1"] == {"a", "b"} and g["dia_d2"] == {"c"} and "dia_d3" not in g
