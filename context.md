# context.md — Biblioteca Pessoal

> Estado da sessão do projeto. Carregado pelo Miguel no menu "Contexto" do Projeto antes de cada sessão (a cópia em disco é a mais recente). Incidentes, decisões antigas e detalhe das alterações: `docs/historico.md` — ler a pedido, só quando o tema for relevante.

## Sobre o projeto

Aplicação desktop em Python para catalogar livros pessoais (título, autor(es), editora, coleção, género, ISBN, estado de leitura), com inserção manual e/ou por ISBN via APIs gratuitas (Google Books + Open Library, em cascata, com validação do dígito de controlo antes de pesquisar), SQLite local, GUI em PySide6, funcionamento offline. **Publicado no GitHub** como portefólio: https://github.com/Miguellopes-89/biblioteca-pessoal (público, README, LICENSE MIT).

**Fase web concluída**: versão Flask (`web/`) que reutiliza `database.py` e `isbn_lookup.py` a par da app desktop (não a substitui). Corre localmente com `python web/app.py` (mesma BD da desktop) ou em container Docker com `gunicorn` (BD própria, num volume).

## Como se trabalha (desde 2026-10-21)

Há **três cópias** do projeto e o **GitHub é a única fonte de verdade** entre elas:

1. **Claude Code (cloud):** clona o repositório, cria uma branch por tarefa, faz commit, push e abre o PR (pela API REST: `gh pr create` não funciona nas sessões cloud). Não integra na `main` sem confirmação do Miguel. Não tem acesso a nenhum dos PCs nem às BD reais.
2. **PC novo** (onde o Miguel usa o Claude Code; PowerShell, sem Zed): serve para testar as branches do Claude (`git fetch` + `git switch <branch>`, pytest, GUI) e voltar à `main` no fim.
3. **PC original** (OneDrive, Zed): onde estão os dados reais (`biblioteca.db`, 9 livros). Ao voltar a ele: `git switch main` + `git pull`.

Regra: **começar cada sessão com `git pull` e acabar com tudo enviado para o GitHub**, em qualquer cópia; só uma cópia altera código de cada vez. A `venv` e a `biblioteca.db` não viajam pelo GitHub (de propósito): cada PC tem as suas, e a BD não se copia entre PCs.

O Claude do Projeto (claude.ai) só vê este ficheiro; o Claude Code recebe o `CLAUDE.md` anexado pelo Miguel (não está versionado no repositório).

## Ambiente

- **PC original:** Windows · Python 3.14.6 · Git 2.55.0 · `gh` 2.96.0 (autenticado como `Miguellopes-89`) · Zed · Docker Desktop 29.7.2 (o daemon tem de estar ativo: abrir o Docker Desktop antes de qualquer `docker`); imagem `biblioteca-web`, volume `biblioteca-data`
  - **Caminho:** `C:\Users\User\OneDrive\Projetos\biblioteca-pessoal` (localização definitiva de todos os projetos do Miguel; o `.git/` fica lá, a `venv` não). **Venv** em `C:\Users\User\venvs\biblioteca-pessoal`, ativar com `C:\Users\User\venvs\biblioteca-pessoal\Scripts\Activate.ps1`. Sem ela ativa o `pytest` não é reconhecido; `python -m pytest` é a forma segura. **Zed:** venv adicionada com "Add Virtual Environment" (âmbito Project); contagem do Zed: 0 erros, 139 avisos
  - **Acesso de Claude:** Filesystem (`mcp__Filesystem__*`, restrito a `C:\Users\User\OneDrive`) nem sempre disponível; **sem shell** — `git`, `pip`, `pytest`, `python web/app.py` corre-os o Miguel e cola o output
- **PC novo:** Windows · Python 3.14.8 (64 bits) · Git 2.56.0 · **sem** `winget`, Zed ou `gh` (não são precisos: só lê do GitHub)
  - **Caminho:** `C:\Users\Utilizador\Desktop\biblioteca-pessoal` (clone). **Venv** em `C:\Users\Utilizador\venvs\biblioteca-pessoal`, usada sem ativar: `$py = "C:\Users\Utilizador\venvs\biblioteca-pessoal\Scripts\python.exe"` e depois `& $py -m pytest`, `& $py gui.py` (o `$py` perde-se ao fechar a janela). BD de testes própria (não são os dados reais)
  - Usar a janela "Windows PowerShell" normal: nem "Administrator" nem "(x86)" (32 bits, incompatível com PySide6)
