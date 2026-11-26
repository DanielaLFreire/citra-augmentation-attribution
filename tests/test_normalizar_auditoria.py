import pytest

from scripts.normalizar_auditoria import normalizar


def L(tipo, cl, cat, obs=""):
    return {"codigo": "A001", "tipo": tipo, "item": "1", "classe": cl, "categoria": cat, "observacao": obs}


def test_move_e_grafia():
    out, rel = normalizar([L("caixa", "0", "deslocado"), L("imagem", "1", "", "embarcação"), L("original", "0", "")])
    assert out[0]["categoria"] == "deslocada" and out[1]["categoria"] == "1" and out[1]["classe"] == "" and out[1]["observacao"] == "embarcação"
    assert out[2]["categoria"] == "0" and rel["linhas_movidas_de_classe_para_categoria"] == 2


def test_nao_inventa():
    with pytest.raises(ValueError):
        normalizar([L("caixa", "0", "")])
    with pytest.raises(ValueError):
        normalizar([L("imagem", "", "")])
    with pytest.raises(ValueError):
        normalizar([L("caixa", "0", "talvez")])
