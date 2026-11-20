# Configurações

Arquivos de configuração de treino e de análise, versionados. O hash de cada um entra em `runs/REGISTRO_EXECUCOES.csv`. 

- `treino_yolo11n_d43.yaml`: hiperparâmetros de todas as execuções do experimento (D35, D42, D43); `data`, `project`, `name` e `seed` vão em cada execução.
- `treino_yolo11n_f5_reproducao.yaml`: a configuração exata da Fase 5 (S2), só para a checagem de reprodutibilidade da D09 (C na divisão antiga).
- Versão do Ultralytics fixada em 8.4.165 (`requirements-colab.txt`).
