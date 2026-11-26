"""Normalização mecânica de uma planilha de auditoria do 4a, sem alterar nenhum julgamento.

Só faz duas coisas, ambas listadas no relatório:
  1. nas linhas `imagem` e `original`, se `categoria` está vazia e `classe` tem 0 ou 1, move o valor para `categoria` e esvazia `classe`;
  2. corrige a grafia `deslocado` -> `deslocada` (e `apagado` -> `apagada`, `alterado` -> `alterada`) em caixas, só quando a categoria não existe.
Qualquer outra categoria inválida ou vazia faz o script parar. Recusa sobrescrever. Uso: python -m scripts.normalizar_auditoria entrada.csv saida.csv
"""
import csv
import json
import sys
from pathlib import Path

VALIDAS = {"valida", "apagada", "deslocada", "alterada", "sem_objeto_original", "nao_avaliavel"}
GRAFIA = {"deslocado": "deslocada", "apagado": "apagada", "alterado": "alterada"}


def normalizar(linhas: list[dict]) -> tuple[list[dict], dict]:
    mov, graf = [], []
    for r in linhas:
        if r["tipo"] == "caixa":
            c = r["categoria"].strip().lower()
            if c in GRAFIA:
                graf.append((r["codigo"], r["item"], c, GRAFIA[c]))
                c = GRAFIA[c]
            if c not in VALIDAS:
                raise ValueError(f"categoria inválida ou vazia: {r['codigo']} caixa {r['item']}: {r['categoria']!r}")
            r["categoria"] = c
        else:
            if r["categoria"].strip() == "" and r["classe"].strip() in {"0", "1"}:
                r["categoria"], r["classe"] = r["classe"].strip(), ""
                mov.append((r["codigo"], r["tipo"]))
            if r["categoria"].strip() not in {"0", "1"}:
                raise ValueError(f"{r['tipo']} sem 0/1: {r['codigo']}")
    return linhas, {"linhas_movidas_de_classe_para_categoria": len(mov), "grafias_corrigidas": graf}


def principal(argv=None) -> int:
    ent, sai = Path(argv[0]), Path(argv[1])
    if sai.exists():
        print("recuso sobrescrever", file=sys.stderr)
        return 2
    with open(ent, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        campos = rd.fieldnames
        linhas = list(rd)
    linhas, rel = normalizar(linhas)
    with open(sai, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)
    print(json.dumps(rel, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(principal(sys.argv[1:]))
