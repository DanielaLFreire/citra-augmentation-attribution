"""Confere a saída de uma ou duas execuções do iflens (ramo reprodutibilidade-condicoes-restritas).

Uso: python -m scripts.verificar_saida_iflens PASTA_SAIDA_1 [PASTA_SAIDA_2]
Com duas pastas feitas com a MESMA semente e o MESMO conjunto, confere também a reprodutibilidade
da amostra, da classificação e da variação (a imagem gerada não é determinística).
"""
import hashlib
import json
import sys
from pathlib import Path

CAMPOS = ["image", "master_seed", "input_sha256", "original_conditions", "variation_conditions",
          "generation_prompt", "generation_model_returned", "response_id", "output_sha256",
          "same_size_as_input", "status"]


def carregar(pasta):
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(pasta).glob("AUG_*.json"))}


def conferir_pasta(pasta):
    regs, problemas = carregar(pasta), []
    if not regs:
        problemas.append("nenhum AUG_*.json encontrado")
    for nome, r in regs.items():
        if r.get("status") != "ok":
            problemas.append(f"{nome}: status {r.get('status')} {r.get('error', '')}")
            continue
        for c in CAMPOS:
            if r.get(c) in (None, ""):
                problemas.append(f"{nome}: campo vazio/ausente: {c}")
        png = Path(pasta) / r.get("output_file", "")
        if not png.exists():
            problemas.append(f"{nome}: PNG ausente")
        elif hashlib.sha256(png.read_bytes()).hexdigest() != r.get("output_sha256"):
            problemas.append(f"{nome}: SHA-256 do PNG não bate com o registro")
        if r.get("same_size_as_input") is False:
            problemas.append(f"{nome}: tamanho da saída difere da entrada {r['input_size_wh']} -> {r['output_size_wh']}")
        o, v = r.get("original_conditions", {}), r.get("variation_conditions", {})
        if any(o.get(k) == x for k, x in v.items()):
            problemas.append(f"{nome}: variação repete condição original")
    return regs, problemas


def comparar(a, b):
    problemas = []
    if set(a) != set(b):
        problemas.append(f"amostras diferentes: só em 1: {sorted(set(a) - set(b))}, só em 2: {sorted(set(b) - set(a))}")
    for nome in sorted(set(a) & set(b)):
        for c in ["input_sha256", "classify_seed", "variation_seed", "original_conditions", "variation_conditions", "generation_prompt"]:
            if a[nome].get(c) != b[nome].get(c):
                problemas.append(f"{nome}: {c} difere entre as execuções: {a[nome].get(c)} x {b[nome].get(c)}")
        if a[nome].get("output_sha256") == b[nome].get("output_sha256"):
            problemas.append(f"{nome}: (informativo) imagem gerada idêntica nas duas execuções")
    return problemas


def main(argv):
    if not 1 <= len(argv) <= 2:
        print(__doc__); return 2
    regs1, p = conferir_pasta(argv[0])
    print(f"{argv[0]}: {len(regs1)} registros")
    if len(argv) == 2:
        regs2, p2 = conferir_pasta(argv[1])
        print(f"{argv[1]}: {len(regs2)} registros")
        p += p2 + comparar(regs1, regs2)
    for x in p:
        print("-", x)
    print("OK" if not [x for x in p if "(informativo)" not in x] else "FALHAS")
    return 0 if not [x for x in p if "(informativo)" not in x] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
