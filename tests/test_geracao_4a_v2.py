import random
import sys
from pathlib import Path

import pytest
import yaml

from scripts import geracao_4a_v2 as v2

IFLENS = Path("/home/claude/iflens")
pytestmark = pytest.mark.skipif(not (IFLENS / "conditions-citra.yaml").exists(), reason="iflens não disponível")


def test_variacao_so_entre_valores_de_risco(tmp_path):
    sys.path.insert(0, str(IFLENS))
    from iflens.schema.conditions import ConditionSchema, ImageConditions

    padrao = yaml.safe_load((IFLENS / "conditions-citra.yaml").read_text())
    risco = yaml.safe_load((IFLENS / "conditions-citra-risk.yaml").read_text())
    original = {"time_of_day": "dusk", "sky": "clear", "atmosphere": "haze"}
    esq = v2.montar_esquema(padrao, risco, original)
    arq = tmp_path / "e.yaml"
    arq.write_text(yaml.safe_dump(esq))
    schema = ConditionSchema.from_yaml(arq)
    cond = ImageConditions.from_dict(schema=schema, data=original)
    for s in range(50):
        var = cond.get_variation(keep=["planet"], rng=random.Random(s)).to_dict()
        assert var["time_of_day"] in risco["time_of_day"] and var["sky"] in risco["sky"] and var["atmosphere"] in risco["atmosphere"]
    # original igual a um valor de risco: é excluído da variação
    orig2 = {"time_of_day": "noon", "sky": "overcast", "atmosphere": "haze"}
    esq2 = v2.montar_esquema(padrao, risco, orig2)
    assert list(esq2["sky"]) == ["overcast"] and "haze" in esq2["atmosphere"]


def test_valor_original_desconhecido():
    with pytest.raises(ValueError):
        v2.montar_esquema({"sky": {"clear": "x"}}, {"sky": {"overcast": "y"}}, {"sky": "snow"})
