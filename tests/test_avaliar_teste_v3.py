import pytest

from scripts import avaliar_teste as v1
from scripts import avaliar_teste_v3 as v3
from scripts._hashes import sha256


def _cenario(tmp_path, bracos_extras=(), gpu_l4="NVIDIA L4"):
    aval = tmp_path / "avaliar_teste_v3.py"
    aval.write_text("# v3\n", encoding="utf-8")
    registro = []

    def linha(i, gpu="NVIDIA L4"):
        w = tmp_path / f"{i}.pt"
        w.write_bytes(i.encode())
        registro.append({"id_execucao": i, "caminho_pesos": str(w), "sha256_pesos": sha256(w), "avaliado_teste": "nao", "gpu": gpu})

    for b in ("C", "R") + tuple(bracos_extras):
        for s in v1.SEMENTES:
            linha(f"{b}_principal_yolo11n_seed{s}")
    for i in v3.ids_replica_L4():
        linha(i, gpu_l4)
    hashes = {"artefatos": {"avaliar_teste_v3.py": {"sha256": sha256(aval)}},
              "adendos": {"adendo4_fontes_aumento.md": {}, "adendo4a_fidelidade_iflens.md": {}}}
    return aval, registro, hashes


def test_ids_replica():
    assert v3.ids_replica_L4() == [f"C_principalL4_yolo11n_seed{s}" for s in (7, 42, 123, 2024, 31415)]


def test_etapa1_seleciona_25(tmp_path):
    aval, registro, hashes = _cenario(tmp_path)
    linhas = v3.selecionar_modelos(1, registro, hashes, aval, lacre_etapa1=tmp_path / "l1.json")
    ids = [r["id_execucao"] for r in linhas]
    assert len(ids) == 25 and len(set(ids)) == 25 and ids[-1] == "C_principalL4_yolo11n_seed31415"
    assert sum(i.startswith("R_principal") for i in ids) == 10 and sum("principalL4" in i for i in ids) == 5


def test_etapa1_recusa_replica_ausente_fora_da_L4_ou_ja_avaliada(tmp_path):
    aval, registro, hashes = _cenario(tmp_path)
    l1 = tmp_path / "l1.json"
    with pytest.raises(ValueError, match="ausente do registro"):
        v3.selecionar_modelos(1, [r for r in registro if "principalL4_yolo11n_seed42" not in r["id_execucao"]], hashes, aval, lacre_etapa1=l1)
    aval2, reg2, h2 = _cenario(tmp_path, gpu_l4="NVIDIA A100-SXM4-80GB")
    with pytest.raises(ValueError, match="não foi treinado na L4"):
        v3.selecionar_modelos(1, reg2, h2, aval2, lacre_etapa1=l1)
    registro[-1]["avaliado_teste"] = "sim"
    with pytest.raises(ValueError, match="já consta"):
        v3.selecionar_modelos(1, registro, hashes, aval, lacre_etapa1=l1)
    registro[-1]["avaliado_teste"] = "nao"
    registro[-1]["sha256_pesos"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256"):
        v3.selecionar_modelos(1, registro, hashes, aval, lacre_etapa1=l1)


def test_etapa1_recusa_lacre_existente_e_avaliador_alterado(tmp_path):
    aval, registro, hashes = _cenario(tmp_path)
    l1 = tmp_path / "l1.json"
    l1.write_text("{}")
    with pytest.raises(ValueError, match="já foi avaliado"):
        v3.selecionar_modelos(1, registro, hashes, aval, lacre_etapa1=l1)
    l1.unlink()
    aval.write_text("# mudou\n")
    with pytest.raises(ValueError, match="alterado"):
        v3.selecionar_modelos(1, registro, hashes, aval, lacre_etapa1=l1)


def test_etapa2_exige_lacre_da_etapa1_e_bracos_validos(tmp_path):
    aval, registro, hashes = _cenario(tmp_path, bracos_extras=("E", "G"))
    l1, l2 = tmp_path / "l1.json", tmp_path / "l2.json"
    with pytest.raises(ValueError, match="estágio 1 ainda não"):
        v3.selecionar_modelos(2, registro, hashes, aval, ["E"], lacre_etapa1=l1, lacre_etapa2=l2)
    l1.write_text("{}")
    assert len(v3.selecionar_modelos(2, registro, hashes, aval, ["E"], lacre_etapa1=l1, lacre_etapa2=l2)) == 10
    assert len(v3.selecionar_modelos(2, registro, hashes, aval, None, lacre_etapa1=l1, lacre_etapa2=l2)) == 20
    with pytest.raises(ValueError, match="só os braços E e G"):
        v3.selecionar_modelos(2, registro, hashes, aval, ["R"], lacre_etapa1=l1, lacre_etapa2=l2)
    l2.write_text("{}")
    with pytest.raises(ValueError, match="já foi avaliado"):
        v3.selecionar_modelos(2, registro, hashes, aval, ["E"], lacre_etapa1=l1, lacre_etapa2=l2)
    with pytest.raises(ValueError, match="etapa deve ser"):
        v3.selecionar_modelos(3, registro, hashes, aval)
