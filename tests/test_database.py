"""Testes das funções de acesso a dados em database.py.

Cada teste corre sobre uma base de dados temporária vazia (ver conftest.py).
"""

import database


def add(titulo: str, autores: str = "", isbn: str | None = None) -> int:
    """Atalho para inserir um livro nos testes e garantir que correu bem."""
    livro_id = database.add_book(
        titulo=titulo, editora=None, colecao=None, genero=None,
        isbn=isbn, autores_str=autores,
    )
    assert livro_id is not None
    return livro_id


def authors_of(livro: dict[str, str | int | None] | None) -> set[str]:
    """Devolve os autores de um livro como conjunto. GROUP_CONCAT não garante
    ordem, por isso os testes comparam conjuntos e não strings."""
    assert livro is not None
    texto = livro["autores"]
    assert isinstance(texto, str)
    return set(texto.split(", "))


# ---------- adicionar / ler ----------

def test_add_and_get_book() -> None:
    livro_id = add("Dictator", autores="Robert Harris", isbn="9789722359931")

    livro = database.get_book(livro_id)

    assert livro is not None
    assert livro["titulo"] == "Dictator"
    assert livro["isbn"] == "9789722359931"
    assert livro["estado_leitura"] == "não lido"  # valor por omissão
    assert authors_of(livro) == {"Robert Harris"}


def test_get_book_missing_returns_none() -> None:
    assert database.get_book(999) is None


def test_add_book_with_several_authors() -> None:
    livro_id = add("Livro a quatro mãos", autores="Fabcaro, Conrad")

    assert authors_of(database.get_book(livro_id)) == {"Fabcaro", "Conrad"}


def test_add_book_duplicate_isbn_returns_none() -> None:
    add("Primeiro", isbn="9780132350884")

    segundo = database.add_book(
        titulo="Segundo", editora=None, colecao=None, genero=None,
        isbn="9780132350884", autores_str="",
    )

    assert segundo is None
    assert len(database.list_books()) == 1


def test_several_books_without_isbn_are_allowed() -> None:
    # UNIQUE em SQLite aceita vários NULL. É por isso que a camada web converte
    # um campo vazio em None (e não em "") antes de chamar add_book().
    add("Sem ISBN 1")
    add("Sem ISBN 2")

    assert len(database.list_books()) == 2


def test_author_lookup_is_case_insensitive() -> None:
    add("Livro A", autores="George Orwell")
    add("Livro B", autores="george orwell")

    conn = database.connect()
    total = conn.execute("SELECT COUNT(*) FROM autores").fetchone()[0]
    conn.close()

    assert total == 1  # o mesmo autor, não dois registos


def test_book_without_authors_has_none_in_authors_column() -> None:
    livro_id = add("Anónimo")

    livro = database.get_book(livro_id)

    assert livro is not None
    assert livro["autores"] is None


# ---------- listar ----------

def test_list_books_sorted_ignoring_case_and_accents() -> None:
    # Ordem esperada por um leitor: álgebra, Banana, Zebra.
    # Com ORDER BY simples, o SQLite compara bytes: maiúsculas vêm antes de
    # minúsculas e 'á' (código alto) vai parar depois de 'Z'.
    add("Zebra")
    add("álgebra")
    add("Banana")

    titulos = [livro["titulo"] for livro in database.list_books()]

    assert titulos == ["álgebra", "Banana", "Zebra"]


# ---------- pesquisar ----------

def test_search_ignores_accents_and_case() -> None:
    add("Análise Económica", autores="Fernando Abecassis")

    assert len(database.search_books("ANALISE")) == 1
    assert len(database.search_books("economica")) == 1


def test_search_by_author_name() -> None:
    add("Imperium", autores="Robert Harris")
    add("Outro livro", autores="Alguém")

    resultados = database.search_books("harris")

    assert [livro["titulo"] for livro in resultados] == ["Imperium"]


def test_search_by_one_author_still_returns_all_authors() -> None:
    # O ponto da subquery em search_books: pesquisar por UM autor não pode
    # esconder os restantes autores do mesmo livro.
    add("A quatro mãos", autores="Fabcaro, Conrad")

    resultados = database.search_books("conrad")

    assert len(resultados) == 1
    assert authors_of(resultados[0]) == {"Fabcaro", "Conrad"}


def test_search_without_match_returns_empty_list() -> None:
    add("Dictator", autores="Robert Harris")

    assert database.search_books("inexistente") == []


def test_search_results_sorted_ignoring_case_and_accents() -> None:
    add("Zebra clássica")
    add("álgebra clássica")

    titulos = [livro["titulo"] for livro in database.search_books("classica")]

    assert titulos == ["álgebra clássica", "Zebra clássica"]


# ---------- atualizar ----------

def test_update_book_partial_keeps_other_fields() -> None:
    livro_id = add("Título original", autores="Autor", isbn="9780132350884")

    assert database.update_book(livro_id, genero="Romance") is True

    livro = database.get_book(livro_id)
    assert livro is not None
    assert livro["genero"] == "Romance"
    assert livro["titulo"] == "Título original"
    assert livro["isbn"] == "9780132350884"
    assert authors_of(livro) == {"Autor"}


def test_update_book_replaces_authors() -> None:
    livro_id = add("Livro", autores="Antigo")

    database.update_book(livro_id, autores_str="Novo, Outro")

    assert authors_of(database.get_book(livro_id)) == {"Novo", "Outro"}


def test_update_book_duplicate_isbn_returns_false() -> None:
    add("Livro 1", isbn="9780132350884")
    livro_2 = add("Livro 2", isbn="9789722359931")

    assert database.update_book(livro_2, isbn="9780132350884") is False


def test_update_book_missing_returns_false() -> None:
    assert database.update_book(999, titulo="Nada") is False


# ---------- remover ----------

def test_delete_book_removes_links_but_keeps_author() -> None:
    livro_id = add("Livro", autores="Autor Persistente")

    assert database.delete_book(livro_id) is True

    assert database.get_book(livro_id) is None
    conn = database.connect()
    autores = conn.execute("SELECT COUNT(*) FROM autores").fetchone()[0]
    ligacoes = conn.execute("SELECT COUNT(*) FROM livro_autor").fetchone()[0]
    conn.close()
    assert autores == 1  # o autor fica (decisão documentada em delete_book)
    assert ligacoes == 0


def test_delete_book_missing_returns_false() -> None:
    assert database.delete_book(999) is False
