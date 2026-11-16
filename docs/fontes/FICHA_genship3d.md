# Ficha da fonte: Genship 3D (renderizada, simulador GenShip)

| Campo | Valor | Quem informou / como foi verificado | Data |
| --- | --- | --- | --- |
| Tipo | Renderizada | Inventário do pacote | 2026-11-10 |
| Origem e citação | Simulador GenShip, equipe interna do grupo | Questionário pendente | — |
| Licença / restrições | **desconhecido** (modelos 3D) | Questionário, comum Q1 | — |
| Nº de imagens e de caixas | 444 PNG 1920×1080; 433 arquivos de rótulo (11 imagens sem rótulo) | Inventário | 2026-11-10 |
| Formato dos rótulos e classes | YOLO. Pastas Barca e Lancha usam índice 1; Passageiro usa 4. **Tabela de classes desconhecida** | Inventário | 2026-11-10 |
| Como as caixas foram obtidas | **desconhecido** (projeção da caixa 3D ou máscara renderizada) | Questionário Genship Q9 | — |
| Resolução, câmera, domínio | 1920×1080. Pastas por classe (Barca, Lancha, Passageiro) e condição (Amanhecer, Manha, Entardecer, Thermal). Fidelidade à câmera do CITRA **desconhecida** | Inventário | 2026-11-10 |
| Duplicatas / sobreposição com CITRA | não aplicável (render); quadros consecutivos de mesma sequência prováveis (**desconhecido**) | Questionário Genship Q6 | — |
| Parâmetros por imagem registrados? | Só o que aparece no nome (`Barca_0462_289YD_RainOFF_DirtON_TerrenoON`); significado dos campos **desconhecido** | Questionário Genship Q3–Q4 | — |
| Hash do pacote bruto | a registrar | — | — |
| Manifesto | a gerar (`scripts/perfil_sinteticos.py` produz o perfil estrutural) | — | — |
| Problemas conhecidos | Variação de nome só observada em `RainOFF_DirtON_TerrenoON` na amostra | — | — |

Plano para o braço G: renderizar conjunto novo com parâmetros sorteados por plano e gravados por imagem. Respostas recebidas em 2026-11-16 (seção abaixo): só há executável; o JSON por imagem depende de recompilar com a equipe do GenShip (A17).

**Pacote adicional `genship3d-mirror.zip` (inventário de 2026-11-11):** 450 PNG (444 imagens mais 6 figuras de relatório), 1.299 `.txt`, pasta `quarantine` (11 arquivos), `audit_report.json`, `confirmation_report.csv`, `detection_report.csv` e segmentações em `.cache`. Parece uma versão já auditada do Genship; quem a produziu, com que critério e o que a quarentena contém são **desconhecidos** até ler os relatórios (decisão A11).

## Respostas do responsável pelo GenShip (João; PDF recebido em 2026-11-16; `data/respostas_equipes/`)

Afirmações da equipe. As conferências marcadas com **[medido]** vêm de `data/relatorios_fontes/genship3d_detection_report.csv` (433 imagens com rótulo, 1.772 caixas do `.txt`).

