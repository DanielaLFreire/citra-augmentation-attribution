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

Plano para o braço G: renderizar conjunto novo com parâmetros sorteados por plano e gravados por imagem (depende das respostas 1–3 do questionário).

**Pacote adicional `genship3d-mirror.zip` (inventário de 2026-11-11):** 450 PNG (444 imagens mais 6 figuras de relatório), 1.299 `.txt`, pasta `quarantine` (11 arquivos), `audit_report.json`, `confirmation_report.csv`, `detection_report.csv` e segmentações em `.cache`. Parece uma versão já auditada do Genship; quem a produziu, com que critério e o que a quarentena contém são **desconhecidos** até ler os relatórios (decisão A11).
