import json
from datetime import datetime, timezone

from scripts import producao_E as pe


def base():
    return json.loads(pe.g.SAIDA_PARAMETROS.read_text())


def test_parametros_das_duas_passagens():
    plano = pe.ler_plano()
    for p, semente in ((1, 20261208), (2, 20261209)):
        P = pe.parametros_passagem(plano, p, base())
        assert P["semente_mestra"] == semente and P["n_imagens"] == 1370
        assert P["por_estrato"] == {"padrao": 1096, "risco": 274}
        assert sum(len(v) for v in P["lotes"].values()) == 1370
        assert all(len(v) <= 30 for v in P["lotes"].values())
        assert len({n for v in P["lotes"].values() for n in v}) == 1370
    # fonte na mesma posição de ordem nas duas passagens; só o estrato e a semente mudam
    o = lambda p: [r["nome"] for r in plano if int(r["passagem"]) == p]
    assert o(1) == o(2)


def test_lotes_seguem_a_ordem_do_plano():
    plano = pe.ler_plano()
    P = pe.parametros_passagem(plano, 1, base())
    pad = [r["nome"] for r in plano if r["passagem"] == "1" and r["estrato"] == "padrao"]
    assert P["lotes"]["padrao_001"] == pad[:30] and P["lotes"]["padrao_002"][0] == pad[30]


def test_recusas(tmp_path, capsys):
    args = ["--citra-raiz", "x", "--iflens-dir", "y", "--trabalho", str(tmp_path)]
    assert pe.principal(["--passagem", "2", *args]) == 2                       # sem contagem
    c = tmp_path / "c.json"; c.write_text(json.dumps({"validas": 1370}))
    assert pe.principal(["--passagem", "2", "--contagem-passagem1", str(c), *args]) == 2   # 1370 não é < 1370
    assert pe.principal(["--passagem", "1", *args], agora=datetime(2026, 12, 21, 3, 0, tzinfo=timezone.utc)) == 2  # fora da janela


def test_execucao_completa_com_executores_falsos(tmp_path, monkeypatch, capsys):
    from scripts import producao_E_v2 as pv2
    monkeypatch.setattr(pv2.g, "executar", lambda *a, **k: {"lotes": {"padrao_001": {"n": 30, "ok": 0}}})
    monkeypatch.setattr(pv2.v3, "executar_risco", lambda *a, **k: {"risco_001": {"n": 30, "ok": 0}})
    rc = pv2.principal(["--passagem", "1", "--citra-raiz", "x", "--iflens-dir", "y", "--trabalho", str(tmp_path), "--max-lotes", "1"])
    assert rc == 0 and '"passagem": 1' in capsys.readouterr().out
