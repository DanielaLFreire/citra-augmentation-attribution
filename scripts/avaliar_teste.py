"""Avaliação dos modelos finais (`last.pt`) na validação ou no teste, com o procedimento fixado no adendo 4, seção 5.

Procedimento (não muda): Ultralytics 8.4.165, 640 px, conf 0,001, iou 0,7, max_det 300, lote 16, classe única.
  - mAP50: `model.val(...).box.map50` da API do Ultralytics (métrica primária).
  - Medidas próprias sobre as mesmas predições (conf 0,001): AP50 próprio (conferência), recall de embarcações pequenas com
    confiança >= 0,25 e IoU 0,5, e AP50 do estrato small. Small = caixa com área < 32² px no tamanho de 640 (a imagem é
    reduzida pelo lado maior). Estrato small no estilo COCO: caixas de referência fora do estrato são ignoradas, e a
    predição que casa com uma delas, ou que não casa e não é small, é ignorada.
  - Casamento: guloso por confiança decrescente, uma predição por caixa de referência.

Modo `--split val`: sem restrições além da versão do Ultralytics; serve para testar o script e conferir contra os números do treino.
Modo `--split test`: só roda se TODAS as condições do adendo valem (verificar_condicoes_teste): hash deste script registrado e igual;
adendo 4a lacrado (ou decisão registrada que o dispensa, `--sem-4a-decisao Dnn`); lista de modelos completa (cada braço pedido com as
10 sementes do plano principal, pesos com o SHA-256 do registro, ainda não avaliados no teste); nenhum lacre de avaliação anterior.
Depois de avaliar, escreve o lacre (`runs/AVALIACAO_TESTE_LACRE.json`): o teste é avaliado uma vez.

Uso (Colab):
  python -m scripts.avaliar_teste --split val  --raiz <CITRA-3D-Real> --divisao <divisao.csv> --ids C_principal_yolo11n_seed42 --saida runs/aval_val.csv
  python -m scripts.avaliar_teste --split test --raiz <CITRA-3D-Real> --divisao <divisao.csv> --bracos C R --saida runs/AVALIACAO_TESTE.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

from scripts._hashes import HASHES, RAIZ, carregar, sha256

VERSAO_ULTRALYTICS = "8.4.165"
REGISTRO = RAIZ / "runs" / "REGISTRO_EXECUCOES.csv"
LACRE = RAIZ / "runs" / "AVALIACAO_TESTE_LACRE.json"
DECISOES = RAIZ / "docs" / "DECISOES.md"
SEMENTES = [7, 42, 123, 2024, 31415, 101, 1001, 2025, 4242, 27182]
MODELO = "yolo11n"
IMGSZ, CONF_VAL, IOU_NMS, MAX_DET, LOTE = 640, 0.001, 0.7, 300, 16
CONF_RECALL, IOU_ACERTO, LIMITE_SMALL = 0.25, 0.5, 32 ** 2
COLUNAS = ["id_execucao", "split", "mAP50_ultralytics", "AP50_propria", "recall_small_conf025", "AP50_small", "n_imagens",
           "n_caixas", "n_caixas_small", "sha256_pesos"]


# ---------------------------------------------------------------- medidas (sem GPU, testáveis)
def area_640(caixas_xyxy: np.ndarray, largura: int, altura: int) -> np.ndarray:
    """Área em px² da caixa no tamanho de 640 (redução pelo lado maior)."""
    esc = IMGSZ / max(largura, altura)
    caixas = np.asarray(caixas_xyxy, dtype=float).reshape(-1, 4)
    return (caixas[:, 2] - caixas[:, 0]) * (caixas[:, 3] - caixas[:, 1]) * esc * esc


def iou_matriz(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float).reshape(-1, 4)
    b = np.asarray(b, dtype=float).reshape(-1, 4)
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    iw = np.minimum(a[:, None, 2], b[None, :, 2]) - np.maximum(a[:, None, 0], b[None, :, 0])
    ih = np.minimum(a[:, None, 3], b[None, :, 3]) - np.maximum(a[:, None, 1], b[None, :, 1])
    inter = np.clip(iw, 0, None) * np.clip(ih, 0, None)
    aa = (a[:, 2] - a[:, 0]) * (a[:, 3] - a[:, 1])
    ab = (b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])
    return inter / (aa[:, None] + ab[None, :] - inter + 1e-12)


def casar_imagem(pred_xyxy, pred_conf, gt_xyxy, gt_ignorar, pred_ignorar_se_solta, iou_limiar=IOU_ACERTO):
    """Casamento guloso de uma imagem. Devolve (conf, tp, valida, gt_casado) por predição, em ordem de confiança decrescente.
    `valida` = False para predição ignorada (casou com caixa de referência ignorada, ou ficou solta e `pred_ignorar_se_solta`).
    `gt_casado[j]` = a caixa de referência j (não ignorada) foi casada."""
    pred_xyxy = np.asarray(pred_xyxy, dtype=float).reshape(-1, 4)
    gt_xyxy = np.asarray(gt_xyxy, dtype=float).reshape(-1, 4)
    pred_conf = np.asarray(pred_conf, dtype=float)
    gt_ignorar = np.asarray(gt_ignorar, dtype=bool)
    pred_ignorar_se_solta = np.asarray(pred_ignorar_se_solta, dtype=bool)
    ordem = np.argsort(-pred_conf, kind="stable")
    m = iou_matriz(pred_xyxy, gt_xyxy)
    usada = np.zeros(len(gt_xyxy), dtype=bool)
    tp = np.zeros(len(ordem), dtype=bool)
    valida = np.ones(len(ordem), dtype=bool)
    for k, i in enumerate(ordem):
        cand = np.where((~usada) & (m[i] >= iou_limiar))[0] if len(gt_xyxy) else np.array([], dtype=int)
        if len(cand) == 0:
            if pred_ignorar_se_solta[i]:
                valida[k] = False
            continue
        boas = cand[~gt_ignorar[cand]]
        escolha = boas[np.argmax(m[i, boas])] if len(boas) else cand[np.argmax(m[i, cand])]
        usada[escolha] = True
        if gt_ignorar[escolha]:
            valida[k] = False
        else:
            tp[k] = True
    casado = usada & ~gt_ignorar
    return pred_conf[ordem], tp, valida, casado


def ap_de_curva(conf: np.ndarray, tp: np.ndarray, n_ref: int) -> float:
    """AP com interpolação de 101 pontos (a mesma forma do Ultralytics). NaN se não há caixa de referência."""
    if n_ref == 0:
        return float("nan")
    ordem = np.argsort(-np.asarray(conf), kind="stable")
    tp = np.asarray(tp, dtype=float)[ordem]
    fp = 1.0 - tp
    tpc, fpc = np.cumsum(tp), np.cumsum(fp)
    rec = tpc / n_ref
    prec = tpc / np.maximum(tpc + fpc, 1e-12)
    mrec = np.concatenate(([0.0], rec, [1.0]))
    mpre = np.concatenate(([1.0], prec, [0.0]))
    mpre = np.flip(np.maximum.accumulate(np.flip(mpre)))
    x = np.linspace(0, 1, 101)
    integra = getattr(np, "trapezoid", None) or np.trapz
    return float(integra(np.interp(x, mrec, mpre), x))


def medidas_proprias(imagens: list[dict]) -> dict:
    """`imagens`: lista de dicts com pred_xyxy, pred_conf, gt_xyxy, largura, altura (pixels originais).
    Devolve AP50_propria, AP50_small, recall_small_conf025, n_caixas, n_caixas_small."""
    todas_conf, todas_tp, n_gt = [], [], 0
    s_conf, s_tp, n_small, acertos_small = [], [], 0, 0
    for im in imagens:
        pred = np.asarray(im["pred_xyxy"], dtype=float).reshape(-1, 4)
        conf = np.asarray(im["pred_conf"], dtype=float)
        gt = np.asarray(im["gt_xyxy"], dtype=float).reshape(-1, 4)
        a_gt = area_640(gt, im["largura"], im["altura"])
        a_pr = area_640(pred, im["largura"], im["altura"])
        gt_small = a_gt < LIMITE_SMALL
        pr_small = a_pr < LIMITE_SMALL
        n_gt += len(gt)
        c, t, v, _ = casar_imagem(pred, conf, gt, np.zeros(len(gt), bool), np.zeros(len(pred), bool))
        todas_conf.append(c)
        todas_tp.append(t)
        c2, t2, v2, casado = casar_imagem(pred, conf, gt, ~gt_small, ~pr_small)
        s_conf.append(c2[v2])
        s_tp.append(t2[v2])
        n_small += int(gt_small.sum())
        # recall small com confiança >= 0,25: casa só as predições nesse corte
        corte = conf >= CONF_RECALL
        _, _, _, casado25 = casar_imagem(pred[corte], conf[corte], gt, ~gt_small, ~pr_small[corte])
        acertos_small += int(casado25.sum())
    cat = lambda l, d: np.concatenate(l) if l else np.array([], dtype=d)  # noqa: E731
    return {
        "AP50_propria": ap_de_curva(cat(todas_conf, float), cat(todas_tp, bool), n_gt),
        "AP50_small": ap_de_curva(cat(s_conf, float), cat(s_tp, bool), n_small),
        "recall_small_conf025": (acertos_small / n_small) if n_small else float("nan"),
        "n_caixas": n_gt,
        "n_caixas_small": n_small,
    }


def ler_rotulo_yolo(caminho: Path, largura: int, altura: int) -> np.ndarray:
    """Rótulo YOLO normalizado (cls cx cy w h) -> caixas xyxy em pixels."""
    linhas = [l.split() for l in Path(caminho).read_text(encoding="utf-8").splitlines() if l.strip()]
    if not linhas:
        return np.zeros((0, 4))
    v = np.array([[float(x) for x in l[1:5]] for l in linhas])
    cx, cy, w, h = v[:, 0] * largura, v[:, 1] * altura, v[:, 2] * largura, v[:, 3] * altura
    return np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], axis=1)


# ---------------------------------------------------------------- condições do teste (testáveis)
def ler_registro(caminho: Path = REGISTRO) -> list[dict]:
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ids_principais(bracos: list[str], sementes: list[int] = SEMENTES) -> list[str]:
    return [f"{b}_principal_{MODELO}_seed{s}" for b in bracos for s in sementes]


def verificar_condicoes_teste(registro: list[dict], hashes: dict, avaliador: Path, bracos: list[str], lacre: Path,
                              sem_4a_decisao: str | None = None, decisoes_md: Path = DECISOES,
                              sementes: list[int] = SEMENTES) -> list[dict]:
    """Levanta ValueError se alguma condição do adendo 4 não vale. Devolve as linhas do registro a avaliar, na ordem."""
    if Path(lacre).exists():
        raise ValueError(f"o teste já foi avaliado ({Path(lacre).name} existe): só uma avaliação é permitida")
    if not bracos:
        raise ValueError("nenhum braço pedido")
    reg = hashes.get("artefatos", {}).get(Path(avaliador).name)
    if reg is None or reg["sha256"] != sha256(Path(avaliador)):
        raise ValueError(f"{Path(avaliador).name} sem hash registrado ou alterado depois do registro")
    if "adendo4_fontes_aumento.md" not in hashes.get("adendos", {}):
        raise ValueError("o adendo 4 não está lacrado")
    if "adendo4a_fidelidade_iflens.md" not in hashes.get("adendos", {}):
        if not sem_4a_decisao:
            raise ValueError("o adendo 4a não está lacrado e nenhuma decisão (--sem-4a-decisao) o dispensa")
        if not re.search(rf"^\| {re.escape(sem_4a_decisao)} \|", Path(decisoes_md).read_text(encoding="utf-8"), re.M):
            raise ValueError(f"a decisão {sem_4a_decisao} não existe em DECISOES.md")
    por_id = {r["id_execucao"]: r for r in registro}
    escolhidas = []
    for i in ids_principais(bracos, sementes):
        if i not in por_id:
            raise ValueError(f"execução ausente no registro: {i}")
        r = por_id[i]
        if r.get("avaliado_teste", "").strip().lower() != "nao":
            raise ValueError(f"{i} já consta como avaliado no teste")
        p = Path(r["caminho_pesos"])
        if not p.exists():
            raise ValueError(f"pesos ausentes: {p}")
        if sha256(p) != r["sha256_pesos"]:
            raise ValueError(f"{i}: SHA-256 dos pesos difere do registro")
        escolhidas.append(r)
    return escolhidas


# ---------------------------------------------------------------- execução (GPU)
def _commit_limpo() -> str:
    sujo = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", ".",
                           ":(exclude)runs/REGISTRO_EXECUCOES.csv"], capture_output=True, text=True, cwd=RAIZ).stdout.strip()
    if sujo:
        raise ValueError("o código tem alterações não commitadas:\n" + sujo)
    return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=RAIZ).stdout.strip()


def montar_split(split: str, divisao_csv: Path, raiz: Path, local: Path) -> tuple[Path, list[Path]]:
    """Copia imagens e rótulos do split para `local` e escreve data.yaml. Devolve (data.yaml, lista de imagens)."""
    import shutil

    from scripts.executar_treino import ler_divisao
    from scripts.teste_epoca_ultralytics import indexar

    nomes = sorted(ler_divisao(Path(divisao_csv))["test" if split == "test" else "val"])
    imagens, rotulos = indexar(Path(raiz))
    (local / "images").mkdir(parents=True, exist_ok=True)
    (local / "labels").mkdir(parents=True, exist_ok=True)
    caminhos = []
    for n in nomes:
        if n not in imagens or n not in rotulos:
            raise FileNotFoundError(f"sem imagem ou rótulo: {n}")
        d = local / "images" / f"{n}{imagens[n].suffix}"
        if not d.exists():
            shutil.copyfile(imagens[n], d)
            shutil.copyfile(rotulos[n], local / "labels" / f"{n}.txt")
        caminhos.append(d)
    lista = local / f"{split}.txt"
    lista.write_text("\n".join(map(str, caminhos)) + "\n", encoding="utf-8")
    yaml_ = local / "data.yaml"
    yaml_.write_text(f"path: {local}\ntrain: {lista}\nval: {lista}\ntest: {lista}\nnc: 1\nnames: ['embarcacao']\n", encoding="utf-8")
    return yaml_, caminhos


def avaliar_modelo(pesos: Path, data_yaml: Path, imagens: list[Path], split: str) -> dict:
    from PIL import Image
    from ultralytics import YOLO

    modelo = YOLO(str(pesos))
    r = modelo.val(data=str(data_yaml), split=split, imgsz=IMGSZ, conf=CONF_VAL, iou=IOU_NMS, max_det=MAX_DET, batch=LOTE,
                   plots=False, verbose=False)
    map50 = float(r.box.map50)
    itens = []
    for img, res in zip(imagens, modelo.predict(source=[str(p) for p in imagens], imgsz=IMGSZ, conf=CONF_VAL, iou=IOU_NMS,
                                                max_det=MAX_DET, batch=LOTE, stream=True, verbose=False)):
        alt, larg = res.orig_shape
        itens.append({"pred_xyxy": res.boxes.xyxy.cpu().numpy(), "pred_conf": res.boxes.conf.cpu().numpy(),
                      "gt_xyxy": ler_rotulo_yolo(img.parent.parent / "labels" / f"{img.stem}.txt", larg, alt),
                      "largura": larg, "altura": alt})
    m = medidas_proprias(itens)
    m.update({"mAP50_ultralytics": map50, "n_imagens": len(imagens)})
    return m


def principal(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--split", required=True, choices=["val", "test"])
    p.add_argument("--raiz", required=True)
    p.add_argument("--divisao", required=True)
    p.add_argument("--saida", required=True)
    p.add_argument("--bracos", nargs="*", default=[])
    p.add_argument("--ids", nargs="*", default=[], help="só no split val")
    p.add_argument("--sem-4a-decisao", default=None)
    p.add_argument("--trabalho", default="/content/trabalho_aval")
    a = p.parse_args(argv)
    import torch
    import ultralytics

    if ultralytics.__version__ != VERSAO_ULTRALYTICS:
        raise SystemExit(f"Ultralytics {ultralytics.__version__} != {VERSAO_ULTRALYTICS}")
    if not torch.cuda.is_available():
        raise SystemExit("sem GPU")
    registro = ler_registro()
    if a.split == "test":
        if a.ids:
            raise SystemExit("--ids só vale no split val")
        _commit_limpo()
        linhas = verificar_condicoes_teste(registro, carregar(HASHES), Path(__file__), a.bracos, LACRE, a.sem_4a_decisao)
    else:
        por_id = {r["id_execucao"]: r for r in registro}
        alvo = a.ids or [r["id_execucao"] for r in registro if r["braco"] in a.bracos and "_principal_" in r["id_execucao"]]
        linhas = [por_id[i] for i in alvo]
    saida = Path(a.saida)
    if saida.exists():
        raise SystemExit(f"{saida} já existe")
    data_yaml, imagens = montar_split(a.split, Path(a.divisao), Path(a.raiz), Path(a.trabalho))
    with open(saida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS, lineterminator="\n")
        w.writeheader()
        for r in linhas:
            m = avaliar_modelo(Path(r["caminho_pesos"]), data_yaml, imagens, a.split)
            m.update({"id_execucao": r["id_execucao"], "split": a.split, "sha256_pesos": r["sha256_pesos"]})
            w.writerow({k: m[k] for k in COLUNAS})
            f.flush()
            print(json.dumps({k: m[k] for k in COLUNAS}, ensure_ascii=False))
    if a.split == "test":
        LACRE.write_text(json.dumps({"avaliado_em": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                                     "saida": str(saida), "n_modelos": len(linhas)}, indent=2) + "\n", encoding="utf-8")
        print("LACRE escrito:", LACRE)


if __name__ == "__main__":
    principal()
