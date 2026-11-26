import json
import sys
from pathlib import Path

import pytest

from scripts import producao_E_v3 as p3


def montar(tmp_path, nomes):
    raiz = tmp_path / "citra" / "dia"
    (raiz / "images").mkdir(parents=True); (raiz / "labels_final").mkdir()
    for n in nomes:
        (raiz / "images" / f"{n}.png").write_bytes(b"x"); (raiz / "labels_final" / f"{n}.txt").write_text("0 .5 .5 .1 .1\n")
    P = {"lotes": {"padrao_001": nomes, "risco_001": ["r"]}, "max_tentativas_falha_tecnica": 3, "semente_mestra": 1,
         "condicoes": {"padrao": {"arquivo": "c.yaml"}}, "modelo_geracao_solicitado": "m", "modelo_visao_classificacao": "v",
         "prompt_arquivo": "prompts/prompt_v1.txt"}
    return P, tmp_path / "citra", tmp_path / "trab"


class Falso:
    """Simula o iflens: para cada chamada, consome o próximo resultado roteirizado da fonte."""
    def __init__(self, roteiro):
        self.roteiro, self.k, self.cmds = {n: list(v) for n, v in roteiro.items()}, 0, []

    def __call__(self, cmd, cwd, limite):
        self.cmds.append(cmd)
        ds, out = Path(cmd[cmd.index("--dataset") + 1]), Path(cmd[cmd.index("--output") + 1])
        nome = next(ds.glob("*.png")).stem
        r = self.roteiro[nome].pop(0)
        self.k += 1
        if r == "sem_registro":
            return "tempo_esgotado"
        pasta = out / f"2026-11-27_00-00-{self.k:02d}"; pasta.mkdir(parents=True)
        reg = {"image": f"{nome}.png", "status": r if r != "bloqueio" else "error"}
        if r == "error": reg["error"] = "ServerError(503)"
        if r == "bloqueio": reg["error"] = "AssertionError('Generated image is None!')"
        (pasta / f"AUG_{nome}.json").write_text(json.dumps(reg))
        return "tempo_esgotado" if r == "started" else "concluida"


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(p3, "conferir", lambda P, d: None)
    monkeypatch.setattr(p3.time, "sleep", lambda s: None)


def test_uma_por_vez_ordem_e_tentativas_com_evidencia(tmp_path):
    P, citra, trab = montar(tmp_path, ["a", "b", "c", "d"])
    # a: ok; b: started, depois ok; c: sem registro duas vezes e started (esgota); d: bloqueio (não repete)
    f = Falso({"a": ["ok"], "b": ["started"], "c": ["sem_registro"], "d": ["bloqueio"]})
    r = p3.executar_padrao(P, citra, Path("."), trab, chamar=f)
    assert [Path(c[c.index("--dataset") + 1]).name for c in f.cmds] == ["padrao_001"] * 4
    assert all(c[c.index("--n") + 1] == "1" for c in f.cmds)
    assert r["padrao_001"] == {"n": 4, "ok": 1, "bloqueadas": 1, "esgotadas": 0, "pendentes": 2, "chamadas_agora": 4}
    f.roteiro.update({"b": ["ok"], "c": ["sem_registro", "started"]})
    r = p3.executar_padrao(P, citra, Path("."), trab, chamar=f)
    assert r["padrao_001"]["ok"] == 2 and r["padrao_001"]["pendentes"] == 1      # c: 2 tentativas com evidência
    r = p3.executar_padrao(P, citra, Path("."), trab, chamar=f)
    assert r["padrao_001"]["esgotadas"] == 1 and r["padrao_001"]["chamadas_agora"] == 1
    r = p3.executar_padrao(P, citra, Path("."), trab, chamar=f)                  # nada mais a fazer
    assert r["padrao_001"]["chamadas_agora"] == 0
    log = [json.loads(l) for l in (trab / p3.LOG).read_text().splitlines()]
    assert [e["tentativa"] for e in log if e["nome"] == "c"] == [1, 2, 3]
    assert [e["resultado"] for e in log if e["nome"] == "c"] == ["sem_registro", "sem_registro", "started"]


def test_registros_antigos_contam_como_tentativa(tmp_path):
    P, citra, trab = montar(tmp_path, ["x"])
    for k, st in enumerate(["started", "error"]):           # duas chamadas do v2 sem sucesso
        d = trab / "saidas" / "padrao_001" / f"2026-11-26_0{k}"; d.mkdir(parents=True)
        (d / "AUG_x.json").write_text(json.dumps({"image": "x.png", "status": st, "error": "ReadTimeout()"}))
    f = Falso({"x": ["started"]})
    p3.executar_padrao(P, citra, Path("."), trab, chamar=f)
    assert len(f.cmds) == 1                                   # só a 3ª
    assert p3.executar_padrao(P, citra, Path("."), trab, chamar=f)["padrao_001"]["esgotadas"] == 1


def test_tempo_limite_envia_sigint_e_o_processo_grava(tmp_path):
    marca = tmp_path / "gravou"
    prog = f"import time,pathlib\ntry:\n    time.sleep(30)\nexcept KeyboardInterrupt:\n    pathlib.Path({str(marca)!r}).write_text('started')\n"
    assert p3.rodar_com_limite([sys.executable, "-c", prog], str(tmp_path), 1) == "tempo_esgotado"
    assert marca.read_text() == "started"
    assert p3.rodar_com_limite([sys.executable, "-c", "pass"], str(tmp_path), 5) == "concluida"
