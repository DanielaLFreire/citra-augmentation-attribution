import json
import hashlib

import pytest

from scripts.lacrar_adendo import lacrar_adendo
from scripts.registrar_artefato import registrar_artefato
from scripts.verificar_integridade import verificar


def test_registrar_nao_altera_existentes_e_recusa_duplicata(tmp_path):
    h = tmp_path / "hashes.json"
    h.write_text(json.dumps({"artefatos": {"a": {"sha256": "x"}}, "adendos": {"d": {"sha256": "y"}}}))
    f = tmp_path / "m.csv"
    f.write_text("a,b\n1,2\n")
    e = registrar_artefato(f, h)
    novo = json.loads(h.read_text())
    assert novo["artefatos"]["a"] == {"sha256": "x"} and novo["adendos"]["d"] == {"sha256": "y"}
    assert e["sha256"] == hashlib.sha256(f.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="já está registrado"):
        registrar_artefato(f, h)


def test_registrar_arquivo_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        registrar_artefato(tmp_path / "x", tmp_path / "h.json")


def test_lacrar_recusa_pendente_e_relacracao(tmp_path):
    h = tmp_path / "hashes.json"
    ad = tmp_path / "adendo.md"
    ad.write_text("margem = ___\n")
    with pytest.raises(ValueError, match="pendente"):
        lacrar_adendo(ad, h)
    ad.write_text("margem = 1 pp\n")
    lacrar_adendo(ad, h)
    with pytest.raises(ValueError, match="já está lacrado"):
        lacrar_adendo(ad, h)


def test_verificar_detecta_alteracao(tmp_path):
    (tmp_path / "docs/pre_registro").mkdir(parents=True)
    (tmp_path / "data").mkdir()
    h = tmp_path / "docs/pre_registro/hashes.json"
    f = tmp_path / "m.csv"
    f.write_text("1\n")
    h.write_text(json.dumps({"artefatos": {"m.csv": {"caminho": "m.csv", "sha256": hashlib.sha256(b"1\n").hexdigest()}}}))
    assert verificar(h, tmp_path) == []
    f.write_text("2\n")
    assert len(verificar(h, tmp_path)) == 1
    f.unlink()
    assert "ausente" in verificar(h, tmp_path)[0]
