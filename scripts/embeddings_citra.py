"""Passo 1 da medida de semelhança v2: embeddings DINOv2 das imagens reais do CITRA (treino, validação e teste).

Lê o CITRA-3D.zip (zips internos train/val/test), usa só as imagens reais (nome dd.mm.aaaa-hh-mm-ss.png; exclui as 2
da quarentena), redimensiona para 448x252 (múltiplos de 14, sem recorte, para não perder embarcações nas bordas) e
extrai, com facebook/dinov2-base em fp32: o token CLS e a média dos tokens de patch (768 valores cada).
Roda localmente no Colab; nenhuma imagem sai do ambiente (condições da D21 não se aplicam: sem API externa).
Saídas: .npz (split, nome, cls, patch_medio) e .json de proveniência (versões, commit do modelo, hash do .npz).
O .npz fica no Drive do projeto, não no repositório (derivado de imagem privada); o repositório guarda o .json.
Critérios de uso dos embeddings: D25 em docs/DECISOES.md (definidos antes da extração).
"""
import datetime
import hashlib
import io
import json
import platform
import re
import subprocess
import sys
import zipfile

import numpy as np

REAL = re.compile(r"^\d{2}\.\d{2}\.\d{4}-\d{2}-\d{2}-\d{2}\.png$")
QUARENTENA = {"29.04.2022-14-59-27", "14.04.2022-13-48-55"}
INTERNOS = {
    "train": "CITRA-3D/train-20260103T082001Z-1-001.zip",
    "val": "CITRA-3D/val-20260103T104420Z-1-001.zip",
    "test": "CITRA-3D/test-20260103T110900Z-1-001.zip",
}
MODELO = "facebook/dinov2-base"
LARGURA, ALTURA = 448, 252
MEDIA = np.array([0.485, 0.456, 0.406], np.float32)
DP = np.array([0.229, 0.224, 0.225], np.float32)


def nomes_reais(nomes_no_zip):
    """[(caminho no zip, nome sem extensão)] só das imagens reais fora da quarentena, em ordem de nome."""
    achados = []
    for n in nomes_no_zip:
        b = n.split("/")[-1]
        if REAL.match(b) and b[:-4] not in QUARENTENA:
            achados.append((n, b[:-4]))
    return sorted(achados, key=lambda t: t[1])


def l2(x):
    """Normaliza cada linha para norma 1 (o cosseno vira produto interno)."""
    x = np.asarray(x, np.float32)
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def sha256_arquivo(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _commit_repositorio():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def principal(caminho_zip, saida_npz, lote=16):
    import cv2
    import torch
    import transformers
    from transformers import AutoModel

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    modelo = AutoModel.from_pretrained(MODELO).eval().to(dev)
    ext = zipfile.ZipFile(caminho_zip)
    splits, nomes, cls, medio = [], [], [], []
    for split in ("train", "val", "test"):
        with ext.open(INTERNOS[split]) as f:
            z = zipfile.ZipFile(io.BytesIO(f.read()))
        itens = nomes_reais(z.namelist())
        print(split, len(itens), "imagens reais", flush=True)
        for i in range(0, len(itens), lote):
            blocos = []
            for caminho, _ in itens[i:i + lote]:
                im = cv2.imdecode(np.frombuffer(z.read(caminho), np.uint8), cv2.IMREAD_COLOR)
                im = cv2.cvtColor(cv2.resize(im, (LARGURA, ALTURA), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
                blocos.append(((im.astype(np.float32) / 255.0 - MEDIA) / DP).transpose(2, 0, 1))
            with torch.no_grad():
                h = modelo(pixel_values=torch.from_numpy(np.stack(blocos)).to(dev)).last_hidden_state
            cls.append(h[:, 0].cpu().numpy())
            medio.append(h[:, 1:].mean(1).cpu().numpy())
        splits += [split] * len(itens)
        nomes += [n for _, n in itens]
    np.savez(saida_npz, split=np.array(splits), nome=np.array(nomes),
             cls=np.concatenate(cls), patch_medio=np.concatenate(medio))
    meta = {
        "gerado_em_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "modelo": MODELO,
        "modelo_commit": getattr(modelo.config, "_commit_hash", None),
        "entrada_px_largura_altura": [LARGURA, ALTURA],
        "precisao": "fp32",
        "dispositivo": dev,
        "versoes": {"python": platform.python_version(), "torch": torch.__version__,
                    "transformers": transformers.__version__, "numpy": np.__version__, "opencv": cv2.__version__},
        "n_por_split": {s: splits.count(s) for s in ("train", "val", "test")},
        "repositorio_commit": _commit_repositorio(),
        "npz_sha256": sha256_arquivo(saida_npz),
    }
    with open(saida_npz.replace(".npz", "_proveniencia.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    principal(sys.argv[1], sys.argv[2])
