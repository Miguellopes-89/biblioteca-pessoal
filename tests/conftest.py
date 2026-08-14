# tests/conftest.py
#
# Fixtures partilhadas por toda a suite de testes. A mais importante
# aqui garante que os testes nunca tocam na base de dados real do
# utilizador (data/biblioteca.db) — cada teste que precisa de base de
# dados recebe uma cópia limpa e temporária.

import sys
from pathlib import Path

import pytest

# Garante que "import database" funciona quando o pytest corre a
# partir da raiz do projeto (onde estão database.py, constantes.py, etc.)
sys.path.insert(0, str(Path(__file__).parent.parent))

import database


@pytest.fixture
def bd_temporaria(tmp_path, monkeypatch):
    """
    Redireciona CAMINHO_BD para um ficheiro temporário, isolado por
    teste (tmp_path é uma pasta única fornecida pelo pytest para cada
    teste, apagada automaticamente no fim). Isto evita qualquer risco
    de um teste apagar ou corromper a biblioteca real do utilizador.
    """
    caminho_temporario = tmp_path / "teste_biblioteca.db"
    monkeypatch.setattr(database, "CAMINHO_BD", caminho_temporario)
    database.criar_tabela()
    yield
