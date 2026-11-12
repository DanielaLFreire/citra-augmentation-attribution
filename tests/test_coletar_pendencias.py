import json
import zipfile

from scripts.coletar_pendencias import coletar


def test_coletar(tmp_path):
    z = tmp_path / "z"
    z.mkdir()
    with zipfile.ZipFile(z / "seaship.zip", "w") as f:
        f.writestr("SeaShip/train.csv", "image,xmin\n001.jpg,1\n001.jpg,2\n002.jpg,3\n")
        f.writestr("SeaShip/train_images/001.jpg", b"x")
    with zipfile.ZipFile(z / "ABOships.zip", "w") as f:
        f.writestr("D/Labels/Vesibussi_Labels.csv", "filename,xmin\na1,1\na1,2\n")
        f.writestr("D/Seaships/x/a1.png", b"x")
        f.writestr("D/Seaships/x/a2.png", b"x")
    with zipfile.ZipFile(z / "genship3d-mirror.zip", "w") as f:
        f.writestr("G/audit_report.json", "{}")
    with zipfile.ZipFile(z / "dataset_25k_v2.zip", "w") as f:
        f.writestr("d/reconstrucao_report.json", "{}")
    out = tmp_path / "out"
    r = coletar(z, out)
    assert r["seaship.zip"]["train.csv"]["n_nomes_distintos"] == 2
    assert r["ABOships.zip"]["n_imagens_sem_linha_no_csv"] == 1
    assert (out / "audit_report.json").exists() and (out / "reconstrucao_report.json").exists()
    assert (tmp_path / "out.zip").exists()
    assert json.loads((out / "resumo_pendencias.json").read_text())
