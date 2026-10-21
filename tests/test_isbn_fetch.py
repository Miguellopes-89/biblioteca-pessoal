"""Testes do parsing das respostas da Google Books e da Open Library.

Nenhum teste toca na rede: a fixture no_network (autouse) troca _pedir_bytes
por uma função que rebenta, e cada teste troca _pedir_json por uma versão
falsa que devolve um dict escrito à mão (a "resposta simulada").

As respostas simuladas seguem a estrutura documentada de cada API, com os
dados do ISBN 9780132350884 ("Clean Code"). Só têm os campos que o código
lê, mais um ou dois que ele deve ignorar. NÃO foram copiadas de uma resposta
real: a sessão em que foram escritas não tinha acesso às duas APIs.
"""

from typing import Any

import pytest

import isbn_lookup

ISBN = "9780132350884"


# ---------- respostas simuladas ----------

def google_response() -> dict[str, Any]:
    """Resposta típica de GET /books/v1/volumes?q=isbn:... com 1 resultado.

    É uma função (e não uma constante) para cada teste receber uma cópia
    nova, que pode alterar à vontade sem afetar os outros testes.
    """
    return {
        "kind": "books#volumes",
        "totalItems": 1,
        "items": [
            {
                "kind": "books#volume",
                "id": "hjEFCAAAQBAJ",
                "volumeInfo": {
                    "title": "Clean Code",
                    "subtitle": "A Handbook of Agile Software Craftsmanship",
                    "authors": ["Robert C. Martin"],
                    "publisher": "Pearson Education",
                    "publishedDate": "2008-08-01",
                    "categories": ["Computers"],
                    "imageLinks": {
                        "smallThumbnail": "http://books.google.com/books/content?id=hjEFCAAAQBAJ&zoom=5",
                        "thumbnail": "http://books.google.com/books/content?id=hjEFCAAAQBAJ&zoom=1",
                    },
                    "language": "en",
                },
            }
        ],
    }


def open_library_response() -> dict[str, Any]:
    """Resposta típica de GET /api/books?bibkeys=ISBN:...&format=json&jscmd=data.

    A chave de topo é "ISBN:<isbn>", exatamente como foi pedida em bibkeys.
    """
    return {
        f"ISBN:{ISBN}": {
            "url": "https://openlibrary.org/books/OL22109286M/Clean_code",
            "key": "/books/OL22109286M",
            "title": "Clean code",
            "authors": [{"url": "https://openlibrary.org/authors/OL216228A", "name": "Robert C. Martin"}],
            "publishers": [{"name": "Prentice Hall"}],
            "publish_date": "2009",
            "cover": {
                "small": "https://covers.openlibrary.org/b/id/8234426-S.jpg",
                "medium": "https://covers.openlibrary.org/b/id/8234426-M.jpg",
                "large": "https://covers.openlibrary.org/b/id/8234426-L.jpg",
            },
        }
    }


# ---------- fixtures ----------