| Tema | Resposta | Consequência |
| --- | --- | --- |
| Motor (Q1) | Unity 6 (6000.3.0f1), HDRP, `WaterSurface`. No Git só o **executável compilado**; os modelos 3D e o código não estão no repositório | Nova renderização depende da equipe do GenShip; não podemos recompilar |
| Parâmetros (Q2) | Ajustáveis em tempo de execução pela interface: posição e altitude da câmera, pan, tilt, FOV (base 60°), captura orbital (n por órbita), 3 perfis de hora (Sunny, Sunrise, Sunset) com brilho solar e *washout*, chuva/neblina (`Rain`), sujeira na lente (`Dirt`), relevo de fundo (`Terrain`), visibilidade global (padrão 6.000 m), heave/pitch/roll dos cascos, classes, quantidade, raio de geração, raio mínimo, distância anti-colisão, proa aleatória | Sem noite. Não há menção a modo sem interface nem a semente da cena |
| Metadados (Q3) | Só no nome do arquivo e nos `.txt` YOLO. Exportar `.json` por imagem (câmera, FOV, perfil solar, alinhamento com o sol, mar, posição e distância de cada embarcação) é "viável com poucas linhas" em `ExtractDatasetYOLO.cs` | Pedir o JSON na nova extração (ver A17) |
| Nome (Q4) | `Barca_0462_289YD_RainOFF_DirtON_TerrenoON`: classe da embarcação de referência, contador global, distância em jardas até a **primeira** embarcação da lista (`allVessels[0]`), chuva, sujeira na lente, relevo | A distância não descreve as outras embarcações da cena; a hora do dia **não** está no nome |
| Combinações (Q5) | 8 permutações suportadas; no lote só `RainOFF_DirtON_TerrenoON` porque as chaves ficaram fixas | **[medido] contradiz a resposta:** 36 de 433 imagens (8%) têm `RainON` e 397 têm `RainOFF`; `DirtON` e `TerrenoON` em todas. Perguntar ao João |
| Sequências (Q6) | Imagens consecutivas com a mesma distância vêm da mesma cena (órbita ou PTZ/iluminação trocados sobre a mesma frota) | **[medido]** execuções de ids consecutivos com a mesma distância: 55 grupos (mediana 10 imagens, máx. 12; 27 grupos de 12); 430 das 433 imagens estão em grupos com 2 ou mais. **Unidade independente = cena (~55), não imagem**, 45 distâncias distintas |
| Fidelidade (Q7) | "Gêmeo digital" inspirado na Baía de Guanabara: óptica PTZ, brilho solar, névoa, fundo costeiro, ondulação | Alegação de projeto; não medida |
| Thermal (Q8) | Não é simulação térmica: mapeamento de luminância em tons de cinza sobre a cena renderizada | Estilização, não sensor; fora do experimento até decisão (A18) |
| Caixas (Q9) | 100% automáticas, justas à malha 3D: corte na linha d'água, **filtro de antenas e mastros** (na versão atual), projeção dos vértices visíveis | **Convenção de caixa possivelmente diferente da do CITRA** (as caixas de veleiros do CITRA incluem o mastro nas imagens inspecionadas); afeta métricas por IoU (A19) |
| Supressão (Q10) | Sem rótulo: caixa < 5 px; além de 6.000 m; no cone de brilho solar além da distância de lavagem; oclusão ≥ 60% (versão atual) ou base 100% oculta (versão da amostra); cortes no FOV | **[medido]** menor caixa 5,3 × 5,7 px (consistente). Embarcações presentes e suprimidas ficam **sem rótulo** na imagem: falsos negativos de treino. A versão do exportador da amostra difere da atual (oclusão, antenas), então as 444 e uma renderização nova têm política de rótulo diferente |
| Classes (Q11) | Barca e Lancha com o mesmo `yoloID = 1` por erro de configuração; Passageiro = 4; nome da pasta e do arquivo usam o nome da classe | Com rótulo de classe única (D12) não importa; a distinção Barca/Lancha só se recupera pelo prefixo e só para a embarcação de referência |
| Sem rótulo (Q12) | 11 imagens sem `.txt` são amostras negativas (nenhuma embarcação válida) | Tratar como fundo se entrarem no treino |

**[medido]** adicionais: 222 Barca, 119 Lancha, 92 Passageiro; ids de 36 a 732; distância à embarcação de referência de 170 a 1.637 jardas (mediana 518); largura mediana da caixa 84 px e altura 36 px (1920×1080); 37 das 1.772 caixas têm lado menor < 10 px.

### Segunda resposta do João (2026-11-16; `data/respostas_equipes/Respostas_Genship_rodada2_2026-11-16.txt`)
- Nome do arquivo está correto: 36 imagens `RainON` (D22). Nome e pastas de hora são o único registro das condições nas 444; o `.json` com parâmetros de ambiente e câmera está nos planos dele ("futuramente").
- Amostra de 444 gerada com versão anterior (oclusão mais simples). Versão atual: o filtro de antenas e mastros considera a largura da embarcação; em embarcações estreitas ou pequenas (veleiros) o mastro entra na caixa.
- Repositório só para convidados. 444 imagens em ~5 min em i7-12700H, 32 GB, RTX 3060 6 GB, Windows 11.
- **Não respondeu:** lista de embarcações suprimidas com motivo; cenas curtas e numerosas; semente da cena (A17).
- Modelos 3D de dois artistas do projeto SIMPASS; João vai alinhar o crédito com eles. Licença não declarada. Ele planeja artigo sobre o GenShip e liberação no GitHub ou Zenodo (A22).
