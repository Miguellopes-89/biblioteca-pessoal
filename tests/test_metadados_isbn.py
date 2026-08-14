# tests/test_metadados_isbn.py
#
# Testes para metadados_isbn.py. Todos os cenários de rede são
# simulados — a suite nunca contacta a Open Library a sério.

import requests

import metadados_isbn


# --- normalizar_isbn -------------------------------------------------

def test_normalizar_isbn_remove_hifens():
    assert metadados_isbn.normalizar_isbn("978-989-23-1234-5") == "9789892312345"


def test_normalizar_isbn_remove_espacos():
    assert metadados_isbn.normalizar_isbn("978 989 23 1234 5") == "9789892312345"


def test_normalizar_isbn_ja_limpo():
    assert metadados_isbn.normalizar_isbn("9789892312345") == "9789892312345"


# --- procurar_por_isbn -------------------------------------------------

class RespostaFalsa:
    """Simula um objeto requests.Response, só com o que precisamos."""

    def __init__(self, dados_json, status_ok=True):
        self._dados_json = dados_json
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise requests.HTTPError("erro simulado")

    def json(self):
        return self._dados_json


def test_procurar_por_isbn_encontrado_com_autor(monkeypatch):
    isbn = "9789892312345"
    dados_simulados = {f"ISBN:{isbn}": {"title": "Duna", "authors": [{"name": "Frank Herbert"}]}}
    monkeypatch.setattr(
        metadados_isbn.requests, "get", lambda *a, **k: RespostaFalsa(dados_simulados)
    )
    assert metadados_isbn.procurar_por_isbn(isbn) == {"titulo": "Duna", "autor": "Frank Herbert"}


def test_procurar_por_isbn_encontrado_varios_autores(monkeypatch):
    isbn = "9789892312345"
    dados_simulados = {
        f"ISBN:{isbn}": {
            "title": "Bom Presságio",
            "authors": [{"name": "Terry Pratchett"}, {"name": "Neil Gaiman"}],
        }
    }
    monkeypatch.setattr(
        metadados_isbn.requests, "get", lambda *a, **k: RespostaFalsa(dados_simulados)
    )
    resultado = metadados_isbn.procurar_por_isbn(isbn)
    assert resultado["autor"] == "Terry Pratchett, Neil Gaiman"


def test_procurar_por_isbn_encontrado_sem_autor(monkeypatch):
    isbn = "9789892312345"
    dados_simulados = {f"ISBN:{isbn}": {"title": "Livro Anónimo"}}
    monkeypatch.setattr(
        metadados_isbn.requests, "get", lambda *a, **k: RespostaFalsa(dados_simulados)
    )
    assert metadados_isbn.procurar_por_isbn(isbn) == {"titulo": "Livro Anónimo", "autor": None}


def test_procurar_por_isbn_nao_encontrado(monkeypatch):
    """A API responde, mas sem dados para este ISBN (chave ausente)."""
    monkeypatch.setattr(metadados_isbn.requests, "get", lambda *a, **k: RespostaFalsa({}))
    assert metadados_isbn.procurar_por_isbn("0000000000000") is None


def test_procurar_por_isbn_sem_titulo_e_tratado_como_nao_encontrado(monkeypatch):
    isbn = "9789892312345"
    dados_simulados = {f"ISBN:{isbn}": {"authors": [{"name": "Autor Sem Título"}]}}
    monkeypatch.setattr(
        metadados_isbn.requests, "get", lambda *a, **k: RespostaFalsa(dados_simulados)
    )
    assert metadados_isbn.procurar_por_isbn(isbn) is None


def test_procurar_por_isbn_string_vazia_nao_faz_pedido_de_rede(monkeypatch):
    chamadas = []
    monkeypatch.setattr(
        metadados_isbn.requests, "get",
        lambda *a, **k: chamadas.append(1) or RespostaFalsa({}),
    )
    assert metadados_isbn.procurar_por_isbn("") is None
    assert chamadas == []  # confirma que nem tentou contactar a API


def test_procurar_por_isbn_erro_de_rede_devolve_none(monkeypatch):
    def get_falha(*a, **k):
        raise requests.ConnectionError("sem ligação simulada")
    monkeypatch.setattr(metadados_isbn.requests, "get", get_falha)
    assert metadados_isbn.procurar_por_isbn("9789892312345") is None


def test_procurar_por_isbn_timeout_devolve_none(monkeypatch):
    def get_timeout(*a, **k):
        raise requests.Timeout("timeout simulado")
    monkeypatch.setattr(metadados_isbn.requests, "get", get_timeout)
    assert metadados_isbn.procurar_por_isbn("9789892312345") is None


def test_procurar_por_isbn_resposta_http_erro_devolve_none(monkeypatch):
    monkeypatch.setattr(
        metadados_isbn.requests, "get", lambda *a, **k: RespostaFalsa({}, status_ok=False)
    )
    assert metadados_isbn.procurar_por_isbn("9789892312345") is None
