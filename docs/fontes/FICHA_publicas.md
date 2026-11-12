# Fichas das fontes reais públicas

| Fonte | Imagens | Formato dos rótulos | Situação | Pendência |
| --- | --- | --- | --- | --- |
| Singapore Maritime Dataset (on-shore) | 914 | YOLO, 7.043 caixas | Só recortes extraídos nas Fases 0–5 | Materializar imagens inteiras; quadros de 36 vídeos, deduplicar por conteúdo |
| SeaShips | 6.979 | VOC XML | Só recortes extraídos | Materializar; objetos grandes |
| ABOShips | 9.880 | CSV | Só recortes extraídos | Materializar; a mais próxima do CITRA em escala |
| InaTechShips | 27.796 | YOLO | Só recortes extraídos | Materializar; fotos próximas, objetos grandes |

Para cada fonte, preencher a ficha no modelo `FICHA_modelo.md` ao materializar (licença, citação, hash do pacote, manifesto com hash de conteúdo por imagem). Perfil estrutural por fonte: `scripts/perfilar_fontes.py` do repositório anterior (tag `v1.1-fase5-fechada`).
