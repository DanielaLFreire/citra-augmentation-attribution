# Definições da auditoria (v4, 2026-11-18)

Motivo da revisão: no piloto, dois avaliadores independentes divergiram nas caixas (kappa 0,27 em 6 categorias; José 13 `alterada`, Daniela 2) porque "alterada" não separava "é outro objeto" de "é o mesmo, mas borrado". Esta versão separa os dois casos. Definida antes de qualquer dado confirmatório.

## Por caixa (compare original e gerada; uma categoria)
- `valida`: o mesmo objeto, reconhecível, está dentro da caixa nas duas imagens.
- `degradada` (nova): o mesmo objeto, ainda reconhecível como embarcação na gerada, dentro da caixa, mas com perda de nitidez ou detalhe (borrado, menos contraste).
  **Limiar:** marque `degradada` quando a perda de nitidez é suficiente para a embarcação poder ser confundida com o fundo ou a paisagem. Perda leve, em que a embarcação segue claramente distinguível, é `valida` (pode anotar "pouca nitidez" em `observacao`).
- `apagada`: na gerada não se reconhece embarcação dentro da caixa. **Teste prático:** sem ver a caixa, você diria que há uma embarcação ali? Se não, é `apagada`, mesmo que reste uma mancha.
- `deslocada`: a mesma embarcação aparece na gerada, mas fora da caixa (a caixa não a cobre mais).
- `alterada`: o objeto da gerada é **outro** (forma, tipo ou tamanho muito diferentes). Perda de nitidez sozinha NÃO é `alterada`.
- `sem_objeto_original`: a caixa do ORIGINAL já não tinha objeto (ruído herdado do rótulo).
- `nao_avaliavel`: alvo pequeno demais para decidir (explique em `observacao`).

## Por imagem (0 ou 1)
- `objeto_adicionado`: a gerada tem embarcação, boia ou outro objeto que NÃO existe no original. Mudança do fundo (por exemplo, prédios ou relevo diferentes) NÃO é objeto adicionado. Registre o tipo em `tipo_objeto_adicionado`: `embarcacao`, `boia`, `ave`, `pessoa` ou `outro`.
- `original_sem_rotulo`: o original tem embarcação visível sem caixa (ruído herdado).

## Desfecho primário (pré-especificado)
Imagem **reprovada** se tiver alguma caixa `apagada`, `deslocada` ou `alterada`, ou **embarcação adicionada**.
## Desfecho secundário e sensibilidade
- Taxa de caixas/imagens com `degradada`, relatada sempre.
- Sensibilidade: repetir a taxa de reprovação contando `degradada` como falha.
- Boia, ave, pessoa e outros objetos adicionados: descritivo, fora do primário.

## Dois avaliadores
Regra primária: reprovada se **qualquer** avaliador marcar. Sensibilidade: reprovada só se **ambos** marcarem. Relatar as duas taxas e o kappa (comum e ajustado à prevalência). Cada avaliador preenche sozinho, sem ver a resposta do outro.
