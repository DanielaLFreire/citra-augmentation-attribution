"""Nome de arquivo seguro derivado de um id de imagem (os ids externos trazem ':' e '/')."""
import re


def nome_seguro(id_imagem: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", id_imagem)
