"""isbn_lookup.py — consulta de metadados de livros a partir do ISBN.

Duas fontes, em cascata: tenta primeiro a Google Books API (dados mais
consistentes), e só se não encontrar nada tenta a Open Library API.

Usa apenas `urllib.request` (standard library) em vez de `requests`.
Decisão tomada depois de testar: a biblioteca `requests`/`urllib3` estava
a ter a ligação recusada nesta máquina (algo no sistema — antivírus ou
firewall — a interferir com o TLS do urllib3), enquanto `urllib.request`
é mais estável. Como bónus, remove uma dependência externa do projeto:
quem clonar o repositório não precisa de instalar mais nada.

Mesmo com `urllib.request`, as ligações a hosts externos continuam a
falhar de forma intermitente nesta máquina (reset de ligação, timeouts
pontuais) — por isso `_pedir_json` repete cada pedido automaticamente
antes de desistir.

Este módulo não depende do PySide6 — pode ser testado isoladamente, sem
abrir a GUI, por exemplo:

    python -c "from isbn_lookup import lookup_isbn; print(lookup_isbn('9780132350884'))"
"""

import json
import time
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT_SEGUNDOS = 10
USER_AGENT = "biblioteca-pessoal/1.0 (projeto pessoal de portefolio)"
TENTATIVAS = 3
PAUSA_ENTRE_TENTATIVAS_SEGUNDOS = 1


def _pedir_json(url: str) -> dict | None:
    """Faz um GET ao url e devolve o corpo interpretado como JSON, ou None
    se todas as tentativas falharem (rede, timeout, HTTP de erro, JSON inválido).

    Repete o pedido até TENTATIVAS vezes: falhas de rede transitórias
    (reset de ligação, timeout pontual) são normais e não devem impedir
    uma pesquisa que, à tentativa seguinte, teria funcionado.

    Centraliza aqui o tratamento de erros para as duas funções de fetch
    não repetirem o mesmo bloco try/except duas vezes.
    """
    pedido = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    corpo = None
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            with urllib.request.urlopen(pedido, timeout=TIMEOUT_SEGUNDOS) as resposta:
                corpo = resposta.read()
            break
        except (urllib.error.URLError, TimeoutError):
            # Cobre falhas de rede, DNS, timeout, e HTTPError (subclasse de URLError)
            if tentativa == TENTATIVAS:
                return None
            time.sleep(PAUSA_ENTRE_TENTATIVAS_SEGUNDOS)

    try:
        return json.loads(corpo)
    except json.JSONDecodeError:
        return None


def _fetch_google_books(isbn: str) -> dict | None:
    """Consulta a Google Books API. Devolve dict normalizado ou None."""
    query = urllib.parse.urlencode({"q": f"isbn:{isbn}"})
    dados = _pedir_json(f"https://www.googleapis.com/books/v1/volumes?{query}")
    if dados is None or dados.get("totalItems", 0) == 0:
        return None

    info = dados["items"][0].get("volumeInfo", {})

    return {
        "titulo": info.get("title", ""),
        "autores_str": ", ".join(info.get("authors", [])),
        "editora": info.get("publisher", ""),
        "genero": ", ".join(info.get("categories", [])),
    }


def _fetch_open_library(isbn: str) -> dict | None:
    """Consulta a Open Library API. Devolve dict normalizado ou None."""
    query = urllib.parse.urlencode({"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"})
    dados = _pedir_json(f"https://openlibrary.org/api/books?{query}")

    chave = f"ISBN:{isbn}"
    if dados is None or chave not in dados:
        return None

    info = dados[chave]
    autores = [autor.get("name", "") for autor in info.get("authors", [])]
    editoras = [editora.get("name", "") for editora in info.get("publishers", [])]

    return {
        "titulo": info.get("title", ""),
        "autores_str": ", ".join(autores),
        "editora": ", ".join(editoras),
        "genero": "",  # Open Library não expõe "subjects" de forma fiável neste endpoint
    }


def lookup_isbn(isbn: str) -> dict | None:
    """Procura os metadados de um livro pelo ISBN.

    Tenta primeiro a Google Books; se não encontrar nada, tenta a Open
    Library como reserva. Devolve None se nenhuma das duas tiver
    resultados (ou se ambas falharem por erro de rede/timeout, mesmo
    depois das repetições).

    O dict devolvido tem sempre as chaves: titulo, autores_str, editora,
    genero — prontas a usar diretamente nos campos do formulário da GUI.
    Nota: nenhuma das duas APIs expõe de forma fiável um campo
    "coleção" (série) — esse campo continua a ser preenchimento manual.
    """
    isbn = isbn.strip().replace("-", "").replace(" ", "")
    if not isbn:
        return None

    resultado = _fetch_google_books(isbn)
    if resultado is not None:
        return resultado

    return _fetch_open_library(isbn)
