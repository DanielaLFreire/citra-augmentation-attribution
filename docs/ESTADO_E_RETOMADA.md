# Estado do experimento e como retomar (atualizado em 21/11/2026)

## Onde paramos
- Braço C: 5 sementes concluídas e registradas (D48). Teste não avaliado.
- Braço R: lista e lista de treino prontas e registradas (D49); imagens ainda não materializadas; **não treina antes do lacre**.
- Adendo 4: rascunho em `docs/pre_registro/adendo4_fontes_aumento.md` (D50). Falta Daniela aprovar o texto.
- Adendo 4a (iflens): rascunho com decisões pendentes; só precisa ser lacrado antes de treinar E.

## Retomada, em ordem
1. Daniela lê o adendo 4 e aprova ou corrige.
2. Remover a linha "Estado: RASCUNHO", rodar `python -m scripts.lacrar_adendo docs/pre_registro/adendo4_fontes_aumento.md`, `make check`, commit e push (o commit público é o lacre).
3. No Colab, materializar as externas de R (uma linha por comando, em `%%bash`):
   `python -m scripts.materializar_externas --lista manifests/lista_R_seed20261121.csv --pacote aboships=/content/drive/MyDrive/PROJETO_MARINHA/Datasets/_zips/ABOships.zip:abocsv --pacote smd=/content/drive/MyDrive/PROJETO_MARINHA/Datasets/_zips/smd_clean.zip:yolo --saida /content/externas_R`
4. Fumaça de R (`--fumaca`), depois as sementes 42, 7, 123, 2024, 31415 com `scripts.executar_treino` (`--braco R --plano principal`).
5. Colar a saída aqui; o registro e a D51 saem daí.

## Se o Colab cair no meio
- Cada execução grava em pasta própria no Drive e só entra em `runs/REGISTRO_EXECUCOES.csv` no fim. Reexecutar o mesmo loop **pula as sementes concluídas**.
- Uma semente interrompida não retoma de onde parou: apague a pasta incompleta no Drive (ou mova) e rode de novo; a regra do adendo (seção 8) trata isso como falha técnica, mesma semente e configuração.
- `/content` some quando a sessão cai: a materialização de R precisa ser refeita (minutos).
- Cada execução leva cerca de 0,6 h na A100; cinco sementes, cerca de 3 h.
