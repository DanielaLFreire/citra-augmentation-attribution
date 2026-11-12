# Pré-registro

O adendo deste experimento (`adendo4_fontes_aumento.md`, a escrever) só pode ser lacrado depois de:

- respostas das equipes do Genship 3D e do iflens (ver `docs/QUESTIONARIO_equipes.md`);
- piloto de métrica concluído (etapa 2 do planejamento) e métrica primária escolhida;
- piloto do braço generativo auditado, se o braço E for mantido (etapa 3);
- manifestos de todas as fontes materializados e com hash registrado.

## Como lacrar

```bash
python -m scripts.lacrar_adendo docs/pre_registro/adendo4_fontes_aumento.md
python -m scripts.registrar_artefato manifests/<manifesto>.csv
git add docs/pre_registro manifests && git commit && git push   # o commit público é a lacração
```

`hashes.json` só recebe entradas novas. `lacrar_adendo.py` recusa adendo com "DECISÃO PENDENTE" ou "___" e recusa re-lacração.
Os adendos 1–3 e as previsões da Fase 0 estão no repositório anterior; seus hashes são repetidos em `docs/pre_registro/herdado_hashes_fases_0_5.json` como referência cruzada.
