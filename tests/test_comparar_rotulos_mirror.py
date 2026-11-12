import zipfile

from scripts.comparar_rotulos_mirror import comparar


def test_comparar(tmp_path):
    d = tmp_path / "raiz" / "train" / "labels_final"
    d.mkdir(parents=True)
    (d / "a.txt").write_text("0 0.5 0.5 0.1 0.1\n")
    (d / "b.txt").write_text("0 0.2 0.2 0.1 0.1\n")
    zp = tmp_path / "m.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("M/navio/labels/a.txt", "3 0.5 0.5 0.1 0.1\r\n")
        z.writestr("M/navio/labels/b.txt", "3 0.9 0.9 0.1 0.1\r\n")
        z.writestr("M/navio/labels/c.txt", "3 0.9 0.9 0.1 0.1\r\n")
    r = comparar(zp, tmp_path / "raiz", tmp_path / "out")
    assert r["labels"]["igual"] == 1 and r["labels"]["difere"] == 1 and r["labels"]["so_no_espelho"] == 1
