"""Avaliação final, versão 3 (adendo 4b): estágios 1 e 2 do teste, com as réplicas de C na L4 e a verificação por código das condições.

Reutiliza o v2 (`avaliar_modelo`, que grava as predições por imagem) e o v1 (medidas, condições do adendo 4, lacre). Não altera nenhum deles.

  --etapa 1: avalia, numa única execução, os 20 modelos de C e R (10 sementes cada) e as 5 réplicas de C na L4 (plano `principalL4`,
             sementes 7, 42, 123, 2024 e 31415), 25 modelos no total. Lacre: runs/AVALIACAO_TESTE_LACRE.json.
  --etapa 2: avalia os braços E e/ou G (10 sementes cada), só depois de existir o lacre do estágio 1. Lacre próprio:
             runs/AVALIACAO_TESTE_LACRE_ETAPA2.json. Mesmo procedimento de medida.

No split de teste, antes de qualquer imagem, roda `verificar_condicoes_etapa1.verificar` (adendos, instrumentos, etiquetas, código limpo) e
as condições do v1; se algo falhar, não avalia. No split de validação (ensaio) só roda as condições do v1 e as das réplicas; com
`--verificar-documentos` roda também a verificação de adendos e instrumentos.

Uso (ensaio na validação, estágio 1):
  python -m scripts.avaliar_teste_v3 --etapa 1 --split val --lacre /content/lacre_ensaio3.json --sem-4a-decisao D54 \\
      --raiz <CITRA-3D-Real> --divisao <divisao.csv> --pasta-predicoes <pasta nova> --saida <csv novo>
Uso (teste): python -m scripts.avaliar_teste_v3 --etapa 1 --split test --raiz ... --divisao ... --pasta-predicoes ... --saida ...
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts import avaliar_teste as v1
from scripts import avaliar_teste_v2 as v2
from scripts._hashes import HASHES, RAIZ, carregar

COLUNAS = v2.COLUNAS
LACRE_ETAPA1 = v1.LACRE
LACRE_ETAPA2 = RAIZ / "runs" / "AVALIACAO_TESTE_LACRE_ETAPA2.json"
PLANO_L4 = "principalL4"
SEMENTES_L4 = [7, 42, 123, 2024, 31415]


def ids_replica_L4() -> list[str]:
    return [f"C_{PLANO_L4}_{v1.MODELO}_seed{s}" for s in SEMENTES_L4]


def verificar_replica_L4(registro: list[dict]) -> list[dict]:
    """As 5 réplicas de C na L4 devem estar no registro, na L4, com pesos íntegros e ainda não avaliadas no teste."""
    por_id = {r["id_execucao"]: r for r in registro}
    escolhidas = []
    for i in ids_replica_L4():
        if i not in por_id:
            raise ValueError(f"réplica de C na L4 ausente do registro: {i}")
        r = por_id[i]
        if "L4" not in r.get("gpu", ""):
            raise ValueError(f"{i} não foi treinado na L4 (gpu: {r.get('gpu')})")
        if r.get("avaliado_teste", "").strip().lower() != "nao":
            raise ValueError(f"{i} já consta como avaliado no teste")
        p = Path(r["caminho_pesos"])
        if not p.exists():
            raise ValueError(f"pesos ausentes: {p}")
        if v1.sha256(p) != r["sha256_pesos"]:
            raise ValueError(f"{i}: SHA-256 dos pesos difere do registro")
        escolhidas.append(r)
    return escolhidas


def selecionar_modelos(etapa: int, registro: list[dict], hashes: dict, avaliador: Path, bracos: list[str] | None = None,
                       sem_4a_decisao: str | None = None, lacre_etapa1: Path = LACRE_ETAPA1, lacre_etapa2: Path = LACRE_ETAPA2,
                       decisoes_md: Path = v1.DECISOES) -> list[dict]:
    """Linhas do registro a avaliar na etapa, na ordem. Levanta ValueError se alguma condição não vale."""
    if etapa == 1:
        linhas = v1.verificar_condicoes_teste(registro, hashes, avaliador, ["C", "R"], lacre_etapa1, sem_4a_decisao, decisoes_md)
        return linhas + verificar_replica_L4(registro)
    if etapa == 2:
        if not Path(lacre_etapa1).exists():
            raise ValueError("o estágio 1 ainda não foi avaliado (falta o lacre do estágio 1)")
        bracos = bracos or ["E", "G"]
        if any(b not in ("E", "G") for b in bracos):
            raise ValueError("o estágio 2 avalia só os braços E e G")
        return v1.verificar_condicoes_teste(registro, hashes, avaliador, bracos, lacre_etapa2, sem_4a_decisao, decisoes_md)
    raise ValueError("etapa deve ser 1 ou 2")


def principal(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--etapa", required=True, type=int, choices=[1, 2])
    p.add_argument("--split", required=True, choices=["val", "test"])
    p.add_argument("--raiz", required=True)
    p.add_argument("--divisao", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--pasta-predicoes", required=True)
    p.add_argument("--bracos", nargs="*", default=None, help="só na etapa 2: E e/ou G")
    p.add_argument("--sem-4a-decisao", default=None)
    p.add_argument("--dispensa", action="append", default=[], help="NOME_DO_ADENDO=Dnn (só vale depois de 30/12/2026)")
    p.add_argument("--trabalho", default="/content/trabalho_aval")
    p.add_argument("--verificar-documentos", action="store_true", help="na validação, roda também a verificação de adendos e instrumentos")
    p.add_argument("--lacre", default=None, help="só na validação (ensaio): onde gravar o lacre do ensaio")
    p.add_argument("--lacre-etapa1", default=None, help="só na validação (ensaio da etapa 2): lacre do ensaio da etapa 1")
    a = p.parse_args(argv)
    import torch
    import ultralytics

    if ultralytics.__version__ != v1.VERSAO_ULTRALYTICS:
        raise SystemExit(f"Ultralytics {ultralytics.__version__} != {v1.VERSAO_ULTRALYTICS}")
    if not torch.cuda.is_available():
        raise SystemExit("sem GPU")
    if a.etapa == 1 and a.bracos:
        raise SystemExit("--bracos só existe na etapa 2")
    teste = a.split == "test"
    if teste and (a.lacre or a.lacre_etapa1):
        raise SystemExit("no split test os lacres são sempre os fixados no código")
    if not teste and not a.lacre:
        raise SystemExit("no ensaio (val) informe --lacre para não tocar nos lacres do teste")
    if not teste and a.etapa == 2 and not a.lacre_etapa1:
        raise SystemExit("no ensaio da etapa 2 informe também --lacre-etapa1 (o lacre do ensaio da etapa 1)")
    if teste:
        l1, l2 = LACRE_ETAPA1, LACRE_ETAPA2
    else:
        l1, l2 = (Path(a.lacre), LACRE_ETAPA2) if a.etapa == 1 else (Path(a.lacre_etapa1), Path(a.lacre))
    lacre = l1 if a.etapa == 1 else l2
    if teste or a.verificar_documentos:
        from scripts import verificar_condicoes_etapa1 as vc

        res = vc.verificar({k: x for k, x in (d.split("=", 1) for d in a.dispensa)})
        if not res["ok"]:
            raise SystemExit("condições do estágio 1 não satisfeitas:\n- " + "\n- ".join(res["problemas"]))
    hashes = carregar(HASHES)
    if not teste and not a.verificar_documentos:
        # ensaio: o hash deste arquivo ainda pode não estar registrado; no teste a conferência real vale (e é testada)
        hashes.setdefault("artefatos", {})[Path(__file__).name] = {"sha256": v1.sha256(Path(__file__))}
    try:
        linhas = selecionar_modelos(a.etapa, v1.ler_registro(), hashes, Path(__file__), a.bracos, a.sem_4a_decisao, l1, l2)
    except ValueError as e:
        raise SystemExit(str(e))
    saida, pasta = Path(a.saida), Path(a.pasta_predicoes)
    if saida.exists() or pasta.exists():
        raise SystemExit("--saida e --pasta-predicoes não podem existir")
    pasta.mkdir(parents=True)
    data_yaml, imagens = v1.montar_split(a.split, Path(a.divisao), Path(a.raiz), Path(a.trabalho))
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader()
        for r in linhas:
            m = v2.avaliar_modelo(Path(r["caminho_pesos"]), data_yaml, imagens, a.split, pasta / f"{r['id_execucao']}.npz")
            m.update({"id_execucao": r["id_execucao"], "split": a.split, "sha256_pesos": r["sha256_pesos"]})
            w.writerow({k: m[k] for k in COLUNAS})
            f.flush()
            print(json.dumps({k: m[k] for k in COLUNAS}, ensure_ascii=False))
    lacre.write_text(json.dumps({"avaliado_em": datetime.now(timezone.utc).isoformat(), "etapa": a.etapa, "split": a.split,
                                 "saida": str(saida), "predicoes": str(pasta), "n_modelos": len(linhas)}, indent=2) + "\n",
                     encoding="utf-8")
    print("LACRE escrito:", lacre)


if __name__ == "__main__":
    principal()
