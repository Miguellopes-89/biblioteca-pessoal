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
- **Acesso de Claude ao PC:** varia dentro da própria sessão — Miguel liga/desliga o Windows-MCP (filesystem + shell) conforme o consumo de tokens. Quando desligado, Claude dá instruções passo a passo (comandos exatos, código exato com indicação de onde colar) e Miguel executa. Miguel não é engenheiro informático — explicações claras, sem assumir jargão não explicado.
- **Cuidado ao colar código no Zed:** já aconteceu mais de uma vez colar um bloco com `if`/`try` e a indentação ficar desalinhada (o editor não é um campo de texto simples). Uma vez causou `IndentationError` (fácil de detetar); outra vez causou um bug silencioso sem erro nenhum (ver "Incidentes"). Depois de colar blocos com `if`/`try`/`except`, vale a pena confirmar visualmente a indentação antes de correr.

## Estado atual do repositório Git

- Branch única: `main`, remoto `origin` → `https://github.com/Miguellopes-89/biblioteca-pessoal.git` (público)
- Working tree limpa, tudo commitado e sincronizado com o GitHub no fim desta sessão
- `.gitignore` cobre: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`
- Últimos commits (mais recente primeiro):
  - `Adiciona previsualizacao de capa no lookup de ISBN`
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
- `database.py` — módulo SQLite, com type hints em todas as funções. Expõe: `normalize_text`, `connect`, `create_tables`, `get_or_create_author`, `add_book`, `list_books`, `search_books`, `update_book`, `delete_book`. Zero erros do basedpyright neste ficheiro (só avisos preexistentes, deliberadamente não resolvidos).
- `isbn_lookup.py` — sem dependência do PySide6 (testável isoladamente). Contém:
  - `_pedir_bytes(url)` — GET com `urllib.request`, `User-Agent` próprio, retry automático (`TENTATIVAS = 3`, 1s de pausa). Devolve bytes em bruto; base de `_pedir_json` e de `baixar_capa`.
  - `_pedir_json(url)` — usa `_pedir_bytes` e interpreta o resultado como JSON.
  - `baixar_capa(url)` — **novo**. Descarrega os bytes de uma imagem de capa; devolve `None` se o url for vazio ou o download falhar.
  - `_fetch_google_books` / `_fetch_open_library` — uma função por fonte, dict normalizado (`titulo`, `autores_str`, `editora`, `genero`, **`capa_url`**) ou `None`.
  - `lookup_isbn(isbn)` — cascata: Google Books primeiro, Open Library só se a primeira não encontrar nada.
  - `validar_isbn(isbn)` — valida dígito de controlo (ISBN-10 e ISBN-13). Não confirma que o livro existe.
  - Nenhuma API expõe de forma fiável "coleção" (série) — continua manual.
- `gui.py` — `PesquisaISBNThread(QThread)` corre o lookup em segundo plano e, se encontrar resultado, descarrega também a capa (`baixar_capa`) na mesma thread — guarda os bytes em `resultado["capa_bytes"]`. O `run()` tem um `try/except` de diagnóstico que imprime o traceback no terminal em caso de erro (**deixar ficar** — já provou o seu valor a apanhar bugs). Novo `QLabel` (`self.label_capa`, 120x180px) ao lado do formulário mostra a capa via `QPixmap.scaled(..., KeepAspectRatio)`, ou "Sem capa" se não houver imagem — **é só pré-visualização, não é guardada na base de dados** (decisão consciente, Opção A do scope). Botão "Procurar" valida com `validar_isbn()` antes de gastar uma chamada de rede. `ao_receber_resultado_isbn()` preenche só os campos que a API devolveu com conteúdo. **Tem 8 erros do basedpyright por resolver** (suspeita não confirmada: padrão `self.tabela_livros.item(...).text()` sem verificar `None` — a investigar quando abordarmos este ficheiro).
- `biblioteca.db` — não versionado, 5 livros de teste.

## Modelo de dados (schema SQLite)

- **livros**: `id` (PK), `titulo`, `editora`, `colecao`, `genero`, `isbn` (UNIQUE), `estado_leitura` (NOT NULL, DEFAULT 'não lido')
- **autores**: `id` (PK), `nome` (UNIQUE)
- **livro_autor**: `livro_id` + `autor_id` (PK composta, FKs)
- Nota: a capa de livro **não está no schema** — é só pré-visualização (ver "Ficheiros existentes" → `gui.py`). Guardá-la na BD seria a "Opção B", não escolhida.

## Incidentes resolvidos (histórico, não repetir)

1. **Google Books API sem chave devolve HTTP 429** — quota global partilhada, esgotada com frequência. Por isso o fallback para Open Library é essencial. Em dois testes desta sessão, ambas as APIs falharam ao mesmo tempo para livros conhecidos (Clean Code, Harry Potter) — confirmado por teste isolado (`python -c "from isbn_lookup import lookup_isbn; print(lookup_isbn(...))"`) que é coincidência das APIs, não bug de código.
2. **`requests`/`urllib3` com ligações resetadas** pela Open Library nesta máquina (WinError 10054). Diagnosticado como interferência do **Network Inspection System (NIS)** do Windows Defender. Solução: `urllib.request` (standard library) + retry automático (3 tentativas).
3. **Bug do botão "Procurar" preso indefinidamente** — ao colar o código da funcionalidade de capa, `self.resultado_pronto.emit(resultado)` ficou (por erro de indentação ao colar) dentro do `if resultado is not None:`. Quando a API não encontrava nada (o caso mais comum), o sinal nunca era emitido, e sem sinal a GUI nunca sabe que a pesquisa terminou. Sem exceção nenhuma, o terminal ficava mudo. Diagnosticado isolando `isbn_lookup.py` da GUI (teste sem thread) e inspecionando o ficheiro diretamente via filesystem.

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
- Type hints em `database.py`: sintaxe moderna `str | None`; `list_books()`/`search_books()` devolvem `list[dict[str, str | int | None]]` — sem `Any` (proibido por `reportExplicitAny`).
- `cursor.lastrowid` é `int | None` nos stubs do `sqlite3`; `get_or_create_author()` usa `assert cursor.lastrowid is not None`.
- Os 93 avisos do basedpyright (`reportUnusedCallResult`, `reportAny`) em `database.py` ficam deliberadamente por resolver.
- **Capa de livro:** só pré-visualização (Opção A), descarregada na mesma `QThread` da pesquisa ISBN. Google Books dá o URL direto (`imageLinks.thumbnail`, forçado para `https://`); Open Library dá `cover.medium`.
- `try/except` de diagnóstico no `run()` do `PesquisaISBNThread`, com print do traceback — mantido deliberadamente, já ajudou a apanhar um bug real.
- Decisões antigas sobre o modelo de dados (ISBN como chave de duplicado, `LOWER()` para autores, normalização via `unicodedata`, autores órfãos mantidos) continuam válidas.

