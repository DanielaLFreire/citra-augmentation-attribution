from scripts.construir_lista_treino import PLANOS


def test_plano_replica_L4_igual_ao_principal():
    assert PLANOS["principalL4"] == PLANOS["principal"]
