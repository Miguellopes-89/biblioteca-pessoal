# context.md — Biblioteca Pessoal

> Estado da sessão do projeto. Carregado pelo Miguel no menu "Contexto" do Projeto antes de cada sessão (a cópia em disco é a mais recente). Incidentes, decisões antigas e detalhe das alterações: `docs/historico.md` — ler a pedido, só quando o tema for relevante.

## Sobre o projeto

Aplicação desktop em Python para catalogar livros pessoais (título, autor(es), editora, coleção, género, ISBN, estado de leitura), com inserção manual e/ou por ISBN via APIs gratuitas (Google Books + Open Library, em cascata, com validação do dígito de controlo antes de pesquisar), SQLite local, GUI em PySide6, funcionamento offline. **Publicado no GitHub** como portefólio: https://github.com/Miguellopes-89/biblioteca-pessoal (público, README, LICENSE MIT).

**Fase web concluída**: versão Flask (`web/`) que reutiliza `database.py` e `isbn_lookup.py` a par da app desktop (não a substitui). Corre localmente com `python web/app.py` (mesma BD da desktop) ou em container Docker com `gunicorn` (BD própria, num volume).

## Ambiente

- **SO:** Windows · **Python:** 3.14.6 · **Git:** 2.55.0 · **`gh`:** 2.96.0 (autenticado como `Miguellopes-89`) · **Editor:** Zed · **Docker:** Desktop 29.7.2 a funcionar (o daemon tem de estar ativo: abrir o Docker Desktop antes de qualquer `docker`); imagem `biblioteca-web`, volume `biblioteca-data`
- **Caminho do projeto:** `C:\Users\User\Projetos\biblioteca-pessoal`; venv: `.\venv\Scripts\Activate.ps1`
- **Dependências:** `PySide6` 6.11.2 (`requirements.txt`) e `Flask` 3.1.3 (`requirements-web.txt`) separados deliberadamente; `requirements-dev.txt` com `pytest` 9.1.1 e `basedpyright`
- **basedpyright:** 0 erros, 145 avisos (deixados por resolver de propósito). `pyrightconfig.json` com `"failOnWarnings": false`: só erros reprovam
- **Testes e CI:** `pytest` a partir da raiz, venv ativo; **39 testes a passar**. CI em `.github/workflows/ci.yml` (GitHub Actions) corre `pytest` + `basedpyright`; última execução verde
- **Acesso de Claude ao PC:** Filesystem (`mcp__Filesystem__*`, restrito a `C:\Users\User\Projetos`) ativo; **sem shell/PowerShell** — `git`, `pip`, `pytest`, `python web/app.py` corre-os o Miguel e cola o output
- **Colar código no Zed:** causa mais comum de bugs (4 vezes) — confirmar visualmente a indentação de blocos `if`/`try` depois de colar

## Git

- Branch única `main`, remoto `origin` → `https://github.com/Miguellopes-89/biblioteca-pessoal.git`
- HEAD de partida desta sessão (2026-10-04): `3533b9c` "Atualiza estado Git no context.md" (em sincronia com `origin/main`). O bloco Docker (Dockerfile, .dockerignore, `database.py`, README, este ficheiro) ficou por commitar no fim da sessão. Este ficheiro não regista o HEAD de cada commit: confirmar sempre com `git log --oneline -8` e `git status` antes de continuar
- `.gitignore`: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`, `.pytest_cache/`

## Ficheiros

- Raiz: `gui.py` (PySide6), `database.py`, `isbn_lookup.py`, `main.py` (smoke test antigo, não usado), `README.md` (inglês), `LICENSE`, `pytest.ini`, `pyrightconfig.json`, `Dockerfile`, `.dockerignore`, `biblioteca.db` (não versionado, 9 livros)
- `database.py` expõe: `normalize_text`, `connect`, `create_tables`, `get_or_create_author`, `add_book`, `list_books`, `search_books`, `update_book`, `delete_book`, `get_book`. `DB_NAME` lê a variável de ambiente `BIBLIOTECA_DB` e, se não existir, usa o caminho absoluto de `biblioteca.db` junto ao ficheiro; listagens ordenadas sem acentos nem maiúsculas
- Docker: `python:3.14-slim`, `gunicorn==26.2.0` instalado só na imagem (não está em `requirements-web.txt`), utilizador sem privilégios, `BIBLIOTECA_DB=/data/biblioteca.db`; o `create_tables()` corre no `CMD` antes do `gunicorn` (não passa pelo `__main__` do `app.py`). Comandos: `docker build -t biblioteca-web .` e `docker run --rm -p 8000:8000 -v biblioteca-data:/data biblioteca-web` (http://localhost:8000). Persistência confirmada no browser: o livro sobreviveu ao reinício do container. A BD do container é separada da da desktop; contém 1 "Livro de teste"
- `tests/`: `conftest.py` (fixture `isolated_db`), `test_isbn.py`, `test_normalize.py`, `test_database.py`
- `web/`: `app.py` + `templates/` (`index.html`, `adicionar.html`, `editar.html`)
- Rotas web (todas testadas no browser): `GET /` (lista; `?q=` pesquisa), `GET/POST /adicionar`, `GET/POST /livros/<int:livro_id>/editar`, `POST /livros/<int:livro_id>/remover` (só POST), `GET /pesquisar-isbn?isbn=` (JSON; casos de erro confirmados, **caminho de sucesso nunca validado** por causa do 429 da Google Books — arrumado por decisão do Miguel)
- Flask com `debug=True` só ao correr `python web/app.py` (localhost); no container o `gunicorn` não executa esse bloco, por isso o debugger não fica ativo

## Próximo passo

A escolher (fase web fechada). Pendente, de custo pequeno: proteção CSRF no formulário de remover (mencionada no README; só necessária antes de expor a app a uma rede).

Opções: (B) notebook de EDA com pandas sobre a própria biblioteca e apresentar a validação de ISBN/deteção de duplicados como data quality no README (alinhado com o alvo de carreira do Miguel); testes das rotas Flask com o test client; testar o lookup de ISBN com respostas de API simuladas; limpar os 24 avisos novos dos testes (ou modo estrito, zero avisos).

Backlog secundário: confirmar visualmente uma capa (bloqueado pela falha das APIs); chave de API gratuita da Google Books se o lookup for retomado.

## Regras de trabalho

- PT-PT; código e nomes em inglês; README e descrição do GitHub em inglês. Miguel não é engenheiro informático: termos técnicos definidos na primeira menção.
- Passos pequenos, código comentado, forma de testar. Não assumir factos sobre ferramentas: confirmar na prática.
- Lint: correr a ferramenta no terminal e ler a lista completa antes de suspeitar. Rede: testar fora do Python (`Invoke-WebRequest`) antes de suspeitar do código.
- Atualizar este ficheiro ao fechar um bloco coerente; incidentes e decisões novas vão para `docs/historico.md`. No fim da sessão, sugerir título em `kebab-case`.

## Título desta sessão

`instrucao-projeto-context-historico-split`
