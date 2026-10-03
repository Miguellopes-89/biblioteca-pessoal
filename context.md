# context.md — Biblioteca Pessoal

> Este ficheiro é o "estado da sessão" do projeto. Cola o conteúdo no início de uma nova conversa com o Claude para retomar exatamente onde ficámos, sem reexplicar nada.

## Sobre o projeto

Aplicação desktop em Python para catalogar livros pessoais (título, autor(es), editora, coleção, género, ISBN, estado de leitura), com inserção manual e/ou por leitura de ISBN via APIs gratuitas (Google Books + Open Library, em cascata, com validação de dígito de controlo antes de pesquisar), base de dados SQLite local, GUI desktop em PySide6, funcionamento offline. **Publicado no GitHub** como portefólio: https://github.com/Miguellopes-89/biblioteca-pessoal (público, com README, LICENSE MIT e requirements.txt).

**Fase web em curso**: versão Flask (`web/`) que reutiliza `database.py` e `isbn_lookup.py` sem alterações, correndo a par da app desktop (não a substitui), sobre a mesma base de dados SQLite.

Claude atua como tutor sénior: explica o "porquê" de cada decisão, avança passo a passo, nunca assume conhecimento prévio, nunca assume factos sobre o ambiente sem confirmar.

## Ambiente

- **SO:** Windows
- **Python:** 3.14.6
- **Git:** 2.55.0
- **GitHub CLI (`gh`):** 2.96.0, autenticado como `Miguellopes-89`
- **Editor:** Zed
- **Docker:** instalado, ainda não usado (entra no fim da fase web, para containerizar)
- **Caminho do projeto:** `C:\Users\User\Projetos\biblioteca-pessoal`
- **Ambiente virtual:** ativar sempre: `.\venv\Scripts\Activate.ps1`
- **Dependências no venv:** `PySide6` 6.11.2 (app desktop) + `Flask` 3.1.3 e as suas dependências (`blinker`, `click`, `itsdangerous`, `jinja2`, `markupsafe`, `werkzeug`) para a fase web. `requirements.txt` (só PySide6) e `requirements-web.txt` (só Flask) ficam separados deliberadamente — quem só quiser a app desktop não precisa de instalar o Flask.
- **`basedpyright`:** instalado no venv (`pip install basedpyright`) para poder ser corrido a partir do terminal, além da integração no Zed. Estado atual: **0 erros, 121 avisos** em todo o projeto (avisos deixados deliberadamente por resolver — `reportUnusedCallResult`, `reportAny`, `reportUnannotatedClassAttribute`, etc.).
- **Testes e CI (2026-10-03):** `pytest` 9.1.1 em `requirements-dev.txt` (com `basedpyright`), configuração em `pytest.ini` (`pythonpath = .`, `testpaths = tests`). Correr com `pytest` a partir da raiz, venv ativo. **39 testes, todos a passar**. CI em `.github/workflows/ci.yml` (GitHub Actions, `ubuntu-latest`, Python 3.14, `actions/checkout@v7`, `actions/setup-python@v6`): corre `pytest` e `basedpyright`; o basedpyright só reprova com erros (os 121 avisos não reprovam).
- **Acesso de Claude ao PC:** desde 2026-09-19, o filesystem (`mcp__Filesystem__*`, restrito a `C:\Users\User\Projetos`) está ativo — Claude lê e edita ficheiros diretamente. **Não há acesso a shell/PowerShell** — comandos (incluindo `git`, `pip install`, correr `basedpyright`, correr `python web/app.py`) continuam a ser executados por Miguel, que cola o output de volta.
- **Cuidado ao colar código no Zed:** continua a ser a causa mais comum de bugs nesta sessão (já aconteceu 4 vezes ao todo, contando sessões anteriores) — blocos com `if`/`try` a ficarem com indentação errada ao colar, umas vezes com erro de sintaxe óbvio, outras vezes como código morto sem erro nenhum. Confirmar sempre visualmente a indentação depois de colar.

## Estado atual do repositório Git

- Branch única: `main`, remoto `origin` → `https://github.com/Miguellopes-89/biblioteca-pessoal.git` (público)
- HEAD confirmado em 2026-10-03: `2c594cf` (versão web com CRUD), em sincronia com `origin/main`. Os commits do basedpyright e do CRUD web já estão feitos.
- **Sugeridos no fim de 2026-10-03, ainda por confirmar como feitos** (4 commits, por ordem; o trabalho de pesquisa/lookup web estava por commitar desde sessões anteriores):
  1. `git add web/app.py web/templates` — `Adiciona pesquisa e lookup de ISBN na versao web`
  2. `git add database.py tests pytest.ini requirements-dev.txt .gitignore` — `Adiciona testes pytest, corrige caminho da BD e ordenacao insensivel a acentos`
  3. `git add .github` — `Adiciona CI com GitHub Actions (pytest + basedpyright)`
  4. `git add context.md` — `Atualiza context.md apos testes e CI`
