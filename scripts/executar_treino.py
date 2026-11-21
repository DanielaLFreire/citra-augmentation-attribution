"""Executa UMA execução de treino do experimento (D35, D42, D43) e registra tudo em runs/REGISTRO_EXECUCOES.csv.

Antes de treinar, recusa se: a versão do Ultralytics não é a fixada (8.4.165); não há GPU; o código tem alteração não
commitada; o hash da lista de treino, da configuração ou da divisão não confere com docs/pre_registro/hashes.json; a execução já
existe no registro; o treino, a validação e o teste da divisão não são disjuntos.
Monta os dados numa pasta LOCAL (copia as imagens únicas, como a Fase 5, em vez de ler o Drive a cada época) sem tocar no
CITRA-3D-Real. Guarda `last.pt` (o modelo avaliado, pelo protocolo), `results.csv` e `args.yaml` no destino (Drive).
Não avalia no teste: a avaliação única do teste é uma etapa à parte.

Uso (uma execução por chamada; um laço de shell repete as sementes; --fumaca faz um teste curto do caminho todo):
  python -m scripts.executar_treino --braco C --plano principal --lista manifests/lista_treino_C.csv \\
      --config configs/treino_yolo11n_d43.yaml --divisao data/divisao_citra_blocos_dias/divisao_blocos_dias.csv \\
      --raiz <CITRA-3D-Real> --seed 42 --destino <pasta no Drive> [--mapa-externas mapa.csv] [--modelo yolo11n.pt]
O mapa de externas tem as colunas id_imagem,caminho_imagem,caminho_rotulo (só para os braços R, E e G).
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

from scripts._hashes import HASHES, carregar, sha256
from scripts._nomes import nome_seguro
from scripts.construir_lista_treino import PLANOS
from scripts.teste_epoca_ultralytics import indexar

VERSAO_ULTRALYTICS = "8.4.165"
REGISTRO = Path(__file__).resolve().parent.parent / "runs" / "REGISTRO_EXECUCOES.csv"
COLUNAS = ["id_execucao", "braco", "fonte_externa", "fracao", "seed", "orcamento_passos", "commit_codigo",
           "sha256_manifesto", "sha256_config", "versoes_bibliotecas", "gpu", "duracao_h", "caminho_pesos",
           "sha256_pesos", "avaliado_val", "avaliado_teste", "observacoes"]
FONTES_CITRA = ("citra", "citra_extra")


def carregar_config(caminho: Path) -> dict:
    return yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))


def verificar_registrado(caminho: Path, hashes_json: Path = HASHES) -> str:
    """Devolve o SHA-256 do arquivo se ele confere com o registrado em hashes.json; senão levanta ValueError."""
    caminho = Path(caminho)
    registrado = carregar(hashes_json).get("artefatos", {}).get(caminho.name)
    if registrado is None:
        raise ValueError(f"{caminho.name} não tem hash registrado (python -m scripts.registrar_artefato)")
    atual = sha256(caminho)
    if atual != registrado["sha256"]:
        raise ValueError(f"{caminho.name}: hash {atual[:12]}… difere do registrado {registrado['sha256'][:12]}…")
    return atual


def ler_divisao(csv_divisao: Path) -> dict[str, set[str]]:
    d: dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
    with open(csv_divisao, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d[r["divisao"]].add(r["nome"])
    return d


def conferir_listas(ids_treino: set[str], divisao: dict[str, set[str]]) -> None:
    """O treino do CITRA só usa imagens do treino da divisão; nada do teste ou da validação."""
    fora = sorted(i for i in ids_treino if i not in divisao["train"])
    if fora:
        raise ValueError(f"{len(fora)} ids da lista não estão no treino da divisão, ex.: {fora[:3]}")
    if divisao["train"] & (divisao["val"] | divisao["test"]) or divisao["val"] & divisao["test"]:
        raise ValueError("a divisão tem imagens em mais de um split")


def ler_mapa_externas(caminho: Path | None) -> dict[str, tuple[Path, Path]]:
    if not caminho:
        return {}
    with open(caminho, newline="", encoding="utf-8") as f:
        return {r["id_imagem"]: (Path(r["caminho_imagem"]), Path(r["caminho_rotulo"])) for r in csv.DictReader(f)}


def preparar_dados(lista_csv: Path, divisao: dict[str, set[str]], raiz: Path, local: Path,
                   mapa_externas: dict | None = None) -> dict:
    """Copia as imagens únicas (e os rótulos de labels_final) para a pasta local e escreve train.txt, val.txt e data.yaml.
    train.txt tem uma linha por linha da lista (as repetições valem, D41). Nunca copia imagem do teste."""
    with open(lista_csv, newline="", encoding="utf-8") as f:
        linhas = [(r["id_imagem"], r["fonte"]) for r in csv.DictReader(f)]  # o mesmo id pode vir como citra e citra_extra
    imagens, rotulos = indexar(Path(raiz))
    mapa_externas = mapa_externas or {}
    conferir_listas({i for i, fonte in linhas if fonte in FONTES_CITRA}, divisao)
    (local / "images").mkdir(parents=True, exist_ok=True)
    (local / "labels").mkdir(parents=True, exist_ok=True)

    def copiar(nome, origem_img, origem_rot):
        nome = nome_seguro(nome)  # ids externos trazem ':' e '/'; ids do CITRA passam sem mudar
        destino = local / "images" / f"{nome}{origem_img.suffix}"
        if not destino.exists():
            shutil.copyfile(origem_img, destino)
            shutil.copyfile(origem_rot, local / "labels" / f"{nome}.txt")
        return destino

    caminhos_treino = []
    for nome, fonte in linhas:
        if fonte in FONTES_CITRA:
            if nome not in imagens or nome not in rotulos:
                raise FileNotFoundError(f"sem imagem ou rótulo de labels_final: {nome}")
            caminhos_treino.append(copiar(nome, imagens[nome], rotulos[nome]))
        else:
            if nome not in mapa_externas:
                raise FileNotFoundError(f"id externo sem entrada no mapa de externas: {nome}")
            caminhos_treino.append(copiar(nome, *mapa_externas[nome]))
    val = sorted(divisao["val"])
    caminhos_val = []
    for nome in val:
        if nome not in imagens or nome not in rotulos:
            raise FileNotFoundError(f"validação sem imagem ou rótulo: {nome}")
        caminhos_val.append(copiar(nome, imagens[nome], rotulos[nome]))
    (local / "train.txt").write_text("\n".join(map(str, caminhos_treino)) + "\n", encoding="utf-8")
    (local / "val.txt").write_text("\n".join(map(str, caminhos_val)) + "\n", encoding="utf-8")
    (local / "data.yaml").write_text(
        f"path: {local}\ntrain: {local / 'train.txt'}\nval: {local / 'val.txt'}\nnc: 1\nnames: ['embarcacao']\n", encoding="utf-8")
    nao_citra = [fonte for _, fonte in linhas if fonte != "citra"]
    fontes_ext = sorted({fonte for fonte in nao_citra})
    return {"linhas_treino": len(linhas), "imagens_unicas_treino": len({n for n, _ in linhas}), "imagens_val": len(val),
            "fonte_externa": ",".join(fontes_ext), "fracao": round(len(nao_citra) / len(linhas), 4),
            "data_yaml": str(local / "data.yaml")}


def linha_registro(**kw) -> dict:
    """Uma linha do REGISTRO_EXECUCOES.csv; levanta KeyError se faltar coluna e ignora o que não é coluna."""
    return {c: kw[c] for c in COLUNAS}


def anexar_registro(linha: dict, caminho: Path = REGISTRO) -> None:
    caminho = Path(caminho)
    existe = caminho.exists() and caminho.read_text(encoding="utf-8").strip() != ""
    if existe:
        with open(caminho, newline="", encoding="utf-8") as f:
            if any(r["id_execucao"] == linha["id_execucao"] for r in csv.DictReader(f)):
                raise ValueError(f"execução {linha['id_execucao']} já está no registro")
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUNAS)
        if not existe:
            w.writeheader()
        w.writerow(linha)


def argumentos_treino(cfg: dict, data_yaml: str, projeto: str, nome: str, seed: int, fumaca: bool = False) -> dict:
    """Argumentos de Model.train: a configuração fixa + os campos de cada execução, numa só mapa (sem chave repetida).
    'model' sai da configuração (quem escolhe o modelo é --modelo). No modo fumaça: 1 época em 2% do treino, só para
    exercitar o caminho todo (dados, treino, cópia de pesos, registro)."""
    args = {k: v for k, v in cfg.items() if k != "model"}
    args.update({"data": data_yaml, "project": projeto, "name": nome, "exist_ok": True, "seed": seed})
    if fumaca:
        args.update({"epochs": 1, "fraction": 0.02, "plots": False})
    return args


def _commit_limpo(cwd=None) -> tuple[str, bool]:
    """Commit atual e se o código está limpo. O próprio registro de execuções fica de fora da conferência: cada execução
    termina anexando uma linha a ele, e isso não pode barrar a execução seguinte (falha da 2ª semente em 2026-11-20)."""
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=cwd).strip()
    sujo = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no", "--", ".", ":(exclude)runs/REGISTRO_EXECUCOES.csv"],
        text=True, cwd=cwd).strip()
    return sha, sujo == ""


def principal(a) -> dict:
    import torch
    import ultralytics
    from ultralytics import YOLO, settings

    if ultralytics.__version__ != VERSAO_ULTRALYTICS:
        raise SystemExit(f"Ultralytics {ultralytics.__version__} instalado; o experimento fixa {VERSAO_ULTRALYTICS} (D43)")
    if not torch.cuda.is_available():
        raise SystemExit("sem GPU: troque o ambiente de execução do Colab para GPU")
    commit, limpo = _commit_limpo()
    if not limpo:
        raise SystemExit("o código tem alterações não commitadas; commit ou git checkout antes de treinar")
    plano = PLANOS[a.plano]
    base = f"{a.braco}_{a.plano}_{a.modelo.split('.')[0]}_seed{a.seed}"
    id_exec = base + ("_fumaca" if a.fumaca else "")
    destino = Path(a.destino) / id_exec
    if destino.exists():
        raise SystemExit(f"{destino} já existe; execuções não se sobrescrevem")
    h_lista, h_config = verificar_registrado(Path(a.lista)), verificar_registrado(Path(a.config))
    verificar_registrado(Path(a.divisao))
    try:
        settings.update({"sync": False})  # sem telemetria: as imagens são da Marinha
    except Exception:
        pass
    divisao = ler_divisao(Path(a.divisao))
    local = Path(a.trabalho) / base  # a fumaça e a execução real reaproveitam os mesmos dados copiados
    dados = preparar_dados(Path(a.lista), divisao, Path(a.raiz), local, ler_mapa_externas(a.mapa_externas))
    cfg = carregar_config(Path(a.config))
    medido = {}

    def ao_iniciar_epoca(trainer):
        if "lotes" not in medido:
            medido["lotes"] = len(trainer.train_loader)
            medido["imagens"] = len(trainer.train_loader.dataset)
            if a.fumaca:
                return
            if medido["lotes"] != plano["passos_por_epoca"] or medido["imagens"] != dados["linhas_treino"]:
                raise RuntimeError(f"conjunto fora do desenho: {medido} (esperado {plano['passos_por_epoca']} lotes, "
                                   f"{dados['linhas_treino']} imagens)")

    modelo = YOLO(a.modelo)
    pesos_iniciais = sha256(Path(modelo.ckpt_path)) if getattr(modelo, "ckpt_path", None) and Path(modelo.ckpt_path).exists() else "desconhecido"
    modelo.add_callback("on_train_epoch_start", ao_iniciar_epoca)
    t0 = time.time()
    cfg = argumentos_treino(cfg, dados["data_yaml"], str(local / "runs"), id_exec, a.seed, a.fumaca)
    modelo.train(**cfg)
    horas = (time.time() - t0) / 3600
    saida = local / "runs" / id_exec
    destino.mkdir(parents=True)
    for nome in ("weights/last.pt", "results.csv", "args.yaml"):
        if (saida / nome).exists():
            shutil.copyfile(saida / nome, destino / Path(nome).name)
    pesos = destino / "last.pt"
    val_final = ""
    if (destino / "results.csv").exists():
        with open(destino / "results.csv", newline="", encoding="utf-8") as f:
            lin = [{k.strip(): v for k, v in r.items()} for r in csv.DictReader(f)]
        val_final = lin[-1].get("metrics/mAP50(B)", "") if lin else ""
    linha = linha_registro(
        id_execucao=id_exec, braco=a.braco, fonte_externa=dados["fonte_externa"], fracao=dados["fracao"], seed=a.seed,
        orcamento_passos=medido["lotes"] * cfg["epochs"], commit_codigo=commit, sha256_manifesto=h_lista, sha256_config=h_config,
        versoes_bibliotecas=f"ultralytics {ultralytics.__version__}; torch {torch.__version__}", gpu=torch.cuda.get_device_name(0),
        duracao_h=round(horas, 3), caminho_pesos=str(pesos), sha256_pesos=sha256(pesos) if pesos.exists() else "",
        avaliado_val=f"mAP50 última época {val_final}", avaliado_teste="nao",
        observacoes=f"modelo inicial {a.modelo} sha256 {pesos_iniciais}; plano {a.plano}; lotes por época {medido['lotes']}")
    if not a.fumaca:  # a fumaça não entra no registro do experimento
        anexar_registro(linha)
    anexar_registro(linha, destino / "registro_execucao.csv")
    print("REGISTRO:", json.dumps(linha, ensure_ascii=False))
    return linha


def argumentos(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--braco", required=True, choices=["C", "R", "E", "G"])
    p.add_argument("--plano", required=True, choices=sorted(PLANOS))
    p.add_argument("--lista", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--divisao", required=True)
    p.add_argument("--raiz", required=True)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--destino", required=True)
    p.add_argument("--trabalho", default="/content/trabalho")
    p.add_argument("--mapa-externas", default=None)
    p.add_argument("--modelo", default="yolo11n.pt")
    p.add_argument("--fumaca", action="store_true", help="teste de caminho: 1 época em 2%% do treino, fora do registro")
    return p.parse_args(argv)


if __name__ == "__main__":
    principal(argumentos())
