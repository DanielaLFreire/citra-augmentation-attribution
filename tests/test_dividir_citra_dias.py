from scripts.dividir_citra_dias import ALVOS, dentro, sortear

CONT = {f"{d:02d}.04.2022": c for d, c in enumerate(
    [5, 11, 19, 31, 39, 40, 47, 48, 53, 55, 56, 60, 70, 80, 92, 93, 98, 99, 103, 104, 104, 113, 114, 121, 122, 148, 156], start=1)}


def test_sortear_deterministico_e_dentro_da_tolerancia():
    a, ta = sortear(CONT, 123)
    b, tb = sortear(CONT, 123)
    assert a == b and ta == tb
    for s in ("test", "val", "train"):
        assert dentro(sum(CONT[d] for d in a[s]), ALVOS[s])


def test_sortear_particao_sem_sobreposicao_de_dias():
    a, _ = sortear(CONT, 7)
    todos = a["test"] + a["val"] + a["train"]
    assert sorted(todos) == sorted(CONT) and len(set(todos)) == len(CONT)
