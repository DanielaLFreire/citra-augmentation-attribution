from scripts.analise_reavaliacao_v4 import eh_embarcacao, kappa, mcnemar_exato, wilson


def test_eh_embarcacao():
    for t in ("embarcacao", "embarcações", "varias embarcacoes", "varias embarcacaoes", "barco", "Lancha grande"):
        assert eh_embarcacao(t), t
    for t in ("boia", "ave", "pessoa", "", None, "cidade alterada"):
        assert not eh_embarcacao(t), t


def test_kappa_perfeito_e_acaso():
    assert kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"])[1] == 1.0
    assert abs(kappa(["a", "a", "b", "b"], ["a", "b", "a", "b"])[1]) < 1e-12


def test_mcnemar_exato():
    assert mcnemar_exato(0, 0) == 1.0
    assert abs(mcnemar_exato(1, 8) - 0.0391) < 0.001


def test_wilson_limites():
    lo, hi = wilson(0, 30)
    assert lo == 0 or lo < 1e-9
    assert 0 < hi < 0.2