- Depois do push, acompanhar a primeira execução do CI com `gh run watch`; se falhar, `gh run view --log-failed` e colar o output.
- Confirmar com `git log --oneline -8` e `git status` na próxima sessão antes de continuar
- `.gitignore` cobre: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`, `.pytest_cache/`. `web/__pycache__/` confirmado como ignorado (não aparece no `git status`).

## Ficheiros existentes

### App desktop (inalterados nesta sessão, só corrigidos os erros do basedpyright)
- `.gitignore`, `README.md`, `LICENSE`, `requirements.txt`, `main.py`, `pyrightconfig.json`
- `database.py` — módulo SQLite. Expõe: `normalize_text`, `connect`, `create_tables`, `get_or_create_author`, `add_book`, `list_books`, `search_books`, `update_book`, `delete_book`, e **novo nesta sessão**: `get_book(livro_id) -> dict | None` (busca um único livro pelo id, mesmo formato de `list_books()`; usado pela rota de editar da versão web). **Alterado em 2026-10-03:** `DB_NAME` é agora um caminho absoluto (`Path(__file__).resolve().parent / "biblioteca.db"`); `connect()` regista a função SQL `normalizar` (= `normalize_text`) em todas as ligações; `list_books()` e `search_books()` ordenam por `normalizar(titulo), titulo` (antes: ordem por bytes — maiúsculas antes de minúsculas, títulos acentuados no fim; bug descoberto por um teste).
- `isbn_lookup.py` — corrigido: `_pedir_json` devolve `dict[str, Any] | None` (JSON de API externa é genuinamente arbitrário); `_fetch_google_books`, `_fetch_open_library`, `lookup_isbn` devolvem `dict[str, str] | None` (chaves e valores sempre `str`, conhecidos).
- `gui.py` — dois bugs de indentação corrigidos (`QMessageBox.warning` em `pesquisar_isbn`; bloco de `linha_selecionada` que tinha ficado como código morto dentro do `if`). `PesquisaISBNThread.run()` ajustado: constrói um dict novo (`{**resultado, "capa_bytes": ...}`) tipado `dict[str, str | bytes | None]`, em vez de alargar o tipo de retorno de `lookup_isbn()`.
- `biblioteca.db` — não versionado, com 9 livros (confirmado no browser em 2026-10-03).

### Versão web (nova nesta sessão)
```
web/
├── app.py              ← servidor Flask; sys.path aponta para a raiz para importar database.py/isbn_lookup.py
└── templates/
    ├── index.html        ← lista de livros + link "Adicionar" + Editar/Remover por linha
    ├── adicionar.html     ← formulário de adicionar (GET mostra vazio, POST processa)
    └── editar.html        ← formulário de editar, pré-preenchido via get_book()
