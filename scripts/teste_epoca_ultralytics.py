"""Teste de 1 época do Ultralytics com a lista de treino da D35 (confirma que as linhas repetidas valem).

Pergunta: o Ultralytics, ao ler um .txt com caminhos repetidos, mantém as repetições? Esperado para o braço C da D35:
10.960 imagens na época e 685 lotes de 16. Se o conjunto vier com 1.370 imagens (repetições descartadas), o teste mostra
isso e se usa --copias-fisicas (links com nomes únicos id__c<copia>, cada um com seu rótulo).

Não toca no CITRA-3D-Real: monta uma cópia de trabalho (links para as imagens e rótulos de `labels_final` copiados)
numa pasta nova, porque o Ultralytics procura rótulos em .../labels/ e grava um .cache ao lado.
Uso (Colab, com ultralytics instalado):
  python -m scripts.teste_epoca_ultralytics <lista.csv> <raiz CITRA-3D-Real> <pasta_trabalho> [--copias-fisicas] [--so-contar]
Os números (imagens no conjunto e lotes por época) são medidos e IMPRESSOS no início da época. Com --so-contar o treino
para logo depois disso (a contagem basta para o objetivo do teste; a época completa é lenta porque lê imagens do Drive).
Saída: <pasta_trabalho>/resultado_teste_epoca.json
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
from pathlib import Path

LOTE = 16
ESPERADO_LINHAS = 10960
ESPERADO_LOTES = 685


def indexar(raiz: Path) -> tuple[dict[str, Path], dict[str, Path]]:
    """nome -> caminho da imagem (qualquer split antigo) e nome -> rótulo de labels_final."""
    imagens = {p.stem: p for p in raiz.glob("*/images/*") if p.suffix.lower() in (".png", ".jpg", ".jpeg")}
    rotulos = {p.stem: p for p in raiz.glob("*/labels_final/*.txt")}
    return imagens, rotulos


def ler_lista(csv_lista: Path) -> list[tuple[str, int]]:
    with open(csv_lista, newline="", encoding="utf-8") as f:
        return [(r["id_imagem"], int(r["copia"])) for r in csv.DictReader(f)]


def montar(linhas: list[tuple[str, int]], imagens: dict, rotulos: dict, saida: Path, copias_fisicas: bool = False) -> list[str]:
    """Cria saida/images e saida/labels e devolve as linhas do train.txt (uma por linha da lista, na mesma ordem)."""
    faltam = sorted({i for i, _ in linhas if i not in imagens or i not in rotulos})
    if faltam:
        raise FileNotFoundError(f"{len(faltam)} ids sem imagem ou rótulo, ex.: {faltam[:3]}")
    (saida / "images").mkdir(parents=True, exist_ok=True)
    (saida / "labels").mkdir(parents=True, exist_ok=True)
    caminhos = []
    for nome, copia in linhas:
        base = f"{nome}__c{copia}" if copias_fisicas else nome
        img = saida / "images" / f"{base}{imagens[nome].suffix}"
        if not img.exists():
            img.symlink_to(imagens[nome].resolve())
            shutil.copyfile(rotulos[nome], saida / "labels" / f"{base}.txt")
        caminhos.append(str(img))
    return caminhos


class _Parada(Exception):
    """Interrompe o treino depois da contagem (modo --so-contar)."""


def principal(csv_lista: str, raiz: str, trabalho: str, copias_fisicas: bool = False, so_contar: bool = False) -> dict:
    import ultralytics
    from ultralytics import YOLO

    saida = Path(trabalho)
    imagens, rotulos = indexar(Path(raiz))
    linhas = ler_lista(Path(csv_lista))
    caminhos = montar(linhas, imagens, rotulos, saida, copias_fisicas)
    (saida / "train.txt").write_text("\n".join(caminhos) + "\n", encoding="utf-8")
    (saida / "val.txt").write_text("\n".join(sorted(set(caminhos))[:LOTE]) + "\n", encoding="utf-8")
    (saida / "data.yaml").write_text(
        f"path: {saida}\ntrain: {saida / 'train.txt'}\nval: {saida / 'val.txt'}\nnc: 1\nnames: ['embarcacao']\n", encoding="utf-8")
    medido = {}

    def ao_iniciar_epoca(trainer):
        medido["imagens_no_conjunto"] = len(trainer.train_loader.dataset)
        medido["lotes_por_epoca"] = len(trainer.train_loader)
        print("MEDIDO:", json.dumps(medido), flush=True)
        if so_contar:
            raise _Parada()

    modelo = YOLO("yolo11n.pt")
    modelo.add_callback("on_train_epoch_start", ao_iniciar_epoca)
    try:
        modelo.train(data=str(saida / "data.yaml"), epochs=1, batch=LOTE, imgsz=640, workers=2, val=False, plots=False,
                     project=str(saida / "runs"), name="teste", exist_ok=True, seed=0)
    except _Parada:
        pass
    res = {"ultralytics": ultralytics.__version__, "linhas_na_lista": len(linhas), "copias_fisicas": copias_fisicas,
           "so_contou": so_contar,
           "esperado": {"imagens": ESPERADO_LINHAS, "lotes": ESPERADO_LOTES}, **medido,
           "confere": medido.get("imagens_no_conjunto") == ESPERADO_LINHAS and medido.get("lotes_por_epoca") == ESPERADO_LOTES}
    (saida / "resultado_teste_epoca.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return res


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 3:
        sys.exit(__doc__)
    principal(a[0], a[1], a[2], "--copias-fisicas" in sys.argv, "--so-contar" in sys.argv)
