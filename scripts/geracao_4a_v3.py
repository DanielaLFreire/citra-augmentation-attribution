"""Geração das 150 edições do 4a, versão 3 (D74): o v2 (D73) gerou 23 das 30 imagens de risco; as 7 restantes tinham a original já encoberta
(`overcast`), e o arquivo de risco só tem `overcast` para o céu, então não há outro valor a sortear (IndexError). Nesse caso o céu fica como está
(`--keep planet sky`): a edição muda só a hora do dia e a atmosfera. O v2 e o `geracao_4a.py` continuam registrados e são reutilizados.

Texto do v2, que continua valendo:

Problema (execução de 25/11/2026): o estrato de risco falhou nas 30 imagens, sem nenhuma chamada ao Gemini. O iflens usa o MESMO
arquivo de condições para classificar a imagem original e para sortear a variação. O `conditions-citra-risk.yaml` só tem os valores de
risco (noon/afternoon, overcast, heavy_rain/dense_fog); o classificador devolve valores que não estão nele (dusk, haze, ...) e a leitura
falha ("Invalid sky condition: None", "Cannot choose from an empty sequence"). O README do iflens ("carregue este arquivo no lugar do
conditions-citra.yaml") não funciona como está.

Solução, sem alterar o iflens: para cada imagem de risco
  1. classifica-se a original com o esquema PADRÃO (`conditions-citra.yaml`), com a mesma semente `derive_seed(mestra, imagem, "classify")`
     e o mesmo modelo, temperatura 0;
  2. monta-se um esquema da imagem = valores de risco + o valor original de cada classe (para a leitura da classificação ser válida);
  3. grava-se a classificação no cache sob a chave desse esquema e chama-se o `iflens.main` normalmente com esse esquema (n=1).
Assim a variação é sorteada (`Random(derive_seed(mestra, imagem, "variation"))`) só entre os valores de risco diferentes do original,
que é o objetivo do estrato (4a, seções 3 e 4). O restante (modelo, prompt, semente, geração) não muda. O estrato padrão não é afetado.
Os esquemas por imagem e o resumo ficam em `esquemas_risco/` na pasta de trabalho.

Uso: igual ao `geracao_4a executar`.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from scripts import geracao_4a as g
from scripts.geracao_4a_v2 import montar_esquema
from scripts._hashes import RAIZ, sha256


def classes_sem_sorteio(risco: dict, original: dict[str, str]) -> list[str]:
    """Classes em que todos os valores de risco são iguais ao original: não há o que sortear."""
    return [c for c, v in risco.items() if set(v) <= {original.get(c)}]


def executar_risco(P: dict, citra_raiz: Path, iflens_dir: Path, trabalho: Path, classificar=None, chamar=None) -> dict:
    from iflens.reproducibility import classification_key, derive_seed, load_cache, save_cache, sha256_bytes
    from iflens.schema.conditions import ConditionSchema

    iflens_dir, trabalho = Path(iflens_dir), Path(trabalho)
    padrao_arq = iflens_dir / P["condicoes"]["padrao"]["arquivo"]
    risco_arq = iflens_dir / P["condicoes"]["risco"]["arquivo"]
    padrao = yaml.safe_load(padrao_arq.read_text(encoding="utf-8"))
    risco = yaml.safe_load(risco_arq.read_text(encoding="utf-8"))
    schema_padrao = ConditionSchema.from_yaml(padrao_arq)
    if classificar is None:
        from groq import Groq
        from iflens.functions.classification import classify_image
        cliente = Groq()
        classificar = lambda caminho, nome: classify_image(caminho, schema_padrao, cliente, model=P["modelo_visao_classificacao"],
                                                           temperature=0, seed=derive_seed(P["semente_mestra"], nome, "classify")).to_dict()
    cache_arq = trabalho / "cache_classificacao.json"
    cache = load_cache(cache_arq)
    esq_dir = trabalho / "esquemas_risco"
    esq_dir.mkdir(parents=True, exist_ok=True)
    resumo_arq = esq_dir / "resumo.json"
    resumo = json.loads(resumo_arq.read_text()) if resumo_arq.exists() else {}
    tent_arq = trabalho / "tentativas_risco.json"
    tentativas = json.loads(tent_arq.read_text()) if tent_arq.exists() else {}
    originais = trabalho / "originais_150"
    originais.mkdir(exist_ok=True)
    resultado = {}
    for lote, nomes in P["lotes"].items():
        if not lote.startswith("risco"):
            continue
        saidas = trabalho / "saidas" / lote
        saidas.mkdir(parents=True, exist_ok=True)
        for n in nomes:
            if n in g.registros_ok(saidas):
                continue
            erro = g.ultimo_erro(saidas).get(n)
            if (erro is not None and not g.eh_falha_tecnica(erro)) or tentativas.get(n, 0) >= P["max_tentativas_falha_tecnica"]:
                continue
            img, lab = g.encontrar(citra_raiz, n, "images"), g.encontrar(citra_raiz, n, "labels_final", ".txt")
            shutil.copy(img, originais / img.name)
            shutil.copy(lab, originais / lab.name)
            ds = trabalho / "pendentes" / lote / n
            shutil.rmtree(ds, ignore_errors=True)
            ds.mkdir(parents=True)
            shutil.copy(img, ds / img.name)
            shutil.copy(lab, ds / lab.name)
            if n not in resumo:  # classifica uma vez e guarda; a repetição por falha técnica reutiliza
                resumo[n] = {"original": classificar(str(ds / img.name), img.name)}
            esq = esq_dir / f"{n}.yaml"
            esq.write_text(yaml.safe_dump(montar_esquema(padrao, risco, resumo[n]["original"]), allow_unicode=True, sort_keys=False), encoding="utf-8")
            resumo[n]["esquema_sha256"] = sha256(esq)
            resumo_arq.write_text(json.dumps(resumo, indent=1, sort_keys=True))
            cache[classification_key(sha256_bytes(img.read_bytes()), P["modelo_visao_classificacao"], resumo[n]["esquema_sha256"])] = resumo[n]["original"]
            save_cache(cache_arq, cache)
            tentativas[n] = tentativas.get(n, 0) + 1
            tent_arq.write_text(json.dumps(tentativas, indent=1, sort_keys=True))
            manter = ["planet"] + classes_sem_sorteio(risco, resumo[n]["original"])
            resumo[n]["keep"] = manter
            resumo_arq.write_text(json.dumps(resumo, indent=1, sort_keys=True))
            cmd = [sys.executable, "-m", "iflens.main", "--dataset", str(ds), "--conditions", str(esq), "--n", "1", "--keep", *manter,
                   "--seed", str(P["semente_mestra"]), "--model", P["modelo_geracao_solicitado"],
                   "--vision-model", P["modelo_visao_classificacao"], "--prompt-file", str(RAIZ / P["prompt_arquivo"]),
                   "--classification-cache", str(cache_arq), "--output", str(saidas)]
            (chamar or subprocess.run)(cmd, cwd=str(iflens_dir), check=False)
        resultado[lote] = {"n": len(nomes), "ok": sum(n in g.registros_ok(saidas) for n in nomes)}
    return resultado


def principal(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--parametros", default=str(g.SAIDA_PARAMETROS))
    ap.add_argument("--citra-raiz", required=True)
    ap.add_argument("--iflens-dir", required=True)
    ap.add_argument("--trabalho", required=True)
    a = ap.parse_args(argv)
    P = json.loads(Path(a.parametros).read_text(encoding="utf-8"))
    trab = Path(a.trabalho)
    trab.mkdir(parents=True, exist_ok=True)
    # estrato padrão: mesmo código do v1, sem o lote de risco
    Pp = dict(P, lotes={k: v for k, v in P["lotes"].items() if not k.startswith("risco")},
              condicoes={"padrao": P["condicoes"]["padrao"]})
    tmp = trab / "parametros_padrao_tmp.json"
    tmp.write_text(json.dumps(Pp))
    res_padrao = g.executar(tmp, Path(a.citra_raiz), Path(a.iflens_dir), trab)
    res_risco = executar_risco(P, Path(a.citra_raiz), Path(a.iflens_dir), trab)
    todos = {}
    for lote in P["lotes"]:
        todos.update(g.registros_ok(trab / "saidas" / lote))
    print(json.dumps({"padrao": res_padrao["lotes"], "risco": res_risco, "ok_total": len(todos),
                      "modelos_retornados": sorted({r.get("generation_model_returned") or "" for r in todos.values()}),
                      "mesma_proporcao": sum(bool(r.get("same_aspect_ratio")) for r in todos.values())}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(principal())
