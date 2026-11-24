import json

import pytest

from scripts import filtro_llm_iflens as f

OK2 = '{"caixas":[{"caixa":1,"categoria":"valida"},{"caixa":2,"categoria":"valida"}],"objeto_adicionado":{"presente":false,"tipo":""}}'


def _lit(cats, add=False, tipo=""):
    return {"caixas": {i + 1: c for i, c in enumerate(cats)}, "adicionado": add, "tipo": tipo}


def test_parse_resposta_valida_e_com_ruido():
    assert f.parse_resposta(OK2, 2)["caixas"] == {1: "valida", 2: "valida"}
    assert f.parse_resposta("<think>hmm {x}</think>\n```json\n" + OK2 + "\n```\nfim", 2) is not None


@pytest.mark.parametrize("texto,n", [(None, 2), ("", 2), ("sem json", 2), ("{quebrado", 2), (OK2, 3), (OK2, 1),
                                      ('{"caixas":[{"caixa":1,"categoria":"ruim"}],"objeto_adicionado":{"presente":false}}', 1),
                                      ('{"caixas":[],"objeto_adicionado":{"presente":false}}', 1)])
def test_parse_resposta_invalida(texto, n):
    assert f.parse_resposta(texto, n) is None


def test_regras_de_decisao():
    assert f.sinalizada(None, "R1") is True  # falha de leitura sinaliza
    assert f.sinalizada(_lit(["valida", "valida"]), "R1") is False
    for cat in ("apagada", "deslocada", "alterada"):
        assert f.sinalizada(_lit(["valida", cat]), "R1") is True
    assert f.sinalizada(_lit(["valida"], True, "embarcacao"), "R1") is True
    assert f.sinalizada(_lit(["valida"], True, "boia"), "R1") is False  # boia não entra no primário
    assert f.sinalizada(_lit(["degradada"]), "R1") is False and f.sinalizada(_lit(["degradada"]), "R2") is True
    assert f.sinalizada(_lit(["nao_avaliavel"]), "R2") is False and f.sinalizada(_lit(["nao_avaliavel"]), "R3") is True
    assert f.sinalizada(_lit(["sem_objeto_original"]), "R3") is False
    with pytest.raises(ValueError):
        f.sinalizada(_lit(["valida"]), "R9")


def test_metricas_e_taxa_residual():
    ref = {"a": True, "b": True, "c": False, "d": False, "e": False}
    fl = {"a": True, "b": False, "c": False, "d": True, "e": False}
    m = f.metricas(fl, ref)
    assert (m["tp"], m["fn"], m["tn"], m["fp"]) == (1, 1, 2, 1)
    assert m["sensibilidade"] == 0.5 and m["especificidade"] == pytest.approx(2 / 3)
    assert m["taxa_residual"] == pytest.approx(1 / 3) and m["n_nao_sinalizadas"] == 3
    assert m["taxa_descarte"] == pytest.approx(2 / 5)


def test_selecao_pre_declarada():
    r = lambda c, p, g, s, e: {"config": c, "provedor": p, "regra": g, "sensibilidade": s, "especificidade": e}
    # entre os que passam de 0,85, a maior especificidade
    assert f.selecionar([r("a", "groq", "R1", 0.9, 0.5), r("b", "gemini", "R1", 0.86, 0.7), r("c", "groq", "R2", 0.8, 0.95)])["config"] == "b"
    # empate: provedor groq, depois regra mais simples
    assert f.selecionar([r("a", "gemini", "R1", 0.9, 0.7), r("b", "groq", "R2", 0.9, 0.7), r("c", "groq", "R1", 0.9, 0.7)])["config"] == "c"
    # ninguém passa: maior sensibilidade
    assert f.selecionar([r("a", "groq", "R1", 0.7, 0.9), r("b", "groq", "R2", 0.8, 0.4)])["config"] == "b"


def test_cache_e_uma_chamada_por_folha(tmp_path):
    folha = tmp_path / "A001.png"
    from PIL import Image
    Image.new("RGB", (20, 20), "white").save(folha)
    n = []
    def falso(modelo, prompt, dados, mime):
        n.append(1)
        return {"texto": OK2, "modelo_retornado": "m", "id": "x"}
    r1 = f.ler_folha("groq", "qwen/x", folha, tmp_path / "c", falso)
    r2 = f.ler_folha("groq", "qwen/x", folha, tmp_path / "c", falso)
    assert len(n) == 1 and r1 == r2 and r1["prompt_sha256"] == f.sha256(f.PROMPT)


def test_preparar_imagem_reduz_acima_do_limite(tmp_path, monkeypatch):
    import numpy as np
    from PIL import Image
    p = tmp_path / "g.png"
    Image.fromarray((np.random.default_rng(0).random((900, 900, 3)) * 255).astype("uint8")).save(p)
    monkeypatch.setattr(f, "LIMITE_BYTES", 200_000)
    dados, mime = f.preparar_imagem(p)
    assert mime == "image/jpeg" and len(dados) <= 200_000


def test_referencia_piloto_com_dados_reais():
    ref, ncx = f.referencia_piloto(f.RAIZ / "data" / "auditoria_piloto_iflens")
    assert len(ref) == 60 and sum(ref.values()) == 16  # D33: v1 5 de 30 e v2 11 de 30 (qualquer avaliador, primário)
    assert all(ncx[c] >= 1 for c in ref)


def test_desenvolver_ponta_a_ponta_com_modelo_falso(tmp_path):
    from PIL import Image
    ref, ncx = f.referencia_piloto(f.RAIZ / "data" / "auditoria_piloto_iflens")
    folhas = tmp_path / "folhas"; folhas.mkdir()
    for c in ref:
        Image.new("RGB", (10, 10)).save(folhas / f"{c}.png")
    # modelo "oráculo": lê a folha pelo código e acerta a referência (apagada se reprovada)
    def oraculo(modelo, prompt, dados, mime):
        raise AssertionError("não deve ser chamado sem a folha")
    estado = {"i": 0}
    cods = sorted(ref)
    def falso(modelo, prompt, dados, mime):
        c = cods[estado["i"] % len(cods)]; estado["i"] += 1
        cats = ["apagada" if (ref[c] and k == 1) else "valida" for k in range(1, ncx[c] + 1)]
        return {"texto": json.dumps({"caixas": [{"caixa": k + 1, "categoria": v} for k, v in enumerate(cats)],
                                      "objeto_adicionado": {"presente": False, "tipo": ""}}), "modelo_retornado": "m", "id": "i"}
    res = f.desenvolver(f.RAIZ / "data" / "auditoria_piloto_iflens", folhas, tmp_path / "cache", ["groq:fake"], falso)
    r1 = next(r for r in res["resultados"] if r["regra"] == "R1")
    assert res["positivos"] == 16 and r1["sensibilidade"] == 1.0 and r1["especificidade"] == 1.0 and r1["falhas_de_leitura"] == 0


def test_cache_depende_do_prompt(tmp_path, monkeypatch):
    from PIL import Image
    folha = tmp_path / "A001.png"
    Image.new("RGB", (20, 20), "white").save(folha)
    n = []
    def falso(modelo, prompt, dados, mime):
        n.append(prompt)
        return {"texto": OK2, "modelo_retornado": "m", "id": "x"}
    f.ler_folha("groq", "qwen/x", folha, tmp_path / "c", falso)
    outro = tmp_path / "prompt2.txt"
    outro.write_text("prompt diferente")
    monkeypatch.setattr(f, "PROMPT", outro)
    f.ler_folha("groq", "qwen/x", folha, tmp_path / "c", falso)
    assert len(n) == 2 and n[1] == "prompt diferente"
