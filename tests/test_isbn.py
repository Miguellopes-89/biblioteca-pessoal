"""Testes de validar_isbn(): função pura, sem rede nem base de dados.

Os ISBNs válidos abaixo foram verificados à mão com o algoritmo do dígito
de controlo. Os inválidos são os mesmos números com UM algarismo alterado
— exatamente o tipo de erro de digitação que a validação existe para apanhar.
"""

import pytest

from isbn_lookup import validar_isbn


@pytest.mark.parametrize(
    "isbn",
    [
        "9780132350884",  # ISBN-13 válido
        "978-0-13-235088-4",  # o mesmo, com hífenes
        "978 0 13 235088 4",  # o mesmo, com espaços
        "0132350882",  # ISBN-10 válido
        "080442957X",  # ISBN-10 com dígito de controlo 'X' (vale 10)
        "080442957x",  # 'x' minúsculo também deve ser aceite
    ],
)
def test_valid_isbn(isbn: str) -> None:
    assert validar_isbn(isbn) is True


@pytest.mark.parametrize(
    "isbn",
    [
        "9780132350885",  # ISBN-13 com o último algarismo trocado
        "0132350883",  # ISBN-10 com o último algarismo trocado
        "",  # vazio
        "abc",  # lixo
        "978013235088",  # 12 algarismos: comprimento inválido
        "978013235088X",  # 'X' só é permitido em ISBN-10, na última posição
        "01323508X2",  # 'X' fora da última posição
    ],
)
def test_invalid_isbn(isbn: str) -> None:
    assert validar_isbn(isbn) is False
