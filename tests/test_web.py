"""Testes das rotas Flask (web/app.py)."""

import pytest

from database import list_books

# web/ não tem __init__.py, mas o Python trata-a como "pacote de espaços de
# nomes" (namespace package), por isso este import funciona: o pytest.ini
# tem "pythonpath = ." e a raiz do projeto fica no caminho de pesquisa.
from web.app import app as flask_app


@pytest.fixture
def client():
    """Um "browser falso" ligado à app, sem arrancar servidor.

    - TESTING=True: se uma rota rebentar, o erro sobe até ao pytest com o
      traceback completo, em vez de ser escondido numa página "500".
    - A isolated_db (autouse, no conftest.py) corre antes desta fixture, por
      isso a app já encontra a base de dados temporária e vazia.
    """
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as test_client:
        yield test_client


def _form(**overrides):
    """Dados de formulário válidos. Cada teste muda só o que lhe interessa,
    assim percebe-se logo o que está a ser testado."""
    data = {
        "titulo": "Dom Casmurro",
        "autores_str": "Machado de Assis",
        "editora": "Editora Teste",
        "colecao": "",
        "genero": "Romance",
        "isbn": "9780132350884",
        "estado_leitura": "não lido",
    }
    data.update(overrides)
    return data


def _add(client, **overrides):
    """Submete o formulário de adicionar (sem seguir o redirect)."""
    return client.post("/adicionar", data=_form(**overrides))


def test_index_empty_library(client):
    """GET / com a base vazia: a página abre sem erros."""
    response = client.get("/")
    assert response.status_code == 200


def test_add_book_redirects_and_appears_in_list(client):
    """POST /adicionar válido: redireciona para a lista e o livro aparece lá."""
    response = _add(client)

    assert response.status_code == 302  # redirect, não 200
    assert response.headers["Location"] == "/"

    html = client.get("/").get_data(as_text=True)
    assert "Dom Casmurro" in html
    assert "Machado de Assis" in html


def test_add_book_without_title_shows_error(client):
    """Título vazio: volta ao formulário com erro e não grava nada."""
    response = _add(client, titulo="")

    assert response.status_code == 200
    assert "O título não pode ficar vazio." in response.get_data(as_text=True)
    assert list_books() == []


def test_add_book_duplicate_isbn_shows_error(client):
    """Mesmo ISBN duas vezes: a segunda é recusada com mensagem."""
    _add(client)
    response = _add(client, titulo="Outro Titulo")  # mesmo ISBN do _form()

    assert response.status_code == 200
    assert "Já existe um livro com este ISBN" in response.get_data(as_text=True)
    assert len(list_books()) == 1


def test_search_filters_and_ignores_accents(client):
    """?q= devolve só os livros que coincidem, sem distinguir acentos."""
    # isbn="" vira None na app; o UNIQUE do SQLite aceita vários None.
    _add(client, titulo="Memórias Póstumas", isbn="")
    _add(client, titulo="Dom Casmurro", isbn="")

    html = client.get("/?q=memorias").get_data(as_text=True)  # sem acento

    assert "Memórias Póstumas" in html
    assert "Dom Casmurro" not in html


def test_edit_book_prefills_and_updates(client):
    """GET mostra o formulário preenchido; POST grava as alterações."""
    _add(client)
    livro_id = list_books()[0]["id"]  # não assumimos que o id é 1

    page = client.get(f"/livros/{livro_id}/editar")
    assert page.status_code == 200
    assert "Dom Casmurro" in page.get_data(as_text=True)

    response = client.post(
        f"/livros/{livro_id}/editar",
        data=_form(titulo="Novo Titulo", estado_leitura="lido"),
    )

    assert response.status_code == 302
    livro = list_books()[0]
    assert livro["titulo"] == "Novo Titulo"
    assert livro["estado_leitura"] == "lido"


def test_remove_book(client):
    """POST /remover apaga o livro e redireciona para a lista."""
    _add(client)
    livro_id = list_books()[0]["id"]

    response = client.post(f"/livros/{livro_id}/remover")

    assert response.status_code == 302
    assert list_books() == []


# --- Casos de erro ---------------------------------------------------------


def test_edit_missing_book_returns_404(client):
    """Id inexistente: 404 tanto a abrir o formulário como a submeter."""
    assert client.get("/livros/999/editar").status_code == 404
    assert client.post("/livros/999/editar", data=_form()).status_code == 404


def test_edit_without_title_shows_error(client):
    """Título vazio ao editar: mostra erro e o livro fica como estava."""
    _add(client)
    livro_id = list_books()[0]["id"]

    response = client.post(f"/livros/{livro_id}/editar", data=_form(titulo=""))

    assert response.status_code == 200
    assert "O título não pode ficar vazio." in response.get_data(as_text=True)
    assert list_books()[0]["titulo"] == "Dom Casmurro"


def test_edit_duplicate_isbn_shows_error(client):
    """Editar um livro para o ISBN de outro: recusado, ISBN original mantém-se."""
    _add(client, titulo="Livro A", isbn="9780132350884")
    _add(client, titulo="Livro B", isbn="9780306406157")
    livro_b = next(l for l in list_books() if l["titulo"] == "Livro B")

    response = client.post(
        f"/livros/{livro_b['id']}/editar",
        data=_form(titulo="Livro B", isbn="9780132350884"),  # ISBN do Livro A
    )

    assert response.status_code == 200
    assert "Não foi possível atualizar" in response.get_data(as_text=True)
    assert next(l for l in list_books() if l["titulo"] == "Livro B")["isbn"] == "9780306406157"


