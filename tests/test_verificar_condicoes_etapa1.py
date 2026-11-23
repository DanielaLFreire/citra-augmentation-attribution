import subprocess
from datetime import date
from pathlib import Path

import pytest

from scripts import verificar_condicoes_etapa1 as v
from scripts._hashes import sha256


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _repo(tmp_path):
    raiz = tmp_path / "r"
    (raiz / "scripts").mkdir(parents=True)
    (raiz / "docs").mkdir()
    _git(raiz, "init", "-q")
    _git(raiz, "config", "user.email", "a@b.c")
    _git(raiz, "config", "user.name", "t")
    return raiz


def _hashes(raiz, adendos, instrumentos=True):
    h = {"artefatos": {}, "adendos": {}}
    if instrumentos:
        for n in v.INSTRUMENTOS:
            (raiz / "scripts" / n).write_text(f"# {n}\n")
            h["artefatos"][n] = {"sha256": sha256(raiz / "scripts" / n)}
    for n in adendos:
        (raiz / "docs" / n).write_text(f"adendo {n}\n")
        h["adendos"][n] = {"caminho": f"docs/{n}", "sha256": sha256(raiz / "docs" / n)}
    return h


def test_instrumentos(tmp_path):
    raiz = _repo(tmp_path)
    h = _hashes(raiz, [])
    assert v.verificar_instrumentos(h, raiz / "scripts") == []
    (raiz / "scripts" / "bootstrap_imagens.py").write_text("# mudou\n")
    del h["artefatos"]["analisar_hardware.py"]
    erros = v.verificar_instrumentos(h, raiz / "scripts")
    assert any("bootstrap_imagens.py: alterado" in e for e in erros) and any("analisar_hardware.py: sem hash" in e for e in erros)


def test_adendos_sempre_e_dispensa(tmp_path):
    raiz = _repo(tmp_path)
    dec = tmp_path / "DECISOES.md"
    dec.write_text("| D70 | x |\n", encoding="utf-8")
    h = _hashes(raiz, list(v.ADENDOS_SEMPRE))
    # 4a e 4c ausentes, sem dispensa
    assert len(v.verificar_adendos(h, {}, date(2026, 12, 1), dec, raiz)) == 2
    d = {"adendo4a_fidelidade_iflens.md": "D70", "adendo4c_genship.md": "D70"}
    # dispensa antes do prazo: recusada
    assert len(v.verificar_adendos(h, d, date(2026, 12, 30), dec, raiz)) == 2
    # depois do prazo e com decisão existente: aceita
    assert v.verificar_adendos(h, d, date(2026, 12, 31), dec, raiz) == []
    # decisão inexistente
    assert len(v.verificar_adendos(h, {**d, "adendo4c_genship.md": "D99"}, date(2026, 12, 31), dec, raiz)) == 1
    # adendo 4b ausente não tem dispensa
    h2 = _hashes(raiz, ["adendo4_fontes_aumento.md"])
    assert any("4b" in e or "adendo4b" in e for e in v.verificar_adendos(h2, d, date(2026, 12, 31), dec, raiz))
    # arquivo alterado depois do lacre
    (raiz / "docs" / "adendo4_fontes_aumento.md").write_text("alterado\n")
    assert any("difere do hash do lacre" in e for e in v.verificar_adendos(h, d, date(2026, 12, 31), dec, raiz))


def test_tags_e_codigo_limpo(tmp_path):
    raiz = _repo(tmp_path)
    h = _hashes(raiz, ["adendo4_fontes_aumento.md"], instrumentos=False)
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "x")
    assert any("falta a etiqueta" in e for e in v.verificar_tags(h, raiz))
    _git(raiz, "tag", "lacre-adendo4")
    assert v.verificar_tags(h, raiz) == []
    # etiqueta aponta para versão diferente da lacrada
    (raiz / "docs" / "adendo4_fontes_aumento.md").write_text("outra versão\n")
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "y")
    h["adendos"]["adendo4_fontes_aumento.md"]["sha256"] = sha256(raiz / "docs" / "adendo4_fontes_aumento.md")
    assert any("não aponta para a versão lacrada" in e for e in v.verificar_tags(h, raiz))
    commit, erros = v.verificar_codigo_limpo(raiz)
    assert len(commit) == 40 and erros == []
    (raiz / "docs" / "adendo4_fontes_aumento.md").write_text("sujo\n")
    assert v.verificar_codigo_limpo(raiz)[1]
