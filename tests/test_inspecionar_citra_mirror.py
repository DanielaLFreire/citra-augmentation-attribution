import zipfile

from scripts.inspecionar_citra_mirror import inspecionar


def test_inspecionar(tmp_path):
    raiz = tmp_path / "raiz" / "train"
    (raiz / "labels_final").mkdir(parents=True)
    (raiz / "images").mkdir()
    (raiz / "labels_final" / "a.txt").write_text("0 0.5 0.5 0.1 0.1\n")
    (raiz / "images" / "11.05.2022-14-13-13.png").write_bytes(b"x" * 100)
    zp = tmp_path / "m.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("M/train/labels_final/a.txt", "0 0.4 0.5 0.1 0.1\n")
        z.writestr("M/train/images/11.05.2022-14-13-13.png", b"y" * 41)
        z.writestr("M/audit_report.json", "{}")
    r = inspecionar(zp, tmp_path / "raiz", tmp_path / "out")
    assert r["alvo"][0]["bytes"] == 41
    assert r["comparacao_com_raiz"]["rotulo:difere"] == 1
    assert r["comparacao_com_raiz"]["imagem:difere_tamanho"] == 1
    assert (tmp_path / "out" / "audit_report.json").exists()
