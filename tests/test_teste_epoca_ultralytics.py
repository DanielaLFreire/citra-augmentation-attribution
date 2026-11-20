import pytest

from scripts.teste_epoca_ultralytics import ler_lista, montar


def cenario(tmp_path):
    raiz = tmp_path / "raiz"
    for split in ("train", "val"):
        (raiz / split / "images").mkdir(parents=True)
        (raiz / split / "labels_final").mkdir(parents=True)
    (raiz / "train/images/a.png").write_bytes(b"x")
    (raiz / "val/images/b.png").write_bytes(b"y")
    (raiz / "train/labels_final/a.txt").write_text("0 0.5 0.5 0.1 0.1\n")
    (raiz / "val/labels_final/b.txt").write_text("0 0.2 0.2 0.1 0.1\n")
    return raiz


def indice(raiz):
    from scripts.teste_epoca_ultralytics import indexar
    return indexar(raiz)


def test_ler_lista(tmp_path):
    f = tmp_path / "l.csv"
    f.write_text("ordem,id_imagem,fonte,copia\n1,a,citra,1\n2,a,citra,2\n")
    assert ler_lista(f) == [("a", 1), ("a", 2)]


def test_montar_repete_linhas_e_acha_imagem_em_qualquer_split(tmp_path):
    raiz = cenario(tmp_path)
    imagens, rotulos = indice(raiz)
    caminhos = montar([("a", 1), ("a", 2), ("b", 1)], imagens, rotulos, tmp_path / "w")
    assert len(caminhos) == 3 and caminhos[0] == caminhos[1] != caminhos[2]
    assert (tmp_path / "w/labels/a.txt").read_text().startswith("0 0.5")
    assert (tmp_path / "w/labels/b.txt").exists()


def test_copias_fisicas_nomes_unicos(tmp_path):
    raiz = cenario(tmp_path)
    imagens, rotulos = indice(raiz)
    caminhos = montar([("a", 1), ("a", 2)], imagens, rotulos, tmp_path / "w", copias_fisicas=True)
    assert len(set(caminhos)) == 2
    assert (tmp_path / "w/labels/a__c2.txt").exists()


def test_falta_rotulo(tmp_path):
    raiz = cenario(tmp_path)
    imagens, rotulos = indice(raiz)
    with pytest.raises(FileNotFoundError):
        montar([("a", 1), ("zzz", 1)], imagens, rotulos, tmp_path / "w")


def test_nao_toca_na_raiz(tmp_path):
    raiz = cenario(tmp_path)
    antes = sorted(str(p) for p in raiz.rglob("*"))
    imagens, rotulos = indice(raiz)
    montar([("a", 1)], imagens, rotulos, tmp_path / "w")
    assert sorted(str(p) for p in raiz.rglob("*")) == antes