def test_remove_rejects_get(client):
    """GET na rota de remover: 405 (só aceita POST) e o livro não é apagado."""
    _add(client)
    livro_id = list_books()[0]["id"]

    response = client.get(f"/livros/{livro_id}/remover")

    assert response.status_code == 405
    assert len(list_books()) == 1


def test_remove_missing_book_still_redirects(client):
    """Remover um id inexistente não rebenta: redireciona para a lista.

    Documenta o comportamento atual (a rota ignora o False de delete_book).
    """
    response = client.post("/livros/999/remover")

    assert response.status_code == 302


def test_edit_can_clear_optional_field(client):
    """Esvaziar a editora ao editar deixa-a vazia (NULL na base de dados).

    Foi um xfail até 2026-10-21: a rota convertia o campo vazio em None, que o
    update_book lê como "manter o valor atual". Agora a rota envia "" e o
    update_book grava NULL.
    """
    _add(client, editora="Editora Teste")
    livro_id = list_books()[0]["id"]

    client.post(f"/livros/{livro_id}/editar", data=_form(editora=""))

    assert list_books()[0]["editora"] is None


# --- /pesquisar-isbn (lookup simulado, sem rede) ---------------------------

VALID_ISBN = "9780132350884"  # dígito de controlo válido


@pytest.fixture(autouse=True)
def block_isbn_network(monkeypatch):
    """Rede de segurança: nenhum teste deste ficheiro chama a rede por engano.

    Troca web.app.lookup_isbn por uma função que rebenta. É em "web.app" (onde
    a função é USADA) e não em "isbn_lookup" (onde nasceu) que a troca tem de
    ser feita: o "from isbn_lookup import lookup_isbn" do app.py criou uma
    cópia do nome. Os testes que precisam de um resultado voltam a trocar a
    função por uma versão falsa; o monkeypatch repara tudo no fim de cada teste.
    """

    def _forbidden(isbn):
        raise AssertionError("lookup_isbn chamado sem ser simulado no teste")

    monkeypatch.setattr("web.app.lookup_isbn", _forbidden)


def test_isbn_search_without_isbn_returns_400(client):
    """Sem ?isbn=: 400 com mensagem (e o lookup nem chega a ser chamado)."""
    response = client.get("/pesquisar-isbn")

    assert response.status_code == 400
    assert "erro" in response.get_json()


def test_isbn_search_invalid_checksum_returns_400(client):
    """ISBN com dígito de controlo errado: 400, sem gastar uma chamada de rede."""
    response = client.get("/pesquisar-isbn?isbn=9780132350885")  # último dígito trocado

    assert response.status_code == 400
    assert "dígito de controlo" in response.get_json()["erro"]


def test_isbn_search_not_found_returns_404(client, monkeypatch):
    """ISBN válido que nenhuma API conhece (lookup devolve None): 404."""
    monkeypatch.setattr("web.app.lookup_isbn", lambda isbn: None)

    response = client.get(f"/pesquisar-isbn?isbn={VALID_ISBN}")

    assert response.status_code == 404
    assert "erro" in response.get_json()


def test_isbn_search_success_returns_metadata(client, monkeypatch):
    """Caminho de sucesso (nunca validado no browser por causa do 429):
    a rota devolve em JSON exatamente o que o lookup devolveu."""
    fake_result = {
        "titulo": "Clean Code",
        "autores_str": "Robert C. Martin",
        "editora": "Prentice Hall",
        "genero": "Computers",
        "capa_url": "https://example.com/capa.jpg",
    }
    calls = []

    def fake_lookup(isbn):
        calls.append(isbn)  # guarda com que ISBN a rota chamou o lookup
        return fake_result

    monkeypatch.setattr("web.app.lookup_isbn", fake_lookup)

    response = client.get(f"/pesquisar-isbn?isbn={VALID_ISBN}")

    assert response.status_code == 200
    assert response.get_json() == fake_result
    assert calls == [VALID_ISBN]


# --- ISBN inválido: assinalado, não recusado --------------------------------

def test_add_invalid_isbn_is_saved_and_flagged_in_list(client):
    """ISBN com dígito de controlo errado: gravado, e a lista mostra o aviso."""
    response = _add(client, isbn="9780132350885")

    assert response.status_code == 302  # redirect para a lista, como num sucesso
    assert list_books()[0]["isbn"] == "9780132350885"
    pagina = client.get("/").get_data(as_text=True)
    assert "ISBN inválido" in pagina
    assert 'class="isbn-invalido"' in pagina  # texto a vermelho


def test_edit_invalid_isbn_is_saved(client):
    """Editar para um ISBN inválido: gravado na mesma."""
    _add(client, isbn="9780132350884")
    livro_id = list_books()[0]["id"]

    response = client.post(f"/livros/{livro_id}/editar", data=_form(isbn="123456789"))

    assert response.status_code == 302
    assert list_books()[0]["isbn"] == "123456789"


def test_valid_isbn_is_not_flagged_in_list(client):
    """Um ISBN válido não leva aviso na lista."""
    _add(client, isbn="978-0-13-235088-4")

    pagina = client.get("/").get_data(as_text=True)
    assert "9780132350884" in pagina  # gravado na forma canónica
    assert "ISBN inválido" not in pagina
    assert 'class="isbn-invalido"' not in pagina