## Próximo passo

Ordem acordada:

1. ~~Type hints em `database.py`~~ — **feito**.
2. ~~Capas de livro (pré-visualização)~~ — **feito**, implementado e testado (fluxo "não encontrado" confirmado; fluxo "capa aparece" ainda não visto em ação por coincidência de falhas das duas APIs — sem indicação de bug, só falta de sorte com a rede).
3. Fase web (Docker) — sem prazo.

Backlog secundário, sem urgência:
- Investigar os 8 erros do basedpyright em `gui.py` (suspeita: `.item(...).text()` sem verificar `None`).
- Confirmar visualmente que uma capa aparece (testar com um ISBN quando as APIs estiverem a responder normalmente).
- Melhorias menores de UX (ex.: mensagens de erro mais específicas).

## Regras de trabalho (lembrete permanente)

- **Acesso de Claude ao PC varia** — Miguel liga/desliga o Windows-MCP (filesystem + shell) dentro da mesma sessão, conforme o consumo de tokens. Quando desligado, Claude dá instruções passo a passo e Miguel executa e reporta (screenshots ou output colado). Quando ligado, Claude confirma o estado real dos ficheiros antes de assumir que uma instrução anterior foi aplicada corretamente.
- Miguel não é engenheiro informático — explicações claras, sem assumir jargão não explicado.
- Avançar em passos pequenos, um conceito de cada vez, com explicação, código comentado, forma de testar.
- Comunicação em Português Europeu (PT-PT). Código e nomes de variáveis/funções em inglês. Exceção deliberada: README e descrição do GitHub em inglês.
- Atualizar este ficheiro sempre que se fechar um bloco de trabalho coerente.
- No fim de cada sessão, sugerir título em `kebab-case`.
- Sempre que uma chamada de rede falhar de forma inesperada, testar primeiro fora do Python (`Invoke-WebRequest`, ou isolar com `python -c "..."` sem GUI) antes de assumir bug de código.
- Depois de colar blocos de código com `if`/`try`/`except`, confirmar visualmente a indentação antes de correr — é a causa mais comum de bugs nesta sessão.

## Título desta sessão

`preview-capa-livro-isbn-lookup-bug-indentacao-thread`
