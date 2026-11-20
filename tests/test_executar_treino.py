import csv
import json
from pathlib import Path

import pytest

from scripts.executar_treino import (argumentos_treino, COLUNAS, REGISTRO, anexar_registro, argumentos, carregar_config, conferir_listas,
                                     linha_registro, preparar_dados, verificar_registrado)


def lista(tmp_path, linhas):
    f = tmp_path / "lista.csv"
    with open(f, "w", newline="") as h:
        w = csv.writer(h)
        w.writerow(["ordem", "id_imagem", "fonte", "copia"])
        for k, (i, fonte, c) in enumerate(linhas, 1):
            w.writerow([k, i, fonte, c])
    return f


def raiz_falsa(tmp_path, nomes):
    raiz = tmp_path / "raiz"
    (raiz / "train/images").mkdir(parents=True)
    (raiz / "train/labels_final").mkdir(parents=True)
    for n in nomes:
        (raiz / f"train/images/{n}.png").write_bytes(n.encode())
        (raiz / f"train/labels_final/{n}.txt").write_text("0 0.5 0.5 0.1 0.1\n")
    return raiz


DIV = {"train": {"a", "b"}, "val": {"v"}, "test": {"t"}}


def test_colunas_iguais_as_do_registro_do_repositorio():
    cabecalho = REGISTRO.read_text(encoding="utf-8").splitlines()[0].split(",")
    assert cabecalho == COLUNAS


def test_linha_registro_exige_todas_as_colunas():
    with pytest.raises(KeyError):
        linha_registro(id_execucao="x")


def test_verificar_registrado(tmp_path):
    f = tmp_path / "cfg.yaml"
    f.write_text("epochs: 37\n")
    import hashlib
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    reg = tmp_path / "hashes.json"
    reg.write_text(json.dumps({"artefatos": {"cfg.yaml": {"sha256": h}}}))
    assert verificar_registrado(f, reg) == h
    f.write_text("epochs: 38\n")
    with pytest.raises(ValueError, match="difere"):
        verificar_registrado(f, reg)
    with pytest.raises(ValueError, match="não tem hash"):
        verificar_registrado(tmp_path / "outro.yaml", reg)


def test_conferir_listas_recusa_id_fora_do_treino():
    conferir_listas({"a"}, DIV)
    with pytest.raises(ValueError, match="não estão no treino"):
        conferir_listas({"a", "t"}, DIV)
    with pytest.raises(ValueError, match="mais de um split"):
        conferir_listas({"a"}, {"train": {"a"}, "val": {"a"}, "test": set()})


def test_preparar_dados_copia_unicas_repete_linhas_e_nao_copia_teste(tmp_path):
    raiz = raiz_falsa(tmp_path, ["a", "b", "v", "t"])
    f = lista(tmp_path, [("a", "citra", 1), ("a", "citra", 2), ("b", "citra", 1), ("b", "citra_extra", 1)])
    d = preparar_dados(f, DIV, raiz, tmp_path / "local")
    assert d["linhas_treino"] == 4 and d["imagens_unicas_treino"] == 2 and d["imagens_val"] == 1
    assert d["fracao"] == 0.25 and d["fonte_externa"] == "citra_extra"
    assert len((tmp_path / "local/train.txt").read_text().split()) == 4
    assert not (tmp_path / "local/images/t.png").exists()
    assert (tmp_path / "local/images/v.png").exists()
    assert not (tmp_path / "local/images/a.png").is_symlink()


def test_preparar_dados_externas_precisa_do_mapa(tmp_path):
    raiz = raiz_falsa(tmp_path, ["a", "v"])
    f = lista(tmp_path, [("a", "citra", 1), ("e1", "iflens", 1)])
    with pytest.raises(FileNotFoundError, match="mapa"):
        preparar_dados(f, DIV, raiz, tmp_path / "local")
    img, rot = tmp_path / "e1.png", tmp_path / "e1.txt"
    img.write_bytes(b"e")
    rot.write_text("0 0.5 0.5 0.1 0.1\n")
    d = preparar_dados(f, DIV, raiz, tmp_path / "local2", {"e1": (img, rot)})
    assert d["fonte_externa"] == "iflens" and d["fracao"] == 0.5


def test_anexar_registro_e_duplicata(tmp_path):
    reg = tmp_path / "r.csv"
    linha = {c: "x" for c in COLUNAS}
    anexar_registro(linha, reg)
    assert reg.read_text().splitlines()[0].split(",") == COLUNAS
    with pytest.raises(ValueError, match="já está"):
        anexar_registro(linha, reg)
    anexar_registro({**linha, "id_execucao": "y"}, reg)
    assert len(reg.read_text().strip().splitlines()) == 3


def test_config_do_repositorio_e_argumentos():
    raiz = Path(__file__).resolve().parent.parent
    cfg = carregar_config(raiz / "configs/treino_yolo11n_d43.yaml")
    assert cfg["epochs"] == 37 and cfg["optimizer"] == "AdamW" and cfg["close_mosaic"] == 2 and cfg["batch"] == 16
    for k in ("data", "project", "name", "seed"):
        assert k not in cfg
    a = argumentos(["--braco", "C", "--plano", "principal", "--lista", "l", "--config", "c", "--divisao", "d",
                    "--raiz", "r", "--seed", "42", "--destino", "x"])
    assert a.seed == 42 and a.modelo == "yolo11n.pt"


def test_argumentos_treino_sem_chave_duplicada_e_sem_model():
    cfg = {"model": "yolo11n.pt", "epochs": 37, "exist_ok": True, "batch": 16, "plots": True}

    def treino(**kw):  # imita Model.train: um TypeError se alguma chave vier duas vezes
        return kw

    r = treino(**argumentos_treino(cfg, "d.yaml", "p", "n", 42))
    assert r["data"] == "d.yaml" and r["seed"] == 42 and r["exist_ok"] is True and "model" not in r
    assert r["epochs"] == 37
    f = argumentos_treino(cfg, "d.yaml", "p", "n", 42, fumaca=True)
    assert f["epochs"] == 1 and f["fraction"] == 0.02 and f["plots"] is False
    assert cfg["epochs"] == 37  # não altera a configuração original


def test_argumentos_com_a_config_real_do_repositorio():
    raiz = Path(__file__).resolve().parent.parent
    for nome in ("treino_yolo11n_d43.yaml", "treino_yolo11n_f5_reproducao.yaml"):
        cfg = carregar_config(raiz / "configs" / nome)
        a = argumentos_treino(cfg, "d.yaml", "p", "n", 1)
        assert list(a).count("exist_ok") == 1 and "model" not in a
    assert argumentos(["--braco", "C", "--plano", "principal", "--lista", "l", "--config", "c", "--divisao", "d",
                       "--raiz", "r", "--seed", "1", "--destino", "x", "--fumaca"]).fumaca is True