```
- **Rotas implementadas e testadas no browser:**
  - `GET /` — lista todos os livros (`list_books()`)
  - `GET/POST /adicionar` — uma só view function para mostrar e processar o formulário (padrão idiomático do Flask; alternativa com rotas separadas foi considerada e descartada)
  - `GET/POST /livros/<int:livro_id>/editar` — `<int:livro_id>` captura o id da URL; usa `get_book()` para pré-preencher, `update_book()` para gravar
  - `POST /livros/<int:livro_id>/remover` — **só POST, nunca GET** (ação destrutiva não deve ser disparável por um link simples); confirmação via `confirm()` de JavaScript no template, equivalente ao `QMessageBox.question` da GUI
- **Pesquisa (passo 3):** `GET /` aceita `?q=...`; usa `search_books(termo)` quando há termo, senão `list_books()`. Testado e confirmado: título, autor, termo sem acentos a encontrar título acentuado, zero resultados sem erro, "Limpar" a repor a lista
- **Lookup de ISBN (passo 4):** `GET /pesquisar-isbn?isbn=...` — endpoint JSON chamado por `fetch()` a partir do botão "Procurar" em `adicionar.html`; reutiliza `validar_isbn()`/`lookup_isbn()` sem alterações, devolve 400 (ISBN vazio/inválido) ou 404 (não encontrado), ou o dict de metadados em 200. Não usa `baixar_capa()` — o browser carrega `capa_url` diretamente num `<img>`. Código funciona (casos de erro confirmados), mas o caminho de sucesso nunca foi validado visualmente — 3 ISBNs válidos testados, sempre bloqueados pelo 429 da quota partilhada da Google Books. **Decisão de Miguel: arrumar este assunto por agora**, não investir mais tempo a perseguir a API. Se um dia se quiser retomar, a via mais fiável é obter uma chave de API gratuita da Google Books
- **Resolvido em 2026-10-03:** o aviso antigo "correr sempre a partir da raiz" deixou de ser necessário — `DB_NAME` é agora um caminho absoluto, a mesma base de dados é usada de qualquer pasta. `python web/app.py` continua a ser o comando.
- Modo debug do Flask (`app.run(debug=True)`) está ligado — recarrega sozinho ao gravar ficheiros `.py`; mudanças em `database.py` (módulo importado) também são apanhadas pelo reloader, confirmado na prática.

## Modelo de dados (schema SQLite)

Inalterado desde a última sessão — ver histórico. Sem novidades no schema nesta sessão (só uma função nova de leitura, `get_book`, sem alterar tabelas).

## Incidentes resolvidos (histórico, não repetir)

1. **Google Books API sem chave devolve HTTP 429** — quota global partilhada. Fallback para Open Library é essencial.
2. **`requests`/`urllib3` com ligações resetadas** pela Open Library nesta máquina — resolvido com `urllib.request` + retry.
3. **Bug do botão "Procurar" preso indefinidamente** — erro de indentação ao colar código (`emit()` só corria dentro do `if`).
4. **basedpyright: suspeita inicial errada.** No início desta sessão, suspeitou-se que os erros estariam no padrão `self.tabela_livros.item(...).text()` sem verificar `None`. Estava errado — esse padrão nunca gerou erro nenhum. Os erros reais eram: `dict` sem argumentos de tipo em `isbn_lookup.py` (4×) e um erro de indentação colada em `gui.py`. Lição: **correr o basedpyright a partir do terminal e ler a lista completa (ficheiro:linha:mensagem) antes de assumir onde está o problema** — o contador agregado na barra de estado do Zed (visível ao lado do separador de um ficheiro) é do projeto inteiro, não desse ficheiro.
5. **Quarta ocorrência de falha simultânea das duas APIs de ISBN**, confirmada isoladamente com `Invoke-WebRequest` por API: Google Books com 429 (quota diária esgotada), Open Library com 503. Sem indicação de bug de código, mas já a quarta vez — começa a ser um padrão a vigiar, não só coincidência. Confirmação visual da capa continua por fazer.

## Notas técnicas / decisões tomadas

### App desktop (decisões antigas, continuam válidas)
Cascata de APIs, `urllib.request`, retry simples, `QThread` para a rede, validação de ISBN antes do lookup, preenchimento seletivo pós-lookup, PySide6, type hints modernos em `database.py`, capa como pré-visualização não persistida.

### basedpyright (nesta sessão)
- `dict[str, Any]` só onde os dados são genuinamente arbitrários (JSON de API externa, em `_pedir_json`); `dict[str, str]` onde a forma é conhecida (as funções `_fetch_*` e `lookup_isbn`).
- Conflito de tipos entre `dict[str, str]` (retorno de `lookup_isbn`) e a necessidade de juntar `capa_bytes` (tipo `bytes`) resolvido construindo um dict novo em `gui.py`, não alargando a assinatura pública da função em `isbn_lookup.py` — mantém a função geral (útil também fora da GUI) com o tipo mais preciso possível.

### Testes e CI — decisões tomadas (2026-10-03)
- Cada função de `database.py` abre e fecha a sua própria ligação, por isso uma base `:memory:` não serve para testes (desaparece quando a ligação fecha). Solução: fixture `isolated_db` em `tests/conftest.py`, `autouse=True`, que dá a cada teste um ficheiro temporário (`tmp_path`) e troca `database.DB_NAME` com `monkeypatch` — sem mexer nas assinaturas das funções, e com garantia de que nenhum teste toca no `biblioteca.db` real.
- Ficheiros: `tests/test_isbn.py` (`validar_isbn`, 13 casos), `tests/test_normalize.py` (`normalize_text`, 7 casos), `tests/test_database.py` (19 testes: CRUD, pesquisa, ordenação, vários autores, vários livros sem ISBN, autor mantido ao apagar livro).
- Fluxo "vermelho → verde" usado de propósito: o teste de ordenação foi escrito primeiro, falhou como previsto, e só depois se corrigiu `database.py`.
- CI: o ambiente criado no runner chama-se `venv` para coincidir com `pyrightconfig.json` (`venvPath`/`venv`); o PySide6 é instalado porque o basedpyright verifica `gui.py` e precisa dos pacotes para resolver tipos. Basedpyright só com erros a reprovar, por decisão de Miguel; exigir zero avisos fica como melhoria posterior.

### Fase web — decisões tomadas
- **Framework: Flask**, não FastAPI nem Django. Django descartado (o ORM substituiria o `database.py` escrito à mão). FastAPI adiado, não descartado — migração futura fica barata precisamente porque `database.py`/`isbn_lookup.py` não sabem nada sobre qual framework os chama; só a camada de rotas mudaria.
- App desktop **não é substituída** — as duas interfaces coexistem sobre a mesma base de dados.
- Estrutura: pasta `web/` com `app.py` + `templates/`, ficheiros de lógica de negócio na raiz, reutilizados por importação direta (com ajuste de `sys.path`).
- Dependências da fase web isoladas em `requirements-web.txt`, sem tocar no `requirements.txt` original.
- Padrão de formulário: uma view function por recurso, a tratar `GET` (mostrar) e `POST` (processar) — decisão A sobre B (rotas separadas), por ser o padrão idiomático do Flask para casos simples como este.
- Ações destrutivas (remover) só aceitam `POST`, nunca `GET` — nunca disparáveis por um link simples ou por um crawler.
- `get_book()` foi acrescentado a `database.py` (não a `web/app.py`) porque é lógica de acesso a dados, reutilizável por qualquer interface futura — mesma filosofia das restantes funções desse módulo.

## Próximo passo

1. ~~Listagem (`GET /`)~~ — **feito e testado**.
2. ~~CRUD completo (adicionar, editar, remover)~~ — **feito e testado ponto a ponto**.
3. ~~Pesquisa (reutilizar `search_books()`)~~ — **feito e testado**.
4. ~~Lookup de ISBN na versão web~~ — **código feito e casos de erro testados; caminho de sucesso por validar, arrumado por decisão de Miguel (ver secção da versão web acima)**.
5. ~~Testes automáticos + CI~~ — **testes feitos (39 a passar); CI escrito, por validar após o primeiro push** (ver secção Git).
6. **Docker** — último passo da fase web: containerizar a app Flask já funcional. Antes de expor fora de localhost: tirar `debug=True` (o debugger do Werkzeug permite execução remota de código) e usar `gunicorn`; considerar proteção CSRF no formulário de remover (aceitável em localhost, mencionar no README).

Opções discutidas para depois: (B) notebook de EDA com pandas sobre a própria biblioteca e apresentar a validação de ISBN/deteção de duplicados como data quality no README (alinhado com o alvo de carreira de Miguel); selo "passing" do CI no README; testes das rotas Flask com o test client; testar o lookup de ISBN com respostas de API simuladas (para validar o caminho de sucesso sem depender da quota da Google Books).

Backlog secundário, sem urgência:
- Confirmar visualmente que uma capa aparece (bloqueado pela mesma falha das APIs de ISBN)
- Se um dia se quiser retomar o lookup de ISBN: obter uma chave de API gratuita da Google Books, para sair da quota partilhada

## Regras de trabalho (lembrete permanente)

- **Acesso de Claude ao PC:** filesystem ativo (`mcp__Filesystem__*`), sem shell/PowerShell — comandos continuam a ser corridos por Miguel.
- Miguel não é engenheiro informático — explicações claras, sem assumir jargão não explicado; termos técnicos definidos numa frase na primeira menção.
- Avançar em passos pequenos, um conceito de cada vez, com explicação, código comentado, forma de testar.
- Comunicação em Português Europeu (PT-PT). Código e nomes de variáveis/funções em inglês. Exceção deliberada: README e descrição do GitHub em inglês.
- Atualizar este ficheiro sempre que se fechar um bloco de trabalho coerente — nesta sessão, Claude já o faz diretamente via filesystem, sem depender de copy-paste manual.
- No fim de cada sessão, sugerir título em `kebab-case`.
- Sempre que uma chamada de rede falhar de forma inesperada, testar primeiro fora do Python (`Invoke-WebRequest`, ou isolar com `python -c "..."` sem GUI) antes de assumir bug de código.
- Depois de colar blocos de código com `if`/`try`/`except`, confirmar visualmente a indentação antes de correr.
- Ao investigar avisos/erros de ferramentas de lint, **correr a ferramenta a partir do terminal e ler a lista completa** antes de formular suspeitas — não adivinhar a partir de contadores agregados na UI do editor.

## Título desta sessão

`pytest-ci-db-path-fix-case-insensitive-sort`
