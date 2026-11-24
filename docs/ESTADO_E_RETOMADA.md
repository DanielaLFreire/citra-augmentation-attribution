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
4. Fumaça de R (`--fumaca`), depois as 10 sementes (7, 42, 123, 2024, 31415, 101, 1001, 2025, 4242, 27182) com `scripts.executar_treino` (`--braco R --plano principal`); depois as 5 sementes novas do C (`--braco C`).
   Antes de qualquer uso do teste: escrever e registrar `scripts/avaliar_teste.py`; o teste só é avaliado depois de lacrado o 4a (D51).
5. Colar a saída aqui; o registro e a D51 saem daí.

## Se o Colab cair no meio
- Cada execução grava em pasta própria no Drive e só entra em `runs/REGISTRO_EXECUCOES.csv` no fim. Reexecutar o mesmo loop **pula as sementes concluídas**.
- Uma semente interrompida não retoma de onde parou: apague a pasta incompleta no Drive (ou mova) e rode de novo; a regra do adendo (seção 8) trata isso como falha técnica, mesma semente e configuração.
- `/content` some quando a sessão cai: a materialização de R precisa ser refeita (minutos).
- Cada execução leva cerca de 0,6 h na A100; cinco sementes, cerca de 3 h.

## Atualização de 23/11/2026 (noite): réplica de C na L4 e instrumentos do estágio 1

- Retreino das 5 sementes de C da A100 (7, 42, 123, 2024, 31415) na L4, plano `principalL4`, ids `C_principalL4_yolo11n_seed{s}`, mesma lista `manifests/lista_treino_C.csv` e mesma configuração. Se o Colab cair, a semente interrompida não deixa pasta de destino: basta rodar a célula de novo, que pula as sementes já concluídas. Depois de terminar, recuperar as linhas de `registro_execucao.csv` de cada pasta (como foi feito com R) e commitar `runs/REGISTRO_EXECUCOES.csv`.
- Escritos e testados, ainda **sem hash registrado** (registrar depois do ensaio na validação): `avaliar_teste_v3.py`, `verificar_condicoes_etapa1.py`, `analisar_hardware.py`, `bootstrap_imagens.py`.
- Ordem seguinte: ensaio do v3 na validação com os 25 modelos; ensaio do analisador de hardware e do bootstrap sobre as predições; registrar os hashes (D60); lacrar o 4b; fechar o 4a e redigir o adendo do G (nome `adendo4c_genship.md`); etiquetas `lacre-adendo4`, `lacre-adendo4b`, `lacre-adendo4a`, `lacre-adendo4c`; só então o estágio 1.

## Atualização de 24/11/2026 (noite)
- Adendo 4a LACRADO (D64), commit `d644c32`, sha256 `7dcc1da1…ff73`. Etiqueta `lacre-adendo4a` existe só no clone local; Daniela publica pelo GitHub (Releases, branch `ref-lacre-adendo4a`).
- Regra de uso do E: sensibilidade do filtro ≥ 80% e taxa residual ≤ 7% (D63). Produção do E, calendário e auditoria de 100 imagens estão no 4a (seções 10 e 11).
- Rascunhos não lacrados: 4b (dois estágios) e 4c (GenShip, 6 pendências; esperando o João até 02/12 ou piloto próprio).
- Próximos passos: script de sorteio das 150 (semente 20261201) e lista elegível com hash; filtro congelado e registrado até 30/11; classificação e geração das 150 de 01/12 a 04/12; lacrar o 4b quando Daniela disser.
- (24/11, noite) Etiqueta `lacre-adendo4a` publicada e conferida (aponta para `d644c32`). Sorteio das 150 feito e registrado (D65): `manifests/amostra_4a_seed20261201.csv`, lista elegível de 1.370 em `manifests/lista_elegivel_4a.csv`. Próximos: filtro congelado e registrado até 30/11; sorteio das condições; classificação (Groq) e geração das 150 de 01/12 a 04/12; planilhas cegas.
