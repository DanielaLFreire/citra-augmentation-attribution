# Questionário sobre os datasets sintéticos — Genship 3D e iflens

2026-11-10 · cópia versionada do documento enviado às equipes. Respostas recebidas devem ser registradas nas fichas de `docs/fontes/` com data e autor.

## Contexto

Estas perguntas servem para decidir se e como o Genship 3D e o iflens entram em um experimento pré-registrado sobre aumento de dados para detecção de embarcações no CITRA-3D-Real. O experimento compara três tipos de fonte (imagens reais públicas, renderizadas por simulador e geradas por IA) e investiga quais características das imagens determinam o ganho ou a perda de desempenho.

As perguntas partem de um inventário dos dois pacotes (`Genship_3D.zip` e `iflens.rar`): árvore de pastas, contagens, resoluções e amostras de rótulos. Nenhuma imagem foi inspecionada visualmente.

**Como responder:** uma ou duas frases por pergunta bastam. "Não sei" e "não foi registrado" são respostas úteis. As perguntas marcadas com ★ bloqueiam o desenho do experimento e têm prioridade.

## Genship 3D (simulador GenShip)

O pacote tem 444 imagens PNG de 1920×1080 e 433 rótulos, em pastas por classe (Barca, Lancha, Passageiro) e condição (Amanhecer, Manha, Entardecer, Thermal).

### Geração

1. ★ Qual é a versão do GenShip e sobre qual motor gráfico ele roda? O projeto e os modelos 3D estão disponíveis para novas renderizações?
2. ★ Quais parâmetros podem ser controlados na renderização: distância, altura e campo de visão da câmera, hora do dia, clima, estado do mar, número, tipo e posição das embarcações?
3. ★ Os parâmetros de cada imagem foram gravados em algum arquivo, além do que aparece no nome? É possível renderizar um conjunto novo gravando todos os parâmetros por imagem?
4. O que significa cada campo do nome, por exemplo `Barca_0462_289YD_RainOFF_DirtON_TerrenoON`? `YD` é distância em jardas até qual objeto? O que são `Dirt` e `Terreno`?
5. Existem imagens com `RainON`, `DirtOFF` ou `TerrenoOFF`? Na amostra só apareceu a combinação `RainOFF_DirtON_TerrenoON`.
6. As imagens com índices consecutivos e a mesma distância (por exemplo `0457` a `0465`, todas `289YD`) são quadros de uma mesma sequência? Quantas cenas independentes existem?
7. A cena reproduz o local e a câmera do CITRA-3D-Real (posição, altura, zoom)? Com que fidelidade?
8. Como a pasta `Thermal` foi produzida: simulação de sensor térmico ou filtro sobre a imagem visível?

### Anotação

9. ★ As caixas foram geradas automaticamente pelo simulador? A partir de quê: projeção da caixa 3D do modelo ou contorno da máscara renderizada (caixa justa)?
10. Como são tratadas embarcações parcialmente ocultas, cortadas pela borda ou muito pequenas? Existe tamanho mínimo para receber caixa?
11. Qual é a tabela de classes? As pastas `Barca` e `Lancha` usam o mesmo índice `1`, e `Passageiro` usa `4`.
12. Há 444 imagens e 433 rótulos. As 11 imagens sem rótulo são cenas sem embarcação ou falha de exportação?

## iflens (IA generativa)

