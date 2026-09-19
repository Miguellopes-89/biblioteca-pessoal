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


def _pedir_bytes(url: str) -> bytes | None:
    """Faz um GET ao url e devolve o corpo em bruto (bytes), ou None se
    todas as tentativas falharem (rede, timeout, HTTP de erro).

    Repete o pedido até TENTATIVAS vezes, pela mesma razão descrita no
    cabeçalho deste ficheiro: falhas de rede transitórias nesta máquina.
    Usada tanto para respostas JSON (_pedir_json) como para imagens
    de capa (baixar_capa) — evita duplicar a lógica de retry duas vezes.
    """
    pedido = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    for tentativa in range(1, TENTATIVAS + 1):
        try:
            with urllib.request.urlopen(pedido, timeout=TIMEOUT_SEGUNDOS) as resposta:
                return resposta.read()
        except (urllib.error.URLError, TimeoutError):
            if tentativa == TENTATIVAS:
                return None
            time.sleep(PAUSA_ENTRE_TENTATIVAS_SEGUNDOS)

    return None


def _pedir_json(url: str) -> dict | None:
    """Faz um GET ao url e devolve o corpo interpretado como JSON, ou None
    se o pedido falhar ou a resposta não for JSON válido.
    """
    corpo = _pedir_bytes(url)
    if corpo is None:
        return None

    try:
        return json.loads(corpo)
    except json.JSONDecodeError:
        return None


def baixar_capa(url: str) -> bytes | None:
    """Descarrega os bytes de uma imagem de capa a partir do seu URL.

    Devolve None se o url for vazio ou se o download falhar (mesmo depois
    das repetições em _pedir_bytes). Quem chamar esta função deve sempre
    verificar o resultado antes de o usar (nem toda a API tem sempre capa).
    """
    if not url:
        return None
    return _pedir_bytes(url)


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
        # .replace(...) porque a Google Books por vezes devolve http:// em vez de https://
        "capa_url": info.get("imageLinks", {}).get("thumbnail", "").replace("http://", "https://"),
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
        "capa_url": info.get("cover", {}).get("medium", ""),
    }


def validar_isbn(isbn: str) -> bool:
    """Valida o dígito de controlo de um ISBN-10 ou ISBN-13.

    Não confirma que o livro existe (isso é o lookup_isbn) — só confirma
    que o número em si é matematicamente válido, antes de gastarmos uma
    chamada de rede com ele.

    ISBN-13: soma ponderada (pesos alternados 1 e 3) tem de ser múltiplo de 10.
    ISBN-10: soma ponderada (pesos 10 a 1) tem de ser múltiplo de 11;
    o dígito de controlo pode ser 'X', que vale 10.
    """
    isbn = isbn.strip().replace("-", "").replace(" ", "").upper()

    if len(isbn) == 13:
        if not isbn.isdigit():
            return False
        soma = sum((1 if posicao % 2 == 0 else 3) * int(digito) for posicao, digito in enumerate(isbn))
        return soma % 10 == 0

    if len(isbn) == 10:
        soma = 0
        for posicao, digito in enumerate(isbn):
            if digito == "X" and posicao == 9:
                valor = 10
            elif digito.isdigit():
                valor = int(digito)
            else:
                return False
            soma += valor * (10 - posicao)
        return soma % 11 == 0

    return False


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
