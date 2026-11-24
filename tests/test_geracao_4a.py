import json

from scripts import geracao_4a as g


def amostra_fake():
    linhas = [{"ordem": str(i), "nome": f"img{i:03d}", "bloco": "b", "estrato": "padrao" if i <= 120 else "risco"} for i in range(1, 151)]
    return linhas


def test_lotes_dividem_por_estrato():
    lotes = g.lotes_de(amostra_fake())
    assert len(lotes) == 5 and sorted(lotes) == ["padrao_01", "padrao_02", "padrao_03", "padrao_04", "risco_01"]
    assert sum(len(v) for v in lotes.values()) == 150
    assert len(lotes["risco_01"]) == 30


def test_falha_tecnica():
    assert g.eh_falha_tecnica("ServerError('503')")
    assert not g.eh_falha_tecnica("AssertionError('Generated image is None!')")
    assert not g.eh_falha_tecnica(None)


def test_registros_e_erros(tmp_path):
    d = tmp_path / "lote" / "t1"
    d.mkdir(parents=True)
    (d / "AUG_a.json").write_text(json.dumps({"image": "a.jpg", "status": "ok"}))
    (d / "AUG_b.json").write_text(json.dumps({"image": "b.jpg", "status": "error", "error": "X"}))
    assert set(g.registros_ok(tmp_path / "lote")) == {"a"}
    assert g.ultimo_erro(tmp_path / "lote") == {"b": "X"}
