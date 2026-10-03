"""Testes de normalize_text(): base da pesquisa insensível a acentos,
maiúsculas e pontuação. Função pura, sem base de dados."""

import pytest

from database import normalize_text


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("É, Um Ólá!", "e um ola"),  # o exemplo do docstring
        ("Saramago, José", "saramago jose"),  # acentos e vírgula
        ("O'Brien", "obrien"),  # apóstrofo é removido, não substituído por espaço
        ("  muitos   espaços  ", "muitos espacos"),  # colapsa e apara espaços
        ("Ação", "acao"),  # cedilha e til
        ("", ""),  # vazio continua vazio
        (None, ""),  # None é aceite e dá string vazia
    ],
)
def test_normalize_text(entrada: str | None, esperado: str) -> None:
    assert normalize_text(entrada) == esperado
