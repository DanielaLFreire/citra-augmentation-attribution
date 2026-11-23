"""Avaliação final, versão 2: o mesmo procedimento de `avaliar_teste.py` (v1, reutilizado sem alteração: medidas, condições do teste,
lacre) mais **a gravação das predições por imagem**, para que toda análise posterior (por dia, por subconjunto, por caixa,
intervalos de bootstrap) seja feita offline sobre as predições e o teste NÃO precise ser avaliado de novo.

Por que existe: a v1 foi registrada (D55) antes de eu perceber que as análises de sensibilidade pré-registradas (adendo 4b) pedem
medidas por subconjunto; a v1 não grava predições. A v1 fica intacta e continua sendo importada; só esta v2 é usada no teste.

Cada modelo grava `<pasta_predicoes>/<id_execucao>.npz` com, por imagem: nome, largura, altura, predições (xyxy em pixels
originais, confiança, conf >= 0,001) e caixas de referência. O .npz fica no Drive (não entra no repositório público); o SHA-256 de cada
um vai na coluna `sha256_predicoes` do CSV de saída.

Uso (igual ao da v1, mais --pasta-predicoes):
  python -m scripts.avaliar_teste_v2 --split val --exigir-condicoes --lacre /content/lacre_ensaio.json --bracos C R --sem-4a-decisao Dnn \\
      --raiz <CITRA-3D-Real> --divisao <divisao.csv> --pasta-predicoes <pasta nova> --saida <csv novo>
  python -m scripts.avaliar_teste_v2 --split test --bracos C R ... (só depois das condições do adendo)
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from scripts import avaliar_teste as v1
from scripts._hashes import HASHES, carregar, sha256

COLUNAS = v1.COLUNAS + ["sha256_predicoes"]


def salvar_predicoes(caminho: Path, nomes: list[str], itens: list[dict]) -> None:
    """Grava predições e caixas de referência de todas as imagens num único .npz (formato achatado com deslocamentos)."""
    pred = [np.asarray(i["pred_xyxy"], dtype=np.float32).reshape(-1, 4) for i in itens]
    conf = [np.asarray(i["pred_conf"], dtype=np.float32).reshape(-1) for i in itens]
    gt = [np.asarray(i["gt_xyxy"], dtype=np.float32).reshape(-1, 4) for i in itens]
    desloc = lambda l: np.concatenate(([0], np.cumsum([len(x) for x in l]))).astype(np.int64)  # noqa: E731
    np.savez_compressed(
        caminho, nomes=np.array(nomes), largura=np.array([i["largura"] for i in itens]),
        altura=np.array([i["altura"] for i in itens]), pred=np.concatenate(pred) if pred else np.zeros((0, 4), np.float32),
        conf=np.concatenate(conf) if conf else np.zeros(0, np.float32), desloc_pred=desloc(pred),
        gt=np.concatenate(gt) if gt else np.zeros((0, 4), np.float32), desloc_gt=desloc(gt))


def carregar_predicoes(caminho: Path) -> list[dict]:
    z = np.load(caminho, allow_pickle=False)
    dp, dg = z["desloc_pred"], z["desloc_gt"]
    return [{"nome": str(z["nomes"][k]), "largura": int(z["largura"][k]), "altura": int(z["altura"][k]),
             "pred_xyxy": z["pred"][dp[k]:dp[k + 1]].astype(float), "pred_conf": z["conf"][dp[k]:dp[k + 1]].astype(float),
             "gt_xyxy": z["gt"][dg[k]:dg[k + 1]].astype(float)} for k in range(len(z["nomes"]))]


def avaliar_modelo(pesos: Path, data_yaml: Path, imagens: list[Path], split: str, destino_pred: Path) -> dict:
    from ultralytics import YOLO

    modelo = YOLO(str(pesos))
    r = modelo.val(data=str(data_yaml), split=split, imgsz=v1.IMGSZ, conf=v1.CONF_VAL, iou=v1.IOU_NMS, max_det=v1.MAX_DET,
                   batch=v1.LOTE, plots=False, verbose=False)
    itens = []
    for img, res in zip(imagens, modelo.predict(source=[str(p) for p in imagens], imgsz=v1.IMGSZ, conf=v1.CONF_VAL, iou=v1.IOU_NMS,
                                                max_det=v1.MAX_DET, batch=v1.LOTE, stream=True, verbose=False)):
        alt, larg = res.orig_shape
        itens.append({"pred_xyxy": res.boxes.xyxy.cpu().numpy(), "pred_conf": res.boxes.conf.cpu().numpy(),
                      "gt_xyxy": v1.ler_rotulo_yolo(img.parent.parent / "labels" / f"{img.stem}.txt", larg, alt),
                      "largura": larg, "altura": alt})
    salvar_predicoes(destino_pred, [p.stem for p in imagens], itens)
    m = v1.medidas_proprias(itens)
    m.update({"mAP50_ultralytics": float(r.box.map50), "n_imagens": len(imagens), "sha256_predicoes": sha256(destino_pred)})
    return m


def principal(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--split", required=True, choices=["val", "test"])
    p.add_argument("--raiz", required=True)
    p.add_argument("--divisao", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--pasta-predicoes", required=True)
    p.add_argument("--bracos", nargs="*", default=[])
    p.add_argument("--sem-4a-decisao", default=None)
    p.add_argument("--trabalho", default="/content/trabalho_aval")
    p.add_argument("--exigir-condicoes", action="store_true")
    p.add_argument("--lacre", default=str(v1.LACRE))
    a = p.parse_args(argv)
    import torch
    import ultralytics

    if ultralytics.__version__ != v1.VERSAO_ULTRALYTICS:
        raise SystemExit(f"Ultralytics {ultralytics.__version__} != {v1.VERSAO_ULTRALYTICS}")
    if not torch.cuda.is_available():
        raise SystemExit("sem GPU")
    lacre = Path(a.lacre)
    if a.split == "test" and lacre.resolve() != v1.LACRE.resolve():
        raise SystemExit("no split test o lacre é sempre " + str(v1.LACRE))
    if not a.bracos:
        raise SystemExit("--bracos é obrigatório")
    if a.split == "test" or a.exigir_condicoes:
        v1._commit_limpo()
        linhas = v1.verificar_condicoes_teste(v1.ler_registro(), carregar(HASHES), Path(__file__), a.bracos, lacre, a.sem_4a_decisao)
    else:
        linhas = [r for r in v1.ler_registro() if r["braco"] in a.bracos and "_principal_" in r["id_execucao"]]
    saida, pasta = Path(a.saida), Path(a.pasta_predicoes)
    if saida.exists() or pasta.exists():
        raise SystemExit("--saida e --pasta-predicoes não podem existir")
    pasta.mkdir(parents=True)
    data_yaml, imagens = v1.montar_split(a.split, Path(a.divisao), Path(a.raiz), Path(a.trabalho))
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader()
        for r in linhas:
            m = avaliar_modelo(Path(r["caminho_pesos"]), data_yaml, imagens, a.split, pasta / f"{r['id_execucao']}.npz")
            m.update({"id_execucao": r["id_execucao"], "split": a.split, "sha256_pesos": r["sha256_pesos"]})
            w.writerow({k: m[k] for k in COLUNAS})
            f.flush()
            print(json.dumps({k: m[k] for k in COLUNAS}, ensure_ascii=False))
    if a.split == "test" or a.exigir_condicoes:
        lacre.write_text(json.dumps({"avaliado_em": datetime.now(timezone.utc).isoformat(), "split": a.split, "saida": str(saida),
                                     "predicoes": str(pasta), "n_modelos": len(linhas)}, indent=2) + "\n", encoding="utf-8")
        print("LACRE escrito:", lacre)


if __name__ == "__main__":
    principal()
