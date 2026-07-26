# metadados_isbn.py
#
# Este módulo trata de ir buscar metadados de um livro (título e
# autor) a partir do ISBN, usando a API pública e gratuita da Open
# Library (https://openlibrary.org/dev/docs/api/books). Fica isolado
# num ficheiro próprio por duas razões:
#
#   1. cli.py não precisa de saber nada sobre APIs externas, pedidos
#      HTTP ou o formato da resposta JSON — só chama
#      procurar_por_isbn() e recebe um dicionário simples ou None.
#   2. Se um dia trocarmos de fornecedor (por exemplo, para a API do
#      Google Books), só este ficheiro precisa de mudar.

import requests

URL_BASE = "https://openlibrary.org/api/books"

# Tempo máximo (em segundos) que esperamos pela resposta da API antes
# de desistir. Sem isto, uma ligação à internet lenta ou instável
# podia deixar o programa "pendurado" indefinidamente.
TIMEOUT_SEGUNDOS = 5


def normalizar_isbn(isbn):
    """
    Remove hífens e espaços de um ISBN, para aceitar tanto
    "978-989-23-1234-5" como "9789892312345" da mesma forma.
    """
    return isbn.replace("-", "").replace(" ", "")


def procurar_por_isbn(isbn):
    """
    Consulta a Open Library pelo ISBN indicado.

    Devolve:
      - um dicionário {"titulo": str, "autor": str ou None} se
        encontrar o livro;
      - None se não encontrar o livro, se o ISBN for inválido, ou se
        a pesquisa falhar por qualquer razão (sem ligação à internet,
        timeout, API em baixo, etc.).

    Propositadamente, esta função nunca lança exceções para fora —
    trata todos os problemas de rede internamente e devolve None. É
    o chamador (cli.py) que decide o que mostrar ao utilizador quando
    a pesquisa automática não é possível; este módulo não sabe nada
    sobre menus ou mensagens ao utilizador.
    """
    isbn_limpo = normalizar_isbn(isbn)
    if not isbn_limpo:
        return None

    chave = f"ISBN:{isbn_limpo}"

    try:
        resposta = requests.get(
            URL_BASE,
            params={"bibkeys": chave, "format": "json", "jscmd": "data"},
            timeout=TIMEOUT_SEGUNDOS,
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except (requests.RequestException, ValueError):
        # requests.RequestException cobre timeouts, falhas de ligação
        # e respostas de erro HTTP. ValueError cobre o caso raro de a
        # resposta não ser JSON válido. Em qualquer um destes casos,
        # o resultado prático para o utilizador é o mesmo: seguimos
        # para preenchimento manual.
        return None

    livro = dados.get(chave)
    if not livro:
        # ISBN válido mas não encontrado no catálogo da Open Library.
        return None

    titulo = livro.get("title")
    if not titulo:
        # Sem título, os dados não são úteis o suficiente para
        # considerar que "encontrámos" o livro.
        return None

    lista_autores = livro.get("authors", [])
    autor = ", ".join(a["name"] for a in lista_autores) if lista_autores else None

    return {"titulo": titulo, "autor": autor}
