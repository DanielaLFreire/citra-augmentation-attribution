import csv
import json

import pytest

from scripts import sortear_amostra_4a as s


def _nomes(n_blocos=200, por_bloco=3):
    nomes = []
    for b in range(n_blocos):
        dia = 1 + b // 40
        hora = 8 + (b // 6) % 10
        dez = b % 6
        for k in range(por_bloco):
            nomes.append(f"{dia:02d}.05.2022-{hora:02d}-{dez}{k}-{10 + k:02d}")
    return nomes


def test_bloco_usa_data_hora_e_dezena_de_minutos():
    assert s.bloco("07.07.2022-09-39-44") == "07.07.2022-09-3"
    assert s.bloco("07.07.2022-09-40-32") == "07.07.2022-09-4"
    assert s.bloco("07.07.2022-09-00-05") == "07.07.2022-09-0"


def test_sorteio_deterministico_e_uma_imagem_por_bloco():
    pool = _nomes()
    a = s.sortear(pool, semente=1, n=50, n_risco=10)
    b = s.sortear(list(reversed(pool)), semente=1, n=50, n_risco=10)
    assert a == b
    assert len(a) == 50
    assert len({r["bloco"] for r in a}) == 50
    assert sum(r["estrato"] == "risco" for r in a) == 10
    assert all(r["nome"] in pool for r in a)
    assert s.sortear(pool, semente=2, n=50, n_risco=10) != a


def test_fallback_com_menos_blocos_que_o_tamanho():
    pool = _nomes(n_blocos=20, por_bloco=5)  # 20 blocos, 100 imagens
    r = s.sortear(pool, semente=3, n=40, n_risco=8)
    assert len(r) == 40 and len({x["nome"] for x in r}) == 40
    assert {x["bloco"] for x in r} == {s.bloco(n) for n in pool}  # todos os blocos aparecem
    assert sum(x["estrato"] == "risco" for x in r) == 8


def test_pool_pequeno_demais_falha():
    with pytest.raises(ValueError):
        s.sortear(_nomes(2, 2), n=10, n_risco=2)


def test_lista_elegivel_filtra_quarentena_caixas_e_split(tmp_path):
    div2 = tmp_path / "div2.csv"
    ok = [("01.01.2022-10-05-01", "01.01.2022", "train"), ("11.05.2022-14-13-13", "11.05.2022", "train"),
          ("01.01.2022-10-15-01", "01.01.2022", "train"), ("02.01.2022-10-05-01", "02.01.2022", "val"),
          ("03.01.2022-10-05-01", "03.01.2022", "train")]
    with open(div2, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["nome", "dia", "divisao"]); w.writerows(ok)
    caixas = {"01.01.2022-10-05-01": 2, "11.05.2022-14-13-13": 1, "01.01.2022-10-15-01": 0,
              "02.01.2022-10-05-01": 3, "03.01.2022-10-05-01": 1}
    el = s.lista_elegivel(div2, caixas)
    assert [r["nome"] for r in el] == ["01.01.2022-10-05-01", "03.01.2022-10-05-01"]
    assert el[0]["bloco"] == "01.01.2022-10-0" and el[0]["n_caixas"] == 2


def test_cli_recusa_sobrescrever_e_hash_divergente(tmp_path):
    lista, amostra = tmp_path / "l.csv", tmp_path / "a.csv"
    lista.write_text("x")
    assert s.principal(["--saida-lista", str(lista), "--saida-amostra", str(amostra)]) == 2
    lista.unlink()
    outra = tmp_path / "div.csv"
    outra.write_text("nome,dia,divisao\n")
    assert s.principal(["--saida-lista", str(lista), "--saida-amostra", str(amostra), "--divisao", str(outra)]) == 2
    assert not lista.exists() and not amostra.exists()


def test_execucao_real_com_dados_do_repositorio(tmp_path):
    """Ensaio com semente diferente da oficial: confere contagens e restrições, sem produzir a amostra oficial."""
    lista, amostra = tmp_path / "l.csv", tmp_path / "a.csv"
    assert s.principal(["--saida-lista", str(lista), "--saida-amostra", str(amostra), "--semente", "1"]) == 0
    rel = json.loads((tmp_path / "a.csv.relatorio.json").read_text(encoding="utf-8"))
    assert rel["amostra"]["n_imagens"] == 150 and rel["amostra"]["n_blocos"] == 150
    assert rel["amostra"]["por_estrato"] == {"padrao": 120, "risco": 30}
    piloto = s.ler_piloto(s.CHAVE_PILOTO)
    nomes = {r["nome"] for r in csv.DictReader(open(amostra, encoding="utf-8"))}
    assert not (nomes & piloto) and not (nomes & set(s.QUARENTENA_D10))