@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rede de segurança: se algum teste se esquecer de simular _pedir_json,
    o pedido real rebenta aqui em vez de sair para a internet."""

    def _forbidden(url: str) -> bytes | None:
        raise AssertionError(f"pedido de rede real não simulado: {url}")

    monkeypatch.setattr(isbn_lookup, "_pedir_bytes", _forbidden)


def fake_json(monkeypatch: pytest.MonkeyPatch, resposta: dict[str, Any] | None) -> list[str]:
    """Troca _pedir_json por uma função que devolve sempre `resposta`.

    Devolve a lista de URLs pedidos, para o teste poder confirmar o que
    teria sido enviado à API.
    """
    urls: list[str] = []

    def _fake(url: str) -> dict[str, Any] | None:
        urls.append(url)
        return resposta

    monkeypatch.setattr(isbn_lookup, "_pedir_json", _fake)
    return urls


# ---------- Google Books ----------

def test_google_parses_typical_response(monkeypatch: pytest.MonkeyPatch) -> None:
    urls = fake_json(monkeypatch, google_response())

    resultado = isbn_lookup._fetch_google_books(ISBN)

    assert resultado == {
        "titulo": "Clean Code",  # o subtítulo é ignorado
        "autores_str": "Robert C. Martin",
        "editora": "Pearson Education",
        "genero": "Computers",
        # http:// passa a https:// (a Google devolve muitas vezes http://)
        "capa_url": "https://books.google.com/books/content?id=hjEFCAAAQBAJ&zoom=1",
    }
    assert urls == [f"https://www.googleapis.com/books/v1/volumes?q=isbn%3A{ISBN}"]


def test_google_joins_several_authors_and_categories(monkeypatch: pytest.MonkeyPatch) -> None:
    resposta = google_response()
    info = resposta["items"][0]["volumeInfo"]
    info["authors"] = ["Fabcaro", "Conrad"]
    info["categories"] = ["Comics & Graphic Novels", "Humor"]
    fake_json(monkeypatch, resposta)

    resultado = isbn_lookup._fetch_google_books(ISBN)

    assert resultado is not None
    assert resultado["autores_str"] == "Fabcaro, Conrad"
    assert resultado["genero"] == "Comics & Graphic Novels, Humor"


def test_google_missing_optional_fields_become_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    # Muitos livros não têm autores, editora, categorias ou capa na Google Books.
    resposta = google_response()
    resposta["items"][0]["volumeInfo"] = {"title": "Só título"}
    fake_json(monkeypatch, resposta)

    resultado = isbn_lookup._fetch_google_books(ISBN)

    assert resultado == {"titulo": "Só título", "autores_str": "", "editora": "", "genero": "", "capa_url": ""}


def test_google_no_results_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_json(monkeypatch, {"kind": "books#volumes", "totalItems": 0})

    assert isbn_lookup._fetch_google_books(ISBN) is None


def test_google_total_items_without_items_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    # A Google Books às vezes indica totalItems > 0 mas não envia a lista
    # "items". Antes, dados["items"] rebentava com KeyError e a cascata
    # nunca chegava à Open Library.
    fake_json(monkeypatch, {"kind": "books#volumes", "totalItems": 1})

    assert isbn_lookup._fetch_google_books(ISBN) is None


def test_google_network_failure_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_json(monkeypatch, None)  # _pedir_json devolve None quando a rede falha

    assert isbn_lookup._fetch_google_books(ISBN) is None


# ---------- Open Library ----------

def test_open_library_parses_typical_response(monkeypatch: pytest.MonkeyPatch) -> None:
    urls = fake_json(monkeypatch, open_library_response())

    resultado = isbn_lookup._fetch_open_library(ISBN)

    assert resultado == {
        "titulo": "Clean code",
        "autores_str": "Robert C. Martin",
        "editora": "Prentice Hall",
        "genero": "",  # o código não lê o género da Open Library
        "capa_url": "https://covers.openlibrary.org/b/id/8234426-M.jpg",  # tamanho médio
    }
    assert urls == [f"https://openlibrary.org/api/books?bibkeys=ISBN%3A{ISBN}&format=json&jscmd=data"]


def test_open_library_joins_several_authors_and_publishers(monkeypatch: pytest.MonkeyPatch) -> None:
    resposta = open_library_response()
    livro = resposta[f"ISBN:{ISBN}"]
    livro["authors"] = [{"name": "Fabcaro"}, {"name": "Conrad"}]
    livro["publishers"] = [{"name": "Gradiva"}, {"name": "Asa"}]
    fake_json(monkeypatch, resposta)

    resultado = isbn_lookup._fetch_open_library(ISBN)

    assert resultado is not None
    assert resultado["autores_str"] == "Fabcaro, Conrad"
    assert resultado["editora"] == "Gradiva, Asa"


def test_open_library_missing_optional_fields_become_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_json(monkeypatch, {f"ISBN:{ISBN}": {"title": "Só título"}})

    resultado = isbn_lookup._fetch_open_library(ISBN)

    assert resultado == {"titulo": "Só título", "autores_str": "", "editora": "", "genero": "", "capa_url": ""}


def test_open_library_unknown_isbn_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    # Para um ISBN que não conhece, a Open Library responde com um objeto vazio.
    fake_json(monkeypatch, {})

    assert isbn_lookup._fetch_open_library(ISBN) is None


def test_open_library_network_failure_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_json(monkeypatch, None)

    assert isbn_lookup._fetch_open_library(ISBN) is None


# ---------- lookup_isbn: a cascata Google -> Open Library ----------

def test_lookup_uses_google_and_skips_open_library(monkeypatch: pytest.MonkeyPatch) -> None:
    urls = fake_json(monkeypatch, google_response())

    resultado = isbn_lookup.lookup_isbn(ISBN)

    assert resultado is not None
    assert resultado["editora"] == "Pearson Education"
    assert len(urls) == 1 and "googleapis" in urls[0]  # a Open Library nem é chamada


def test_lookup_falls_back_to_open_library(monkeypatch: pytest.MonkeyPatch) -> None:
    # Resposta diferente consoante o URL: a Google não encontra, a Open Library sim.
    def _fake(url: str) -> dict[str, Any] | None:
        if "googleapis" in url:
            return {"kind": "books#volumes", "totalItems": 0}
        return open_library_response()

    monkeypatch.setattr(isbn_lookup, "_pedir_json", _fake)

    resultado = isbn_lookup.lookup_isbn(ISBN)

    assert resultado is not None
    assert resultado["editora"] == "Prentice Hall"


def test_lookup_falls_back_when_google_omits_items(monkeypatch: pytest.MonkeyPatch) -> None:
    # O caso do KeyError, visto de fora: tem de chegar à Open Library.
    def _fake(url: str) -> dict[str, Any] | None:
        if "googleapis" in url:
            return {"kind": "books#volumes", "totalItems": 1}
        return open_library_response()

    monkeypatch.setattr(isbn_lookup, "_pedir_json", _fake)

    resultado = isbn_lookup.lookup_isbn(ISBN)

    assert resultado is not None
    assert resultado["titulo"] == "Clean code"


def test_lookup_both_fail_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_json(monkeypatch, None)

    assert isbn_lookup.lookup_isbn(ISBN) is None


def test_lookup_sends_normalized_isbn(monkeypatch: pytest.MonkeyPatch) -> None:
    urls = fake_json(monkeypatch, None)

    _ = isbn_lookup.lookup_isbn("978-0-13-235088-4")

    assert all(ISBN in url for url in urls)  # sem hífenes nos dois pedidos
    assert len(urls) == 2


# ---------- _pedir_json: resposta que não é JSON ----------

def test_pedir_json_invalid_json_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ex.: uma página de erro em HTML devolvida com código 200.
    monkeypatch.setattr(isbn_lookup, "_pedir_bytes", lambda url: b"<html>erro</html>")

    assert isbn_lookup._pedir_json("https://exemplo.invalid") is None


def test_pedir_json_parses_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(isbn_lookup, "_pedir_bytes", lambda url: b'{"totalItems": 0}')

    assert isbn_lookup._pedir_json("https://exemplo.invalid") == {"totalItems": 0}
