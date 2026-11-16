# Proposta de especificação do `.json` por imagem para a nova extração do GenShip

Rascunho de 2026-11-16 para discussão com o João. Objetivo: tornar cada imagem auditável (qual cena, quais parâmetros, quais embarcações foram anotadas e quais foram suprimidas e por quê) sem alterar o formato YOLO dos rótulos. Um arquivo `.json` com o mesmo nome da imagem (ou um manifesto único), fora das pastas usadas pelo treino.

```json
{
  "schema_version": "1",
  "exporter_version": "<tag ou commit do build>",
  "unity_version": "6000.3.0f1",
  "scene_id": "S000123",
  "scene_seed": 123456789,
  "image_index_in_scene": 2,
  "image": "Barca_0462_289YD_RainOFF_DirtON_TerrenoON.png",
  "image_size_wh": [1920, 1080],
  "camera": {"position_xyz": [0, 0, 0], "altitude_m": 0, "pan_deg": 0, "tilt_deg": 0, "fov_deg": 60},
  "environment": {
    "time_profile": "Sunny|Sunrise|Sunset",
    "rain": false, "dirt": true, "terrain": true,
    "fog_visibility_limit_m": 6000,
    "sun_alignment": 0.0,
    "sea_state": {"note": "parâmetros de onda usados"}
  },
  "vessels": [
    {
      "vessel_id": "V01", "class_name": "Barca", "yolo_id": 0,
      "position_xyz": [0, 0, 0], "heading_deg": 0, "distance_m": 0,
      "annotated": true,
      "suppression_reason": null,
      "occlusion_fraction": 0.0,
      "bbox_xyxy_px": [0, 0, 0, 0]
    }
  ]
}
```

Pontos que importam para o experimento:
1. **Todas** as embarcações da cena entram em `vessels`, anotadas ou não. Para as suprimidas, `suppression_reason` ∈ {`below_min_size`, `beyond_fog_limit`, `sun_glare`, `occlusion`, `outside_frustum`} e `bbox_xyxy_px` é a caixa projetada mesmo sem rótulo. Assim identificamos imagens com navio visível e sem caixa (falso negativo de treino) e as descartamos ou mascaramos.
2. `scene_id` e `scene_seed` iguais para as imagens da mesma cena, para tratarmos a cena (e não a imagem) como unidade independente.
3. `exporter_version` fixa e igual em todas as imagens de uma extração.
4. `yolo_id` único por classe (hoje Barca e Lancha dividem o índice 1). Para o experimento o rótulo é de classe única, mas o conflito atrapalha qualquer análise por classe.
5. Distâncias em metros (o nome do arquivo usa jardas até a primeira embarcação).
6. O JSON fica separado dos rótulos, como o João sugeriu, para não "sujar" a pasta de treino.