- **Dependências:** `PySide6` 6.11.2 (`requirements.txt`) e `Flask` 3.1.3 (`requirements-web.txt`) separados deliberadamente; `requirements-dev.txt` com `pytest` 9.1.1 e `basedpyright`
- **basedpyright:** 0 erros, 300 avisos (deixados por resolver de propósito). `pyrightconfig.json` só com `"failOnWarnings": false`: só erros reprovam. Com a venv ativada, `basedpyright` sem flags usa o Python ativo; o CI e o PC novo usam `--pythonpath <python da venv>`
- **Testes e CI:** `pytest` a partir da raiz; **70 testes, todos passam, 0 `xfail`** (`tests/test_database.py` tem 27; `tests/test_web.py` 19; `tests/test_isbn.py` 17; `tests/test_normalize.py` 7). CI em `.github/workflows/ci.yml` (GitHub Actions) corre `pytest` + `basedpyright` em cada push para a `main` e em cada PR; verde no PR #1
- **Sessões cloud do Claude Code:** fazem push de branches novas, mas **não conseguem apagar branches remotas** (403 do proxy); isso faz-se no GitHub (Branches → caixote do lixo) ou com `git push origin --delete <branch>` num PC
- **Colar código no Zed:** causa mais comum de bugs (4 vezes) — confirmar visualmente a indentação de blocos `if`/`try` depois de colar

## Git

