# Checklist de reprodutibilidade (para o artigo e para o revisor)

Marcar só com evidência apontada. Itens baseados em práticas usuais de checklists de reprodutibilidade em aprendizado de máquina.

- [ ] Código com commit/tag citado no texto
- [ ] Ambiente: versões de Python, PyTorch, Ultralytics, CUDA e GPU em `runs/REGISTRO_EXECUCOES.csv`
- [ ] Manifestos de treino com SHA-256 registrado antes do primeiro treino
- [ ] Lista de seeds fixada no adendo lacrado e todas reportadas
- [ ] Orçamento de passos e hiperparâmetros por braço em arquivo de configuração versionado
- [ ] Regra de decisão e métrica primária declaradas antes dos resultados
- [ ] Teste avaliado uma vez, com guarda; lista de modelos fixada
- [ ] Todas as comparações realizadas reportadas (não só as significativas)
- [ ] Intervalos de confiança e tamanho de efeito, não só valor-p
- [ ] Desvios do pré-registro listados em `docs/DESVIOS.md`
- [ ] Proveniência e licença de cada fonte em `docs/fontes/`
- [ ] Verificação de vazamento entre fontes e val/test por hash de conteúdo
- [ ] Auditoria de rótulos de imagens geradas descrita, com concordância entre avaliadores
- [ ] Modelo generativo (nome, versão, data de uso) e prompts arquivados
- [ ] Disponibilidade dos dados: o que pode ser publicado, o que não pode e por quê
