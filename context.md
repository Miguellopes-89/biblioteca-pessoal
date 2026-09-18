# context.md — Biblioteca Pessoal

> Este ficheiro é o "estado da sessão" do projeto. Cola o conteúdo no início de uma nova conversa com o Claude para retomar exatamente onde ficámos, sem reexplicar nada.

## Sobre o projeto

Aplicação desktop em Python para catalogar livros pessoais (título, autor(es), editora, coleção, género, ISBN, estado de leitura), com inserção manual e/ou por leitura de ISBN via APIs gratuitas (Google Books + Open Library, em cascata, com validação de dígito de controlo antes de pesquisar), base de dados SQLite local, GUI desktop em PySide6, funcionamento offline. **Publicado no GitHub** como portefólio: https://github.com/Miguellopes-89/biblioteca-pessoal (público, com README, LICENSE MIT e requirements.txt). Fase web é possibilidade futura (Docker pode entrar aí).

Claude atua como tutor sénior: explica o "porquê" de cada decisão, avança passo a passo, nunca assume conhecimento prévio, nunca assume factos sobre o ambiente sem confirmar.

## Ambiente

- **SO:** Windows
- **Python:** 3.14.6
- **Git:** 2.55.0
- **GitHub CLI (`gh`):** 2.96.0, autenticado como `Miguellopes-89`
- **Editor:** Zed
- **Docker:** instalado, não relevante ainda (fase web futura)
- **Caminho do projeto:** `C:\Users\User\Projetos\biblioteca-pessoal`
- **Ambiente virtual:** ativar sempre: `.\venv\Scripts\Activate.ps1`
- **Dependências no venv:** só `PySide6` 6.11.2 (e subpacotes `PySide6_Addons`, `PySide6_Essentials`, `shiboken6`). O `venv` corresponde exatamente ao `requirements.txt`.
- **`pyrightconfig.json`** aponta o linter do Zed para o `venv`. O `basedpyright` deste projeto usa regras mais estritas que o pyright standard (ex.: `reportExplicitAny`, `reportUnusedCallResult`, `reportAny`).
- **Importante:** a partir desta sessão, Claude já não tem acesso direto ao filesystem nem à shell deste PC (foi revogado para poupar tokens). Claude dá instruções passo a passo (comandos exatos, código exato com indicação de onde colar) e Miguel executa. Miguel não é engenheiro informático — as instruções devem ser claras e sem assumir conhecimento técnico.

## Estado atual do repositório Git

