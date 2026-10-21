"""Testes da lógica de repetição (retry) de isbn_lookup._pedir_bytes.

Nenhum teste toca na rede: cada teste troca urllib.request.urlopen por uma
função falsa que devolve uma sequência pré-definida de resultados (bytes ou
uma exceção), e troca time.sleep por uma função que só conta as pausas.
Assim os testes correm instantaneamente e podemos verificar:
- quantas vezes o pedido foi feito (tentativas);
- quantas pausas houve entre tentativas.
"""

import io
import urllib.error
from collections.abc import Callable
from email.message import Message

import pytest

import isbn_lookup

URL = "https://example.test/livro"

# Tipo da fixture fake_net: recebe os resultados simulados e devolve o registo.
Configurar = Callable[..., dict[str, int]]


def _http_error(code: int) -> urllib.error.HTTPError:
    """Cria um HTTPError como o que o urlopen lança quando o servidor
    responde com um código de erro (ex.: 404, 429, 503)."""
    return urllib.error.HTTPError(URL, code, f"HTTP {code}", Message(), io.BytesIO(b""))


class _FakeResponse:
    """Imita a resposta do urlopen: usada com `with` e tem .read()."""

    def __init__(self, body: bytes) -> None:
        self._body: bytes = body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body


@pytest.fixture
def fake_net(monkeypatch: pytest.MonkeyPatch) -> Configurar:
    """Devolve uma função `configurar(*resultados)` e um registo de chamadas.

    Cada chamada ao urlopen falso consome o próximo resultado da lista:
    se for bytes devolve-o como resposta; se for uma exceção, lança-a.
    """
    registo = {"pedidos": 0, "pausas": 0}
    resultados: list[bytes | BaseException] = []

    # Os argumentos (pedido, timeout=...) são aceites mas ignorados.
    def fake_urlopen(_pedido: object, **_kwargs: object) -> _FakeResponse:
        registo["pedidos"] += 1
        resultado = resultados.pop(0)
        if isinstance(resultado, BaseException):
            raise resultado
        return _FakeResponse(resultado)

    def fake_sleep(_segundos: float) -> None:
        registo["pausas"] += 1

    # isbn_lookup usa os módulos urllib.request e time da standard library,
    # por isso troca-se a função diretamente nesses módulos (só neste teste).
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    monkeypatch.setattr("time.sleep", fake_sleep)

    def configurar(*novos: bytes | BaseException) -> dict[str, int]:
        resultados.extend(novos)
        return registo

    return configurar


def test_success_first_try(fake_net: Configurar) -> None:
    registo = fake_net(b"ok")
    assert isbn_lookup._pedir_bytes(URL) == b"ok"
    assert registo == {"pedidos": 1, "pausas": 0}


@pytest.mark.parametrize("code", [400, 404, 429, 499])
def test_http_4xx_is_not_retried(fake_net: Configurar, code: int) -> None:
    # Um 4xx é uma recusa do servidor: desiste à primeira, sem pausas.
    registo = fake_net(_http_error(code))
    assert isbn_lookup._pedir_bytes(URL) is None
    assert registo == {"pedidos": 1, "pausas": 0}


def test_http_5xx_is_retried_then_succeeds(fake_net: Configurar) -> None:
    registo = fake_net(_http_error(503), b"ok")
    assert isbn_lookup._pedir_bytes(URL) == b"ok"
    assert registo == {"pedidos": 2, "pausas": 1}


def test_http_5xx_gives_up_after_all_attempts(fake_net: Configurar) -> None:
    registo = fake_net(*[_http_error(500) for _ in range(isbn_lookup.TENTATIVAS)])
    assert isbn_lookup._pedir_bytes(URL) is None
    assert registo["pedidos"] == isbn_lookup.TENTATIVAS
    assert registo["pausas"] == isbn_lookup.TENTATIVAS - 1


def test_network_error_is_retried_then_succeeds(fake_net: Configurar) -> None:
    registo = fake_net(urllib.error.URLError("sem rede"), TimeoutError(), b"ok")
    assert isbn_lookup._pedir_bytes(URL) == b"ok"
    assert registo == {"pedidos": 3, "pausas": 2}
