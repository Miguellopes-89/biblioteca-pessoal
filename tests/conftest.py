"""Configuração partilhada dos testes.

O pytest carrega este ficheiro automaticamente antes de qualquer teste.
"""

from pathlib import Path

import pytest

import database


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Dá a CADA teste uma base de dados nova e vazia, num ficheiro temporário.

    - tmp_path: pasta temporária única por teste, apagada pelo pytest depois.
    - monkeypatch.setattr: troca database.DB_NAME só durante este teste e
      repõe o valor original no fim. connect() lê DB_NAME no momento em que é
      chamada, por isso a troca tem efeito em todas as funções do módulo.
    - autouse=True: aplica-se a todos os testes sem terem de a pedir. É uma
      rede de segurança: nenhum teste consegue tocar por engano no
      biblioteca.db real.
    """
    monkeypatch.setattr(database, "DB_NAME", str(tmp_path / "test.db"))
    database.create_tables()
