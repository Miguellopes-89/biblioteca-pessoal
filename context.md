# context.md — Biblioteca Pessoal

> Estado da sessão do projeto. Carregado pelo Miguel no menu "Contexto" do Projeto antes de cada sessão (a cópia em disco é a mais recente). Incidentes, decisões antigas e detalhe das alterações: `docs/historico.md` — ler a pedido, só quando o tema for relevante.

## Sobre o projeto

Aplicação desktop em Python para catalogar livros pessoais (título, autor(es), editora, coleção, género, ISBN, estado de leitura), com inserção manual e/ou por ISBN via APIs gratuitas (Google Books + Open Library, em cascata, com validação do dígito de controlo antes de pesquisar), SQLite local, GUI em PySide6, funcionamento offline. **Publicado no GitHub** como portefólio: https://github.com/Miguellopes-89/biblioteca-pessoal (público, README, LICENSE MIT).

**Fase web em curso**: versão Flask (`web/`) que reutiliza `database.py` e `isbn_lookup.py` sem alterações, a par da app desktop (não a substitui), sobre a mesma base de dados.

## Ambiente

- **SO:** Windows · **Python:** 3.14.6 · **Git:** 2.55.0 · **`gh`:** 2.96.0 (autenticado como `Miguellopes-89`) · **Editor:** Zed · **Docker:** instalado, ainda não usado
- **Caminho do projeto:** `C:\Users\User\Projetos\biblioteca-pessoal`; venv: `.\venv\Scripts\Activate.ps1`
- **Dependências:** `PySide6` 6.11.2 (`requirements.txt`) e `Flask` 3.1.3 (`requirements-web.txt`) separados deliberadamente; `requirements-dev.txt` com `pytest` 9.1.1 e `basedpyright`
- **basedpyright:** 0 erros, 145 avisos (deixados por resolver de propósito). `pyrightconfig.json` com `"failOnWarnings": false`: só erros reprovam
- **Testes e CI:** `pytest` a partir da raiz, venv ativo; **39 testes a passar**. CI em `.github/workflows/ci.yml` (GitHub Actions) corre `pytest` + `basedpyright`; última execução verde
- **Acesso de Claude ao PC:** Filesystem (`mcp__Filesystem__*`, restrito a `C:\Users\User\Projetos`) ativo; **sem shell/PowerShell** — `git`, `pip`, `pytest`, `python web/app.py` corre-os o Miguel e cola o output
- **Colar código no Zed:** causa mais comum de bugs (4 vezes) — confirmar visualmente a indentação de blocos `if`/`try` depois de colar

## Git

- Branch única `main`, remoto `origin` → `https://github.com/Miguellopes-89/biblioteca-pessoal.git`
- HEAD em 2026-10-04: `2b63700` "Atualiza README e divide context.md em estado + histórico" (em sincronia com `origin/main`; árvore limpa). Este ficheiro não regista o HEAD de cada commit: confirmar sempre com `git log --oneline -8` e `git status` antes de continuar
- `.gitignore`: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`, `.pytest_cache/`

## Ficheiros

- Raiz: `gui.py` (PySide6), `database.py`, `isbn_lookup.py`, `main.py` (smoke test antigo, não usado), `README.md` (inglês), `LICENSE`, `pytest.ini`, `pyrightconfig.json`, `biblioteca.db` (não versionado, 9 livros)
- `database.py` expõe: `normalize_text`, `connect`, `create_tables`, `get_or_create_author`, `add_book`, `list_books`, `search_books`, `update_book`, `delete_book`, `get_book`. `DB_NAME` é caminho absoluto; listagens ordenadas sem acentos nem maiúsculas
- `tests/`: `conftest.py` (fixture `isolated_db`), `test_isbn.py`, `test_normalize.py`, `test_database.py`
- `web/`: `app.py` + `templates/` (`index.html`, `adicionar.html`, `editar.html`)
- Rotas web (todas testadas no browser): `GET /` (lista; `?q=` pesquisa), `GET/POST /adicionar`, `GET/POST /livros/<int:livro_id>/editar`, `POST /livros/<int:livro_id>/remover` (só POST), `GET /pesquisar-isbn?isbn=` (JSON; casos de erro confirmados, **caminho de sucesso nunca validado** por causa do 429 da Google Books — arrumado por decisão do Miguel)
- Flask com `debug=True` (só para localhost)

## Próximo passo

1. **Docker** — último passo da fase web: containerizar a app Flask. Antes de expor fora de localhost: tirar `debug=True` (o debugger do Werkzeug permite execução remota de código) e usar `gunicorn`; considerar proteção CSRF no formulário de remover (aceitável em localhost, mencionar no README).

Opções para depois: (B) notebook de EDA com pandas sobre a própria biblioteca e apresentar a validação de ISBN/deteção de duplicados como data quality no README (alinhado com o alvo de carreira do Miguel); limpar os 24 avisos novos dos testes (ou modo estrito, zero avisos); testes das rotas Flask com o test client; testar o lookup de ISBN com respostas de API simuladas.

Backlog secundário: confirmar visualmente uma capa (bloqueado pela falha das APIs); chave de API gratuita da Google Books se o lookup for retomado.

## Regras de trabalho

- PT-PT; código e nomes em inglês; README e descrição do GitHub em inglês. Miguel não é engenheiro informático: termos técnicos definidos na primeira menção.
- Passos pequenos, código comentado, forma de testar. Não assumir factos sobre ferramentas: confirmar na prática.
- Lint: correr a ferramenta no terminal e ler a lista completa antes de suspeitar. Rede: testar fora do Python (`Invoke-WebRequest`) antes de suspeitar do código.
- Atualizar este ficheiro ao fechar um bloco coerente; incidentes e decisões novas vão para `docs/historico.md`. No fim da sessão, sugerir título em `kebab-case`.

## Título desta sessão

`instrucao-projeto-context-historico-split`
