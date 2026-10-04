# historico.md — Biblioteca Pessoal

> Arquivo de consulta a pedido: incidentes resolvidos, decisões tomadas e o detalhe das alterações por ficheiro. **Não é carregado em cada sessão** — ler só quando o tema for relevante (chamadas de rede, basedpyright/CI, testes, decisões da fase web, dúvidas do tipo "porque é que fizemos X?"). O estado atual está em `context.md`.

## Incidentes resolvidos (não repetir)

1. **Google Books API sem chave devolve HTTP 429** — quota global partilhada. Fallback para Open Library é essencial.
2. **`requests`/`urllib3` com ligações resetadas** pela Open Library nesta máquina — resolvido com `urllib.request` + retry.
3. **Bug do botão "Procurar" preso indefinidamente** — erro de indentação ao colar código (`emit()` só corria dentro do `if`).
4. **basedpyright: suspeita inicial errada.** Suspeitou-se que os erros estariam no padrão `self.tabela_livros.item(...).text()` sem verificar `None`. Estava errado — esse padrão nunca gerou erro nenhum. Os erros reais eram: `dict` sem argumentos de tipo em `isbn_lookup.py` (4×) e um erro de indentação colada em `gui.py`. Lição: **correr o basedpyright a partir do terminal e ler a lista completa (ficheiro:linha:mensagem) antes de assumir onde está o problema** — o contador agregado na barra de estado do Zed (visível ao lado do separador de um ficheiro) é do projeto inteiro, não desse ficheiro.
5. **Quarta ocorrência de falha simultânea das duas APIs de ISBN**, confirmada isoladamente com `Invoke-WebRequest` por API: Google Books com 429 (quota diária esgotada), Open Library com 503. Sem indicação de bug de código, mas já a quarta vez — começa a ser um padrão a vigiar, não só coincidência. Confirmação visual da capa continua por fazer.
6. **O basedpyright reprova por omissão com avisos.** A primeira execução do CI falhou com `0 errors, 145 warnings` e exit code 1: no basedpyright, `failOnWarnings` vem ligado por omissão (diferente do pyright). Claude tinha afirmado, sem verificar, que avisos não reprovavam. Resolvido com `"failOnWarnings": false` em `pyrightconfig.json`. Lição: o código de saída de uma ferramenta nova confirma-se na prática (`gh run view --log-failed`), não se assume.

## Alterações detalhadas por ficheiro

- `database.py` — `get_book(livro_id) -> dict | None` acrescentado (mesmo formato de `list_books()`; usado pela rota de editar da web). Alterado em 2026-10-03: `DB_NAME` passou a caminho absoluto (`Path(__file__).resolve().parent / "biblioteca.db"`); `connect()` regista a função SQL `normalizar` (= `normalize_text`) em todas as ligações; `list_books()` e `search_books()` ordenam por `normalizar(titulo), titulo` (antes: ordem por bytes — maiúsculas antes de minúsculas, títulos acentuados no fim; bug descoberto por um teste).
- `isbn_lookup.py` — `_pedir_json` devolve `dict[str, Any] | None` (JSON de API externa é genuinamente arbitrário); `_fetch_google_books`, `_fetch_open_library`, `lookup_isbn` devolvem `dict[str, str] | None`.
- `gui.py` — dois bugs de indentação corrigidos (`QMessageBox.warning` em `pesquisar_isbn`; bloco de `linha_selecionada` que tinha ficado como código morto dentro do `if`). `PesquisaISBNThread.run()` constrói um dict novo (`{**resultado, "capa_bytes": ...}`) tipado `dict[str, str | bytes | None]`, em vez de alargar o tipo de retorno de `lookup_isbn()`.
- Lookup de ISBN na web: `GET /pesquisar-isbn?isbn=...` devolve 400 (ISBN vazio/inválido), 404 (não encontrado) ou 200 com o dict. Não usa `baixar_capa()` — o browser carrega `capa_url` num `<img>`. Caminho de sucesso nunca validado visualmente: 3 ISBNs válidos testados, sempre bloqueados pelo 429 da Google Books. **Decisão de Miguel: arrumar este assunto.** Via mais fiável se for retomado: chave de API gratuita da Google Books.
- Resolvido em 2026-10-03: o aviso "correr sempre a partir da raiz" deixou de ser necessário (`DB_NAME` absoluto).
- Modo debug do Flask (`debug=True`): recarrega ao gravar `.py`; mudanças em `database.py` também são apanhadas.

## Decisões tomadas

### App desktop
Cascata de APIs, `urllib.request`, retry simples, `QThread` para a rede, validação de ISBN antes do lookup, preenchimento seletivo pós-lookup, PySide6, type hints modernos em `database.py`, capa como pré-visualização não persistida.

