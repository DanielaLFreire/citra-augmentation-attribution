from scripts.perfil_alvo_citra import perfil


def test_perfil_basico():
    itens = [
        {"largura": 1920, "altura": 1080, "gt_xyxy": [[0, 0, 30, 30], [100, 100, 400, 300]]},
        {"largura": 1920, "altura": 1080, "gt_xyxy": []},
        {"largura": 1280, "altura": 720, "gt_xyxy": [[10, 10, 40, 30]]},
    ]
    r = perfil(itens)
    assert r["n_imagens"] == 3 and r["n_caixas"] == 3
    assert r["tamanhos_imagem"] == {"1920x1080": 2, "1280x720": 1}
    assert r["caixas_por_imagem"]["sem_caixa"] == 1 and r["caixas_por_imagem"]["max"] == 2
    # 30x30 em 1920 -> escala 1/3 -> 100 px² (small); 300x200 -> 6667 (não); 30x20 em 1280 -> 150 (small)
    assert r["fracao_small_640"] == round(2 / 3, 4)
