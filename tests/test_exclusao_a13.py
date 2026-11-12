from scripts.gerar_exclusao_a13 import excluidas


def _r(i, base, col):
    return {"id_imagem": i, "caminho_relativo": i + ".jpg", "sha256_conteudo": "h" + i, "colide_citra": col, "base_roboflow": base}


def test_seaships_exclui_todas_as_versoes_da_base():
    linhas = [_r("a1", "001", "quase:train"), _r("a2", "001", ""), _r("b1", "002", "")]
    assert {r["id_imagem"] for r in excluidas("seaships", linhas)} == {"a1", "a2"}


def test_outras_fontes_so_as_marcadas():
    linhas = [_r("a", "", "quase:val"), _r("b", "", "")]
    assert [r["id_imagem"] for r in excluidas("aboships", linhas)] == ["a"]
