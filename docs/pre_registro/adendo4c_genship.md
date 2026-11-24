# Adendo 4c (RASCUNHO, NÃO LACRADO): braço G, renderizações do GenShip

Estado: esqueleto de 2026-11-24. Os pontos que dependem de Daniela ou do João estão marcados com o marcador de pendência, e `scripts/lacrar_adendo.py` recusa lacrar enquanto houver algum. Este adendo fixa o protocolo do braço G antes de qualquer imagem do conjunto final ser gerada e antes de se conhecer o resultado de R no teste. Origem: D14, D24, A17, A19, A22 e as respostas do João (`data/respostas_equipes/Joao_2026-11-23_resumo.md`, ficha `docs/fontes/FICHA_genship3d.md`).

## 1. O que este adendo decide
O G só entra se houver pelo menos 1.370 imagens distintas válidas até 30/12/2026 (Brasília). Este texto fixa a versão da ferramenta, o plano de cenas, a regra de seleção e de validade, e como o G é relatado. As 444 imagens antigas não treinam o G (D14).

## 2. Gerador e versão
- Quem gera: DECISÃO PENDENTE (João, ou Daniela com o executável, se o João não se comprometer com data e quantidade até 02/12/2026).
- Versão: o executável é fixado por hash SHA-256 e nome de release, e a versão não muda durante a geração: DECISÃO PENDENTE (versão e hash). O tutorial lido é o da v0.1.0-alpha, e os controles descritos nele (horário Sunrise/Morning/Afternoon, ondas, nuvens) não coincidem com os da resposta do João de 16/11 (Sunny/Sunrise/Sunset, `Rain`, `Dirt`, `Terrain`); a versão fixada precisa ser a que de fato gera o conjunto.
- Só RGB. O modo "térmico" é um mapeamento em tons de cinza (A18) e não entra.
- Parâmetros por imagem: se o João gerar com a versão recompilada, exporta-se um `.json` por imagem (câmera, FOV, perfil solar, mar, posição e distância de cada embarcação). Se a geração usar o executável público, os parâmetros por imagem são o nome do arquivo e a tabela de cenas da seção 3, e a análise de atribuição do G fica restrita a esses campos. DECISÃO PENDENTE (qual dos dois casos vale).

## 3. Plano de cenas (fixado antes de gerar)
- Unidade independente: a cena (uma instanciação da frota e uma captura sequencial), não a imagem. Na amostra antiga, 430 das 433 imagens estavam em grupos de 2 a 12 imagens da mesma cena (~55 cenas). O número de imagens por cena é fixado na tabela abaixo e o de cenas é o necessário para ≥ 1.370 imagens, com margem de 10%.
- Imagens por cena: DECISÃO PENDENTE (valor, a medir no piloto).
- A tabela de cenas é sorteada com semente 20261203 a partir de faixas registradas antes de gerar: classe (Barca, Lancha, Passageiro, em proporção igual), número de embarcações, distância entre embarcações, distância de geração, altura da câmera, FOV, horário (só os perfis diurnos disponíveis na versão fixada), intensidade das ondas, nuvens, chuva, sujeira na lente e relevo. Faixas: DECISÃO PENDENTE (propostas a partir do piloto, com os mesmos critérios de fidelidade ao CITRA para todas as cenas). A tabela e o hash dela são registrados antes da primeira imagem do conjunto final.
- As cenas são executadas na ordem da tabela, sem escolha manual de parâmetros nem de enquadramento além do que a tabela prescreve.
- Piloto (cerca de 50 imagens, para medir tempo e conferir formato): fica fora do G e é descrito na decisão que o registra.

## 4. Validade e seleção
- Imagem válida: PNG legível, 1920×1080, com arquivo de rótulo existente, com pelo menos 1 caixa e com SHA-256 diferente de todas as outras. Imagens sem caixa são contadas e relatadas, mas não entram no G.
- Proibido apagar imagens por aparência ou por qualidade, inclusive pelo botão de auditoria do GenShip. Só se descarta arquivo corrompido ou faltante, com registro. O conjunto do G é formado pelas **primeiras 1.370 imagens válidas na ordem da tabela de cenas**.
- Rótulos: o que a versão fixada exporta. Mapeiam-se todas as classes para a classe única (D12). Embarcações presentes e suprimidas ficam sem rótulo (caixa menor que 5 px, oclusão, brilho solar, corte no FOV), e isso é declarado como ruído de rótulo do G.

## 5. Contagem e plano reserva
Ao fim de 30/12/2026 (Brasília) conta-se as válidas. Com 1.370 ou mais, vale o desenho principal. Com menos: DECISÃO PENDENTE (o G sai do experimento, como na D24, ou, se o plano reserva da D36 estiver em vigor por causa do E, valem as primeiras 454 válidas na mesma ordem).

## 6. Como o G é relatado
- Convenção de caixa (A19): medida em 30 imagens sorteadas do conjunto final, avaliadas por Daniela (caixa inclui mastro ou não, comparada às do CITRA). Descritiva e usada só na atribuição.
- A incerteza do G é por cena, não por imagem, e o número de cenas distintas é dito junto de qualquer resultado.
- O G é domínio sintético: um resultado do G mede o efeito dessa fonte com essa ferramenta, versão, convenção de caixa e plano de cenas, e não de imagens sintéticas em geral.
- Licença e crédito (A22): os modelos 3D são dos artistas do SIMPASS, e a licença deles está pendente. O conjunto G não é divulgado até isso ser resolvido, e o artigo registra a autoria e a fonte.

## 7. Desvios
Qualquer mudança é registrada em `docs/DESVIOS.md` com data e motivo. Este documento não é editado depois de lacrado.
