import numpy as np
import pytest

from scripts import analisar_hardware as ah

SEM_REPL = [7, 42, 123, 2024, 31415]
SEM_L4 = [101, 1001, 2025, 4242, 27182]


def _cenario(com_replica=True):
    av, gpu = {}, {}
    rng = np.random.default_rng(3)
    base = {s: 0.62 + 0.001 * k for k, s in enumerate(SEM_REPL + SEM_L4)}
    for s in SEM_REPL + SEM_L4:
        av[f"R_principal_yolo11n_seed{s}"] = {"mAP50_ultralytics": str(base[s] + 0.002)}
        av[f"C_principal_yolo11n_seed{s}"] = {"mAP50_ultralytics": str(base[s])}
        gpu[f"C_principal_yolo11n_seed{s}"] = "NVIDIA A100-SXM4-80GB" if s in SEM_REPL else "NVIDIA L4"
    if com_replica:
        for s in SEM_REPL:
            av[f"C_principalL4_yolo11n_seed{s}"] = {"mAP50_ultralytics": str(base[s] + 0.004 + rng.normal(0, 0.0005))}
            gpu[f"C_principalL4_yolo11n_seed{s}"] = "NVIDIA L4"
    return av, gpu


def test_C_L4_usa_replica_e_originais_na_L4():
    av, gpu = _cenario()
    c, origem = ah.montar_C_L4(av, gpu)
    assert sorted(c) == sorted(SEM_REPL + SEM_L4)
    assert all(origem[s] == "replica_L4" for s in SEM_REPL) and all(origem[s] == "original_L4" for s in SEM_L4)
    assert c[7] == pytest.approx(0.624, abs=0.002) and c[101] == pytest.approx(0.625 - 0.0, abs=0.01)


def test_sem_replica_so_ha_5_pares_e_nao_conta_A100():
    av, gpu = _cenario(com_replica=False)
    c, origem = ah.montar_C_L4(av, gpu)
    assert sorted(c) == sorted(SEM_L4) and set(origem.values()) == {"original_L4"}
    r = ah.analisar(av, gpu)
    assert r["R_menos_C_L4"]["n"] == 5 and "efeito_hardware_L4_menos_A100" not in r


def test_analise_completa_e_efeito_hardware():
    av, gpu = _cenario()
    r = ah.analisar(av, gpu)
    assert r["R_menos_C_L4"]["n"] == 10
    ef = r["efeito_hardware_L4_menos_A100"]
    assert ef["sementes"] == SEM_REPL and ef["diferenca"] == pytest.approx(0.004, abs=0.001)
    # 5 pares com R−C_L4 : nas sementes replicadas R−C_L4 ≈ −0,002; nas demais +0,002 → média perto de 0
    assert abs(r["R_menos_C_L4"]["diferenca"]) < 0.0015
