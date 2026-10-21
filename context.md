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
- **basedpyright:** 0 erros, 346 avisos (deixados por resolver de propósito). `pyrightconfig.json` só com `"failOnWarnings": false`: só erros reprovam. Com a venv ativada, `basedpyright` sem flags usa o Python ativo; o CI e o PC novo usam `--pythonpath <python da venv>`
- **Testes e CI:** `pytest` a partir da raiz; **97 testes, todos passam, 0 `xfail`** (`tests/test_database.py` tem 27; `tests/test_web.py` 20; `tests/test_isbn_fetch.py` 18; `tests/test_isbn.py` 17; `tests/test_normalize.py` 7; `tests/test_pedir_bytes.py` 8). CI em `.github/workflows/ci.yml` (GitHub Actions) corre `pytest` + `basedpyright` em cada push para a `main` e em cada PR; verde nos PR #1, #2 e #3 (todos integrados)
- **Sessões cloud do Claude Code:** fazem push de branches novas, mas **não conseguem apagar branches remotas** (403 do proxy); isso faz-se no GitHub (Branches → caixote do lixo) ou com `git push origin --delete <branch>` num PC. **Sem acesso à Google Books nem à Open Library** (rede bloqueada): respostas reais só se obtêm num PC. **O disco da sessão apaga-se ao fechar: push imediato depois de cada commit** (um commit sem push perdeu-se em 2026-10-21)
- **Testar uma branch que já existe no PC:** `git switch <branch>` usa a cópia local, que pode estar desatualizada; fazer sempre `git pull` a seguir (aconteceu em 2026-10-21)
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
- **ISBN ao gravar** (desde 2026-10-21): `add_book`/`update_book` gravam-no na forma canónica (`isbn_lookup.normalize_isbn`: sem hífenes nem espaços, `X` maiúsculo) e **gravam-no mesmo com dígito de controlo inválido** (decisão do Miguel: assinalar, não recusar). A GUI mostra um aviso depois de gravar e pinta o ISBN a vermelho na tabela (com explicação ao passar o rato); a web pinta-o a vermelho e acrescenta "⚠ ISBN inválido" na lista, via `isbn_valido` registada no Jinja. Ambas cobrem também os livros antigos `update_book` com `isbn=None` mantém o valor antigo intacto
- Docker: `python:3.14-slim`, `gunicorn==26.2.0` instalado só na imagem (não está em `requirements-web.txt`), utilizador sem privilégios, `BIBLIOTECA_DB=/data/biblioteca.db`; o `create_tables()` corre no `CMD` antes do `gunicorn`. Comandos: `docker build -t biblioteca-web .` e `docker run --rm -p 8000:8000 -v biblioteca-data:/data biblioteca-web` (http://localhost:8000). A BD do container é separada da da desktop; contém 1 "Livro de teste"
- `tests/`: `conftest.py` (fixture `isolated_db`), `test_isbn.py`, `test_normalize.py`, `test_database.py`, `test_web.py` (fixtures `client` e `block_isbn_network`, esta autouse: faz rebentar qualquer chamada real ao lookup de ISBN), `test_isbn_fetch.py` (troca `_pedir_json` por respostas simuladas da Google Books e da Open Library; fixture autouse `no_network` faz rebentar qualquer pedido real), `test_pedir_bytes.py` (retry de `_pedir_bytes`, com `urlopen` e `time.sleep` simulados; 4xx não é repetido, 5xx e falhas de rede são)
- `web/`: `app.py` + `templates/` (`index.html`, `adicionar.html`, `editar.html`)
- Rotas web (todas testadas no browser): `GET /` (lista; `?q=` pesquisa), `GET/POST /adicionar`, `GET/POST /livros/<int:livro_id>/editar`, `POST /livros/<int:livro_id>/remover` (só POST), `GET /pesquisar-isbn?isbn=` (JSON; caminho de sucesso nunca validado no browser por causa do 429 da Google Books; o parsing de `_fetch_google_books`/`_fetch_open_library` está testado com respostas simuladas, a da Open Library **confirmada contra a resposta real** em 2026-10-21; a da Google **ainda por confirmar**, porque a quota sem chave está a zero)
- Flask com `debug=True` só ao correr `python web/app.py` (localhost); no container o `gunicorn` não executa esse bloco

## Próximo passo

1. **PR da branch `fix/no-retry-on-http-4xx`** (opção c: erros HTTP 4xx deixam de ser repetidos; já no GitHub, PR por abrir — pedir autorização). Depois de o CI ficar verde, teste manual num PC (`git fetch`, `git switch fix/no-retry-on-http-4xx`, `git pull`): `python -c "import time, isbn_lookup as i; t=time.time(); print(i.lookup_isbn('9780132350884')); print(round(time.time()-t,1), 's')"` deve devolver os dados da Open Library sem as ~2 s de pausas. Integrar depois da confirmação do Miguel. A Google continua sem quota; a chave de API (a) ou a ordem da cascata (b) ficam em aberto.
2. **PC original:** `git config --global user.email ...` (ver Git), `git switch main`, `git pull`; correr as duas consultas só de leitura em `docs/historico.md` (`""` antigos; ISBN inválidos ou com hífenes). Os ISBN inválidos já aparecem a vermelho na GUI e na web.
3. **Proteger a `main` no GitHub** (aviso "Your main branch isn't protected"): "Protect this branch" → exigir o CI verde, bloquear force push e eliminação; se ligar "require pull request", 0 aprovações. Feito pelo Miguel.
4. **Apagar no GitHub** as branches integradas: `feat/validate-isbn-on-save`, `test/isbn-fetch-parsing` (e `fix/no-retry-on-http-4xx` depois do merge).
5. **Acrescentar ao `CLAUDE.md`** (secção "COMO TRABALHAR"): "Nas sessões cloud, faz push imediato depois de cada commit: o disco da sessão apaga-se ao fechar." Feito pelo Miguel (o ficheiro não está versionado).
6. A escolher: (B) notebook de EDA com pandas e apresentar a validação de ISBN/deteção de duplicados como data quality no README (alinhado com o alvo de carreira do Miguel); limpar avisos do basedpyright (ou modo estrito); usar os `subjects` da Open Library para sugerir o género (são temas detalhados, não um género: exige escolher um ou mapear).

Pendente: na web, o formulário de adicionar volta vazio quando há erro (o utilizador perde o que escreveu). CSRF no formulário de remover (só necessária antes de expor a app a uma rede). Hipótese por confirmar: `_pedir_bytes` só apanha `URLError` e `TimeoutError`; um reset de ligação a meio da leitura (`ConnectionResetError`) pode não ser apanhado. Backlog secundário: confirmar visualmente uma capa (a Open Library já devolve uma URL real: `https://covers.openlibrary.org/b/id/15126503-M.jpg`); o título da Google e da Open Library ignora o `subtitle`; decidir se o `CLAUDE.md` passa a ser versionado na raiz.

## Última sessão (2026-10-21, tarde)

- **Divergência à entrada:** a branch `fix/no-retry-on-http-4xx` da sessão anterior nunca chegou ao GitHub (commit sem push; o disco da cloud apagou-se). O GitHub estava em 89 testes e 341 avisos. Trabalho refeito.
- **PR #3 integrado** (merge `9448bda`, CI verde, com autorização do Miguel). Branch `fix/no-retry-on-http-4xx` recriada a partir da `main` (commit `c168502`, **já com push**): 4xx sem retry; 5xx e falhas de rede como antes. 8 testes em `tests/test_pedir_bytes.py`; os 4 de 4xx falham com o código antigo.
- **Testes:** 97 passed; basedpyright 0 erros, 346 avisos (+5, `reportPrivateUsage`).
- **Por verificar:** CI da branch (PR por abrir); teste manual do tempo de pesquisa num PC; forma real da resposta da Google; GUI e Docker não tocados.
- **Decisões:** push imediato depois de cada commit nas sessões cloud (nova regra); o `context.md` desta sessão partiu da cópia do Miguel, não da do repositório (que estava atrasada).

## Regras de trabalho

- PT-PT; código e nomes em inglês; README e descrição do GitHub em inglês. Miguel não é engenheiro informático: termos técnicos definidos na primeira menção.
- Passos pequenos, código comentado, forma de testar. Não assumir factos sobre ferramentas: confirmar na prática.
- Lint: correr a ferramenta no terminal e ler a lista completa antes de suspeitar. Rede: testar fora do Python (`Invoke-WebRequest`) antes de suspeitar do código.
- Uma branch por tarefa, nunca commits diretos na `main`; integrar só depois de o Miguel confirmar. Nas sessões cloud, push logo a seguir a cada commit.
- Atualizar este ficheiro ao fechar um bloco coerente; incidentes e decisões novas vão para `docs/historico.md`. No fim da sessão, sugerir título em `kebab-case`.

## Título desta sessão

`integrar-pr3-e-refazer-sem-retry-4xx`