### basedpyright
- `dict[str, Any]` só onde os dados são genuinamente arbitrários (JSON de API externa, em `_pedir_json`); `dict[str, str]` onde a forma é conhecida (`_fetch_*` e `lookup_isbn`).
- Conflito entre `dict[str, str]` (retorno de `lookup_isbn`) e a necessidade de juntar `capa_bytes` (`bytes`) resolvido construindo um dict novo em `gui.py`, não alargando a assinatura pública em `isbn_lookup.py` — mantém a função geral com o tipo mais preciso possível.

### Testes e CI (2026-10-03)
- Cada função de `database.py` abre e fecha a sua própria ligação, por isso `:memory:` não serve (desaparece quando a ligação fecha). Solução: fixture `isolated_db` em `tests/conftest.py`, `autouse=True`, que dá a cada teste um ficheiro temporário (`tmp_path`) e troca `database.DB_NAME` com `monkeypatch` — sem mexer nas assinaturas, e com garantia de que nenhum teste toca no `biblioteca.db` real.
- Ficheiros: `tests/test_isbn.py` (`validar_isbn`, 13 casos), `tests/test_normalize.py` (`normalize_text`, 7 casos), `tests/test_database.py` (19 testes: CRUD, pesquisa, ordenação, vários autores, vários livros sem ISBN, autor mantido ao apagar livro).
- Fluxo "vermelho → verde" usado de propósito: o teste de ordenação foi escrito primeiro, falhou como previsto, e só depois se corrigiu `database.py`.
- CI: o ambiente no runner chama-se `venv` para coincidir com `pyrightconfig.json` (`venvPath`/`venv`); o PySide6 é instalado porque o basedpyright verifica `gui.py` e precisa dos pacotes para resolver tipos. Só erros reprovam, por decisão de Miguel; exigir zero avisos fica como melhoria posterior.

### Fase web
- **Framework: Flask**, não FastAPI nem Django. Django descartado (o ORM substituiria o `database.py` escrito à mão). FastAPI adiado, não descartado — a migração futura é barata porque `database.py`/`isbn_lookup.py` não sabem qual framework os chama; só a camada de rotas mudaria.
- App desktop **não é substituída** — as duas interfaces coexistem sobre a mesma base de dados.
- Estrutura: pasta `web/` com `app.py` + `templates/`, lógica de negócio na raiz, reutilizada por importação direta (com ajuste de `sys.path`).
- Dependências da web isoladas em `requirements-web.txt`, sem tocar no `requirements.txt` original.
- Padrão de formulário: uma view function por recurso, a tratar `GET` (mostrar) e `POST` (processar) — escolhido em vez de rotas separadas, por ser o padrão idiomático do Flask para casos simples.
- Ações destrutivas (remover) só aceitam `POST`, nunca `GET`; confirmação via `confirm()` de JavaScript, equivalente ao `QMessageBox.question` da GUI.
- `get_book()` está em `database.py` (não em `web/app.py`) porque é lógica de acesso a dados, reutilizável por qualquer interface.

## Modelo de dados

Sem alterações de schema desde a última sessão (só `get_book`, uma função de leitura). Descrição das tabelas no README.

## Docker (2026-10-04)

- **Persistência: volume do Docker + variável `BIBLIOTECA_DB`** (opção B). Rejeitada a opção A (montar o `biblioteca.db` real no container): o SQLite protege contra escritas simultâneas com bloqueios do sistema operativo, que não atravessam a fronteira Windows/container; GUI e container a escrever ao mesmo tempo podiam corromper a BD. Custo assumido: o container tem a sua BD, separada da da desktop, o que contraria a ideia de "mesma base de dados" da fase web (válida só em desenvolvimento local). Consequência: `database.py` alterado numa linha (`DB_NAME = os.environ.get("BIBLIOTECA_DB", <caminho anterior>)`), comportamento por omissão igual; 39 testes continuaram a passar.
- **`create_tables()` no `CMD`**: o `gunicorn` não passa pelo bloco `__main__` do `app.py`, por isso, numa BD nova e vazia, a app arrancaria sem tabelas. Resolvido no `Dockerfile` sem tocar no `app.py`.
- **`debug=True`** deixa de estar ativo no container pelo mesmo motivo (fecha o risco de execução remota de código do debugger do Werkzeug).
- **`gunicorn==26.2.0` só na imagem**, não em `requirements-web.txt` (não corre em Windows). Versão fixada a partir do log do primeiro build.
- **`.dockerignore`** exclui `*.db`, `.env`, `venv/`, `.git`, `tests/`, `docs/`; o `Dockerfile` copia só `database.py`, `isbn_lookup.py` e `web/`, para os dados pessoais não ficarem embutidos na imagem.
- Incidente menor: o primeiro `docker run` falhou com "failed to connect to the docker API" porque o Docker Desktop não estava aberto (o CLI instalado não chega: o daemon tem de estar ativo).
- Teste de persistência: livro adicionado no browser, container parado com Ctrl+C e relançado com o mesmo volume; o livro continuou lá.
- CSRF no formulário de remover continua por tratar (aceitável em localhost; documentado no README).