- Branch única: `main`, remoto `origin` → `https://github.com/Miguellopes-89/biblioteca-pessoal.git` (público)
- Working tree limpa, tudo commitado e sincronizado com o GitHub no fim desta sessão
- `.gitignore` cobre: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`
- Últimos commits (mais recente primeiro):
  - `Adiciona type hints as funcoes de database.py`
  - `Adiciona README, LICENSE, requirements.txt e validacao de digito de controlo do ISBN`
  - `Atualiza context.md apos lookup de ISBN, polimento GUI e publicacao no GitHub`
  - `Redimensiona colunas da tabela automaticamente (ID encolhe, Titulo estica)`
  - `Adiciona lookup de ISBN via Google Books/Open Library com QThread`

## Ficheiros existentes

- `.gitignore`
- `README.md` — em inglês (alcance junto de recrutadores). Descrição, funcionalidades, stack, instalação, estrutura, schema, notas sobre o lookup de ISBN, roadmap.
- `LICENSE` — MIT.
- `requirements.txt` — só `PySide6==6.11.2`.
- `main.py` — smoke test original, não usado pela GUI.
- `pyrightconfig.json`
- `database.py` — módulo SQLite, **agora com type hints em todas as funções**. Expõe: `normalize_text`, `connect`, `create_tables`, `get_or_create_author`, `add_book`, `list_books`, `search_books`, `update_book`, `delete_book`. Zero erros do basedpyright neste ficheiro (só avisos preexistentes de `reportUnusedCallResult`/`reportAny`, deliberadamente não resolvidos — ver "Notas técnicas").
- `isbn_lookup.py` — sem dependência do PySide6 (testável isoladamente). Contém:
  - `_pedir_json(url)` — GET com `urllib.request`, `User-Agent` próprio, retry automático (`TENTATIVAS = 3`, 1s de pausa) por causa de falhas de rede intermitentes nesta máquina (ver "Incidentes").
  - `_fetch_google_books` / `_fetch_open_library` — uma função por fonte, dict normalizado (`titulo`, `autores_str`, `editora`, `genero`) ou `None`.
  - `lookup_isbn(isbn)` — cascata: Google Books primeiro, Open Library só se a primeira não encontrar nada. Não funde campos das duas fontes.
  - `validar_isbn(isbn)` — valida dígito de controlo (ISBN-10 e ISBN-13, incluindo `X` final e hífens). Não confirma que o livro existe — só que o número é matematicamente válido.
  - Nenhuma API expõe de forma fiável "coleção" (série) — continua manual.
- `gui.py` — `PesquisaISBNThread(QThread)` corre o lookup em segundo plano (referência guardada em `self.thread_pesquisa_isbn`, nunca variável local). Botão "Procurar" valida com `validar_isbn()` antes de gastar uma chamada de rede. `ao_receber_resultado_isbn()` preenche só os campos que a API devolveu com conteúdo. Colunas da tabela redimensionam automaticamente. **Tem 8 erros do basedpyright por resolver** (suspeita não confirmada: padrão `self.tabela_livros.item(...).text()` sem verificar `None` — a investigar quando abordarmos este ficheiro).
- `biblioteca.db` — não versionado, 4 livros de teste.

## Modelo de dados (schema SQLite)

- **livros**: `id` (PK), `titulo`, `editora`, `colecao`, `genero`, `isbn` (UNIQUE), `estado_leitura` (NOT NULL, DEFAULT 'não lido')
- **autores**: `id` (PK), `nome` (UNIQUE)
- **livro_autor**: `livro_id` + `autor_id` (PK composta, FKs)

## Incidentes resolvidos (histórico, não repetir)

1. **Google Books API sem chave devolve HTTP 429** — quota global partilhada, esgotada com frequência. Por isso o fallback para Open Library é essencial.
2. **`requests`/`urllib3` com ligações resetadas** pela Open Library nesta máquina (WinError 10054). Diagnosticado como interferência do **Network Inspection System (NIS)** do Windows Defender. Solução: `urllib.request` (standard library) + retry automático (3 tentativas).

## Notas técnicas / decisões tomadas

- Cascata de APIs, não fusão de campos (Google Books → Open Library como reserva).
- `urllib.request` em vez de `requests` — zero dependências externas.
- Retry simples (3 tentativas, 1s fixo), sem backoff exponencial.
- `QThread` para a chamada de rede — referência sempre em atributo da instância.
- Validação de dígito de controlo do ISBN feita **antes** do lookup.
- Preenchimento seletivo dos campos após lookup — Coleção e Estado de leitura nunca são tocados.
- PySide6 (não `tkinter`) — decisão de portefólio.
- Repositório GitHub público, README em inglês (alcance junto de recrutadores).
- LICENSE MIT adicionada.
- **Type hints em `database.py`:** sintaxe moderna `str | None` (não `Optional`); `list_books()`/`search_books()` devolvem `list[dict[str, str | int | None]]` — reflete os tipos reais das colunas, sem usar `Any` (o `basedpyright` deste projeto proíbe `Any` explícito via `reportExplicitAny`).
- **`cursor.lastrowid`** é `int | None` nos stubs do `sqlite3`; `get_or_create_author()` usa `assert cursor.lastrowid is not None` antes do `return` (garantia válida a seguir a um INSERT bem-sucedido) para manter a assinatura `-> int`.
- Os 93 avisos restantes do basedpyright (`reportUnusedCallResult`, `reportAny`) em `database.py` são preexistentes e ficam deliberadamente por resolver — exigiriam silenciar regras no `pyrightconfig.json` ou TypedDict/cast em cada leitura, fora do escopo desta sessão.
- Decisões antigas sobre o modelo de dados (ISBN como chave de duplicado, `LOWER()` para autores, normalização via `unicodedata`, autores órfãos mantidos) continuam válidas.

## Próximo passo

Ordem acordada:

1. ~~Type hints em `database.py`~~ — **feito**.
2. **Capas de livro** — a Open Library já devolve um URL de capa (`cover.medium`/`large`) no lookup; mostrar na GUI.
3. Fase web (Docker) — sem prazo.

Backlog secundário, sem urgência:
- Investigar os 8 erros do basedpyright em `gui.py` (suspeita: `.item(...).text()` sem verificar `None`).
- Melhorias menores de UX (ex.: mensagens de erro mais específicas).

## Regras de trabalho (lembrete permanente)

- **Claude já não tem acesso direto ao filesystem/shell deste PC** (revogado nesta sessão, para poupar tokens). Claude dá instruções passo a passo — comandos exatos para colar, código exato com indicação clara de onde vai — e Miguel executa e reporta o resultado (screenshots ou output colado).
- Miguel não é engenheiro informático — explicações claras, sem assumir jargão não explicado.
- Avançar em passos pequenos, um conceito de cada vez, com explicação, código comentado, forma de testar.
- Comunicação em Português Europeu (PT-PT). Código e nomes de variáveis/funções em inglês. Exceção deliberada: README e descrição do GitHub em inglês.
- Atualizar este ficheiro sempre que se fechar um bloco de trabalho coerente.
- No fim de cada sessão, sugerir título em `kebab-case`.
- Sempre que uma chamada de rede falhar de forma inesperada, testar primeiro fora do Python (`Invoke-WebRequest`) antes de assumir bug de código.

## Título desta sessão

`type-hints-database-py-basedpyright-estrito`