- Remoto `origin` → `https://github.com/Miguellopes-89/biblioteca-pessoal.git`. Uma branch por tarefa, integrada na `main` por PR
- **Email dos commits:** `279319592+Miguellopes-89@users.noreply.github.com` (a conta bloqueia pushes com o email privado). Configurar uma vez em cada PC: `git config --global user.name "Miguel Lopes"` e `git config --global user.email "279319592+Miguellopes-89@users.noreply.github.com"`
- Este ficheiro não regista o HEAD de cada commit: confirmar sempre com `git log --oneline -8` e `git status` antes de continuar
- `.gitignore`: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`, `.pytest_cache/`

## Ficheiros

- Raiz: `gui.py` (PySide6), `database.py`, `isbn_lookup.py`, `main.py` (smoke test antigo, não usado), `README.md` (inglês), `LICENSE`, `pytest.ini`, `pyrightconfig.json`, `Dockerfile`, `.dockerignore`, `biblioteca.db` (não versionado; no PC original, 9 livros)
- `database.py` expõe: `InvalidISBNError`, `normalize_text`, `connect`, `create_tables`, `get_or_create_author`, `add_book`, `list_books`, `search_books`, `update_book`, `delete_book`, `get_book`. `DB_NAME` lê a variável de ambiente `BIBLIOTECA_DB` e, se não existir, usa o caminho absoluto de `biblioteca.db` junto ao ficheiro; listagens ordenadas sem acentos nem maiúsculas
- **Campos opcionais vazios** (editora, coleção, género, ISBN): `""` é gravado como `NULL` (função interna `_empty_to_none`). No `update_book`: `None` = manter o valor atual; `""` = limpar; outro texto = gravar. A GUI e a rota web de editar enviam `""` para um campo esvaziado
- **ISBN ao gravar** (desde 2026-10-21): `add_book`/`update_book` gravam-no na forma canónica (`isbn_lookup.normalize_isbn`: sem hífenes nem espaços, `X` maiúsculo) e lançam `InvalidISBNError` se o dígito de controlo for inválido, sem gravar nada; GUI e web mostram "ISBN inválido". `update_book` com `isbn=None` não valida o valor antigo
- Docker: `python:3.14-slim`, `gunicorn==26.2.0` instalado só na imagem (não está em `requirements-web.txt`), utilizador sem privilégios, `BIBLIOTECA_DB=/data/biblioteca.db`; o `create_tables()` corre no `CMD` antes do `gunicorn`. Comandos: `docker build -t biblioteca-web .` e `docker run --rm -p 8000:8000 -v biblioteca-data:/data biblioteca-web` (http://localhost:8000). A BD do container é separada da da desktop; contém 1 "Livro de teste"
- `tests/`: `conftest.py` (fixture `isolated_db`), `test_isbn.py`, `test_normalize.py`, `test_database.py`, `test_web.py` (fixtures `client` e `block_isbn_network`, esta autouse: faz rebentar qualquer chamada real ao lookup de ISBN)
- `web/`: `app.py` + `templates/` (`index.html`, `adicionar.html`, `editar.html`)
- Rotas web (todas testadas no browser): `GET /` (lista; `?q=` pesquisa), `GET/POST /adicionar`, `GET/POST /livros/<int:livro_id>/editar`, `POST /livros/<int:livro_id>/remover` (só POST), `GET /pesquisar-isbn?isbn=` (JSON; **caminho de sucesso nunca validado no browser** por causa do 429 da Google Books; o parsing real de `_fetch_google_books`/`_fetch_open_library` continua sem teste de sucesso)
- Flask com `debug=True` só ao correr `python web/app.py` (localhost); no container o `gunicorn` não executa esse bloco

## Próximo passo

1. **PR #2** (validação do ISBN ao gravar): no PC novo, `git fetch` + `git switch feat/validate-isbn-on-save`, `& $py -m pytest`, e testar a GUI no ecrã (gravar `123456789` → "ISBN inválido"; gravar `978-0-13-235088-4` → aparece `9780132350884`). Integrar só depois da confirmação do Miguel. Apagar no GitHub as branches já integradas (`fix/update-book-clear-fields`, e esta depois do merge).
2. **PC original** (o PR #1 já está na `main`): `git config --global user.email ...` (ver Git), `git switch main`, `git pull`; correr as duas consultas só de leitura em `docs/historico.md` (`""` antigos, secção dos campos vazios; ISBN inválidos ou com hífenes, secção da validação do ISBN). Livros com ISBN inválido têm de ter o ISBN corrigido ou apagado na próxima edição.
3. A escolher: testar o parsing de `_fetch_google_books`/`_fetch_open_library` com respostas simuladas (trocar `_pedir_json`); (B) notebook de EDA com pandas e apresentar a validação de ISBN/deteção de duplicados como data quality no README (alinhado com o alvo de carreira do Miguel); limpar avisos do basedpyright (ou modo estrito).

Pendente: na web, o formulário de adicionar volta vazio quando há erro (o utilizador perde o que escreveu). CSRF no formulário de remover (só necessária antes de expor a app a uma rede). Backlog secundário: confirmar visualmente uma capa (bloqueado pela falha das APIs); chave de API gratuita da Google Books se o lookup for retomado; decidir se o `CLAUDE.md` passa a ser versionado na raiz.

## Última sessão (2026-10-21)

- **Início:** o PR #1 já tinha sido integrado na `main` (merge `36c0f2a`), ao contrário do que este ficheiro dizia.
- **Branch:** `feat/validate-isbn-on-save` → PR #2 (CI por confirmar).
- **Mudou:** ISBN normalizado (`normalize_isbn`) e validado em `add_book`/`update_book`, que lançam `InvalidISBNError`; GUI e web mostram "ISBN inválido". O mesmo ISBN com e sem hífenes passa a ser detetado como duplicado.
- **Testes:** 70 passed (+11); basedpyright 0 erros, 300 avisos (+17, do tipo já existente).
- **Verificado:** pytest e basedpyright na cloud (Python 3.13, não 3.14); GUI só em modo `offscreen`.
- **Por verificar:** GUI no ecrã; CI do PR #2; ISBN antigos na `biblioteca.db` real; Docker não tocado.
- **Decisões:** validação na camada de dados com exceção própria; forma canónica sem hífenes; `isbn=None` não valida o valor antigo. A branch `fix/update-book-clear-fields` ficou por apagar (bloqueado na cloud).

## Regras de trabalho

- PT-PT; código e nomes em inglês; README e descrição do GitHub em inglês. Miguel não é engenheiro informático: termos técnicos definidos na primeira menção.
- Passos pequenos, código comentado, forma de testar. Não assumir factos sobre ferramentas: confirmar na prática.
- Lint: correr a ferramenta no terminal e ler a lista completa antes de suspeitar. Rede: testar fora do Python (`Invoke-WebRequest`) antes de suspeitar do código.
- Uma branch por tarefa, nunca commits diretos na `main`; integrar só depois de o Miguel confirmar.
- Atualizar este ficheiro ao fechar um bloco coerente; incidentes e decisões novas vão para `docs/historico.md`. No fim da sessão, sugerir título em `kebab-case`.

## Título desta sessão

`validacao-isbn-ao-gravar`