Versão reduzida, depois das primeiras respostas da equipe e da leitura do código em [github.com/Starblessed/iflens](https://github.com/Starblessed/iflens) (commit `beb5e7d`, 15/09/2026). O entendimento atual é que o iflens faz edição generativa de imagens reais: um modelo de visão classifica as condições da imagem original, a ferramenta sorteia uma variação dessas condições, e o Gemini edita a imagem sem alterar a composição. Os rótulos são os da imagem original, e o SAM 3 foi usado só para detectar alucinações e deslocamento de objetos.

O pacote `iflens.rar` tem cerca de 34,7 mil imagens em três árvores (`input/`, `dataset/feitos/` por classe e `dataset/consolidado/` com 21 classes), das quais 34.557 são JPG e 181 são PNG. Os nomes e as classes não são do CITRA-3D-Real. *(Atualização de 10/11/2026: segundo a equipe, são imagens coletadas da internet por outro colaborador; o pacote saiu do experimento.)*

### Bloqueiam o desenho do experimento

1. ★ Onde estão as imagens geradas a partir do CITRA-3D-Real, quantas são, e de quais splits (train, val, test) vieram as originais? Existe uma lista que ligue cada imagem gerada à sua original?
2. ★ O que são as cerca de 17 mil imagens de `dataset/feitos` e `dataset/consolidado`: imagens originais coletadas, ou saídas do Gemini convertidas para JPG? De onde vieram as originais (quais datasets ou sites)?
3. ★ Qual arquivo YAML de condições foi usado para embarcações? Os logs de console, com a condição original e a variação sorteada de cada imagem, foram guardados?
4. ★ Como funcionou a checagem com SAM 3: qual foi o critério para rejeitar uma imagem, e que fração das imagens geradas foi rejeitada? O código dessa checagem está disponível?
5. ★ Qual é a resolução de saída do Gemini para as imagens 1920×1080 do CITRA? A proporção da imagem é preservada?

### Necessárias para o artigo

6. Qual modelo do Gemini foi de fato usado, e em que período? O código traz como padrão `gemini-3.1-flash-lite-image`, mas o valor é editável.
7. Como foram feitos os splits train/valid/test do `consolidado`? A versão editada de uma imagem pode ter caído em um split diferente do da original?

## Para as duas equipes

1. Os datasets podem ser descritos e, idealmente, disponibilizados em uma publicação? Há restrição institucional ou de licença (modelos 3D, termos de uso do Gemini, imagens de terceiros)?
2. Existe relatório, artigo ou documentação interna sobre a geração que possa ser citado?
3. O dataset já foi usado para treinar algum detector avaliado no CITRA? Com que resultado?
4. Quem é a pessoa de contato para dúvidas técnicas e, no caso do GenShip, para solicitar novas renderizações?


## Divisão dos splits do CITRA (para quem criou train/val/test)

**Por que perguntamos.** Os nomes dos arquivos do CITRA-3D-Real trazem data e hora. Ao medir o intervalo entre os quadros, vimos que os 27 dias de captura aparecem nos três splits (train 1.348, val 332, test 401) e que o quadro de treino mais próximo de cada quadro de teste está, em mediana, a 55 segundos (54% a até 60 s, 96% a até 5 min, mínimo de 8 s). Isso sugere que a divisão foi feita por quadro, não por período, e quadros vizinhos de uma mesma cena podem estar dos dois lados. Isso não invalida o trabalho, mas um revisor vai perguntar, e queremos descrever o que de fato foi feito.

**Perguntas**

1. Como foi feita a divisão em treino, validação e teste? (Aleatória por quadro? Estratificada por algum atributo? Por vídeo, sequência ou dia?) Pode nos enviar o script ou o procedimento e a semente aleatória, se houver?
2. Havia alguma regra para impedir que quadros vizinhos no tempo ficassem em splits diferentes? Se sim, qual?
3. De onde vêm os quadros? São extraídos de vídeo contínuo, com que intervalo (os quadros vizinhos ficam em mediana a cerca de 1 minuto)? Houve algum filtro de seleção, por exemplo só quadros com embarcação visível?
4. Existe um identificador de gravação, sessão, câmera ou ponto de vista (além da data)? Há mais de uma câmera ou posição?
5. Existe metadado de condição por dia ou por gravação (clima, luz, maré, tráfego)?
6. Esta divisão foi usada por outras equipes ou em outros trabalhos? Se o teste já foi usado, saberíamos quantas vezes?
7. Seria possível refazer a divisão em blocos de dias (por exemplo, separar alguns dias inteiros para teste)? Há restrições, como dias raros com condições específicas que precisem ficar no treino?
