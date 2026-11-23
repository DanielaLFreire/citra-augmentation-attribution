"""Verificação por código das condições do estágio 1 do teste (adendo 4b, seção 3), antes de qualquer avaliação do teste.

Confere, sem tocar em imagem nem em modelo: (1) adendos 4 e 4b lacrados e iguais ao arquivo; (2) adendos 4a e 4c (G) lacrados, ou
dispensados por decisão registrada depois do prazo de 30/12/2026; (3) todos os instrumentos do estágio 1 com hash registrado e inalterado;
(4) etiqueta de git `lacre-<adendo>` apontando para uma versão do adendo com o hash registrado; (5) código sem alterações não commitadas.
A saída (JSON) é arquivada em decisão. `avaliar_teste_v3.py` chama esta verificação sozinho no split de teste e não avalia se ela falha.

Uso: python -m scripts.verificar_condicoes_etapa1 [--dispensa adendo4a_fidelidade_iflens.md=D70] [--saida verificacao.json]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from scripts._hashes import HASHES, RAIZ, carregar, sha256

PRAZO = date(2026, 12, 30)
ADENDOS_SEMPRE = {"adendo4_fontes_aumento.md": "lacre-adendo4", "adendo4b_avaliacao_em_dois_estagios.md": "lacre-adendo4b"}
ADENDOS_POR_BRACO = {"adendo4a_fidelidade_iflens.md": "lacre-adendo4a", "adendo4c_genship.md": "lacre-adendo4c"}
INSTRUMENTOS = ("avaliar_teste.py", "avaliar_teste_v2.py", "avaliar_teste_v3.py", "analisar_principal.py", "analisar_principal_v2.py",
                "analisar_hardware.py", "bootstrap_imagens.py", "verificar_condicoes_etapa1.py")


def hoje_brasilia() -> date:
    return (datetime.now(timezone.utc) - timedelta(hours=3)).date()


def verificar_instrumentos(hashes: dict, pasta_scripts: Path) -> list[str]:
    erros = []
    for nome in INSTRUMENTOS:
        reg = hashes.get("artefatos", {}).get(nome)
        arq = Path(pasta_scripts) / nome
        if reg is None:
            erros.append(f"{nome}: sem hash registrado")
        elif not arq.is_file():
            erros.append(f"{nome}: arquivo ausente")
        elif sha256(arq) != reg["sha256"]:
            erros.append(f"{nome}: alterado depois do registro")
    return erros


def verificar_adendos(hashes: dict, dispensas: dict[str, str], hoje: date, decisoes_md: Path, raiz: Path = RAIZ) -> list[str]:
    erros = []
    lacrados = hashes.get("adendos", {})

    def conferir(nome: str) -> None:
        arq = Path(raiz) / lacrados[nome]["caminho"]
        if not arq.is_file() or sha256(arq) != lacrados[nome]["sha256"]:
            erros.append(f"{nome}: lacrado, mas o arquivo difere do hash do lacre")

    for nome in ADENDOS_SEMPRE:
        if nome not in lacrados:
            erros.append(f"{nome}: não está lacrado")
        else:
            conferir(nome)
    for nome in ADENDOS_POR_BRACO:
        if nome in lacrados:
            conferir(nome)
            continue
        dec = dispensas.get(nome)
        if not dec:
            erros.append(f"{nome}: não está lacrado e não há dispensa")
        elif hoje <= PRAZO:
            erros.append(f"{nome}: a dispensa só vale depois de {PRAZO.isoformat()} (hoje é {hoje.isoformat()})")
        elif not re.search(rf"^\| {re.escape(dec)} \|", Path(decisoes_md).read_text(encoding="utf-8"), re.M):
            erros.append(f"{nome}: a decisão {dec} não existe em DECISOES.md")
    return erros


def verificar_tags(hashes: dict, cwd: Path = RAIZ) -> list[str]:
    erros = []
    lacrados = hashes.get("adendos", {})
    for nome, tag in {**ADENDOS_SEMPRE, **ADENDOS_POR_BRACO}.items():
        if nome not in lacrados:
            continue
        existe = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"], cwd=cwd, capture_output=True)
        if existe.returncode != 0:
            erros.append(f"{nome}: falta a etiqueta de git {tag}")
            continue
        blob = subprocess.run(["git", "show", f"{tag}:{lacrados[nome]['caminho']}"], cwd=cwd, capture_output=True)
        if blob.returncode != 0 or hashlib.sha256(blob.stdout).hexdigest() != lacrados[nome]["sha256"]:
            erros.append(f"{nome}: a etiqueta {tag} não aponta para a versão lacrada")
    return erros


def verificar_codigo_limpo(cwd: Path = RAIZ) -> tuple[str, list[str]]:
    sujo = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no", "--", ".", ":(exclude)runs/REGISTRO_EXECUCOES.csv"],
                          cwd=cwd, capture_output=True, text=True).stdout.strip()
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True).stdout.strip()
    return commit, ([f"código com alterações não commitadas: {sujo}"] if sujo else [])


def verificar(dispensas: dict[str, str] | None = None, hashes_json: Path = HASHES, hoje: date | None = None,
              decisoes_md: Path | None = None, raiz: Path = RAIZ) -> dict:
    from scripts.avaliar_teste import DECISOES

    hashes = carregar(hashes_json)
    erros = (verificar_instrumentos(hashes, Path(raiz) / "scripts")
             + verificar_adendos(hashes, dispensas or {}, hoje or hoje_brasilia(), decisoes_md or DECISOES, raiz)
             + verificar_tags(hashes, raiz))
    commit, e = verificar_codigo_limpo(raiz)
    erros += e
    return {"ok": not erros, "problemas": erros, "commit": commit, "dispensas": dispensas or {},
            "verificado_em_utc": datetime.now(timezone.utc).isoformat()}


def principal(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dispensa", action="append", default=[], help="NOME_DO_ADENDO=Dnn (só vale depois de 30/12/2026)")
    p.add_argument("--saida", default=None)
    a = p.parse_args(argv)
    r = verificar({k: v for k, v in (x.split("=", 1) for x in a.dispensa)})
    if a.saida:
        Path(a.saida).write_text(json.dumps(r, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(principal())
