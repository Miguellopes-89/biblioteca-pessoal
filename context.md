# context.md — Biblioteca Pessoal

> Este ficheiro é o "estado da sessão" do projeto. Cola o conteúdo no início de uma nova conversa com o Claude para retomar exatamente onde ficámos, sem reexplicar nada.

## Sobre o projeto

Aplicação desktop em Python para catalogar livros pessoais (título, autor(es), editora, coleção, género, ISBN), com inserção manual e/ou por leitura de ISBN via API gratuita (Open Library ou Google Books), base de dados SQLite local, GUI para desktop, funcionamento offline. Publicável no GitHub como parte do portefólio. Fase web é possibilidade futura (Docker pode entrar aí).

Claude atua como tutor sénior: explica o "porquê" de cada decisão, avança passo a passo, nunca assume conhecimento prévio, nunca assume factos sobre o ambiente sem confirmar.

## Ambiente

- **SO:** Windows
- **Python:** 3.14.6
- **Git:** 2.55.0
- **Editor:** Zed
- **Docker:** instalado, não relevante ainda (fase web futura)
- **Caminho do projeto:** `C:\Users\User\Projetos\biblioteca-pessoal`
- **Ambiente virtual:** pasta `venv/`, ativar sempre no início de cada sessão de terminal nova (reinício do PC, novo separador, etc.):
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  (Confirma-se ativo quando o prompt mostra `(venv)` no início da linha.)

## Estado atual do repositório Git

- Branch única: `main`
- Sem remoto configurado (ainda não ligado ao GitHub)
- 9 commits feitos:
  1. `8099b85` — Configuração inicial: ambiente virtual e gitignore
  2. `a09d3eb` — Adiciona main.py como teste inicial do ambiente
  3. `b5c2bfb` — Adiciona context.md para continuidade entre sessões
  4. `168f3d1` — Adiciona database.py com criação das tabelas livros, autores e livro_autor
  5. `f70e979` — Adiciona *.db ao gitignore
  6. `c5fa4b8` — Adiciona funções add_book e get_or_create_author com proteção contra ISBN duplicado
  7. `657855e` — Atualiza context.md após funções de inserção
  8. `2cc408c` — Adiciona list_books e search_books com normalização de acentos/pontuação
  9. `73d0b11` — Adiciona update_book e delete_book, fecha CRUD completo da camada de dados
- `.gitignore` cobre: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`

## Ficheiros existentes

- `.gitignore`
- `main.py` — script mínimo de teste de fumo (smoke test), só confirma que o Python corre e imprime texto. Ainda sem lógica da aplicação.
- `database.py` — módulo da base de dados SQLite. Contém:
  - `normalize_text(texto)` — normaliza texto para comparação/pesquisa insensível a acentos, maiúsculas e pontuação (NFKD + remoção de marcas de combinação + `.lower()` + remoção de pontuação via regex). Devolve `""` para `None`.
  - `connect()` — abre ligação, ativa `PRAGMA foreign_keys = ON`, define `conn.row_factory = sqlite3.Row` (linhas acedidas por índice OU por nome de coluna, convertíveis para `dict()`)
  - `create_tables()` — cria as tabelas `livros`, `autores`, `livro_autor` (schema relacional muitos-para-muitos entre livros e autores)
  - `get_or_create_author(cursor, nome)` — devolve o id de um autor existente (comparação insensível a maiúsculas via `LOWER()`) ou cria-o
  - `add_book(titulo, editora, colecao, genero, isbn, autores_str)` — insere um livro e associa-o aos autores (nomes separados por vírgula na string de entrada); captura `sqlite3.IntegrityError` e avisa em caso de ISBN duplicado, sem criar segunda entrada
  - `list_books()` — devolve todos os livros como lista de dicionários, ordenados por título, com autores agregados numa string (`GROUP_CONCAT`)
  - `search_books(termo)` — pesquisa por título, editora ou autor, usando `normalize_text` registada como função SQL (`conn.create_function`); filtragem feita numa subquery (identifica ids correspondentes) para que a query exterior agregue TODOS os autores do livro, não só o que fez match
  - `update_book(livro_id, titulo=None, editora=None, colecao=None, genero=None, isbn=None, autores_str=None)` — atualização parcial (campos `None` mantêm o valor atual); se `autores_str` for passado, substitui a lista de autores por completo; identifica o livro por `id`
  - `delete_book(livro_id)` — remove o livro e as suas associações em `livro_autor` (necessário por causa da FK); autores ficam na tabela mesmo sem livros associados (decisão deliberada)
- `biblioteca.db` — gerado localmente, não versionado (está no `.gitignore`)

## Modelo de dados (schema SQLite)

- **livros**: `id` (PK), `titulo`, `editora`, `colecao`, `genero`, `isbn` (UNIQUE)
- **autores**: `id` (PK), `nome` (UNIQUE)
- **livro_autor**: `livro_id` + `autor_id` (PK composta, FKs para as duas tabelas anteriores) — permite um livro ter vários autores e um autor ter vários livros (ex.: BD com argumentista e desenhador em coautoria)

## Testado e validado nesta sessão

- `list_books()` — confirmado que devolve dicionário (após ativar `row_factory`), com autores do livro corretamente agregados numa string.
- `normalize_text()` — testado com acentos, maiúsculas, pontuação e `None`; resultado correto em todos os casos.
- `search_books()` — **bug encontrado e corrigido durante os testes**: a primeira versão aplicava o `WHERE` diretamente sobre as linhas já unidas pelo `JOIN`, o que cortava as linhas de autores "irmãos" antes do `GROUP_CONCAT` (pesquisar "Conrad" devolvia só "Conrad", sem "Fabcaro", no mesmo livro). Corrigido movendo o `WHERE` para uma subquery que só identifica os `id`s de livros correspondentes; a query exterior volta a fazer o `JOIN` completo sem `WHERE`, agregando todos os autores do livro. Reteste confirmou o comportamento correto.
- `update_book()` — testado com atualização parcial (só ISBN), depois só autores (substituição completa da lista), e com `id` inexistente (mensagem de aviso, devolve `False`, sem lançar exceção).
- `delete_book()` — testado com `id` inexistente (`False`, sem erro) e remoção real (`True`); confirmado que os autores permanecem na tabela `autores` mesmo depois de o único livro que os continha ser removido.

## Incidente resolvido (histórico, não repetir)

A pasta do projeto continha uma pasta `.git` oculta pré-existente (não criada por nós), com um remoto (`origin`) apontando para um repositório GitHub que **nunca existiu** (confirmado 404), e ficheiros fantasma nunca escritos nesta conversa (`cli.py`, `database.py`, `gui.py`, `Dockerfile`, testes, `docs/adr/`, etc.). Miguel não reconheceu nenhum desses ficheiros como trabalho próprio. A pasta `.git` foi apagada e recriada do zero (`git init`, branch `main`). Não há necessidade de investigar isto mais — está resolvido e o histórico atual é limpo.

## Notas técnicas / decisões tomadas

- Ativação do `venv` é por sessão de terminal, não persiste entre reinícios ou novos separadores — Miguel já interiorizou esta regra.
- `database.py` usa agora `re` e `unicodedata` além de `sqlite3` — continuam a ser bibliotecas da standard library, por isso ainda não é preciso ter o `venv` ativo para correr o módulo sozinho. Isto muda assim que se instalar a primeira dependência externa (ex. GUI ou chamadas à API de ISBN).
- O Zed mostra um aviso do `basedpyright` ("print is not defined") em `main.py` porque o linter está a apontar para um Python global do registo do Windows, não para o interpretador do `venv`. É cosmético, não afeta a execução. Baixa prioridade, não corrigido.
- `conn.row_factory = sqlite3.Row` acrescentado ao `connect()` — retrocompatível com código existente que acedia a colunas por índice (`resultado[0]`), e permite `dict(linha)` nas funções de leitura.
- Duplicação de livros: ISBN continua a ser o único critério de deteção de duplicados.
- Pesquisa insensível a acentos/maiúsculas/pontuação: implementada via `normalize_text()` (NFKD + remoção de marcas de combinação + `.lower()` + regex para pontuação), registada como função SQL personalizada (`conn.create_function("normalizar", 1, normalize_text)`) para ser usada diretamente nas queries de `search_books()`.
- Autores: nomes inseridos como string única separada por vírgulas (ex. "Fabcaro, Conrad"), tanto em `add_book` como em `update_book` (quando `autores_str` é passado, substitui a lista completa — não há edição incremental de autor individual).
- `update_book` usa parâmetros opcionais (`None` = "não mexer neste campo") para permitir atualizações parciais sem ter de reconsultar e repassar todos os campos. Limitação consciente: não há forma de usar `None` para *limpar* um campo deliberadamente — não é um caso de uso necessário neste projeto.
- `delete_book` apaga primeiro as linhas em `livro_autor` (obrigatório, por causa de `PRAGMA foreign_keys = ON`) antes de apagar a linha em `livros`. Autores órfãos (sem livros associados) são mantidos deliberadamente na tabela `autores`, para não perder o registo caso o autor seja reutilizado depois.

## Próximo passo

Camada de dados (CRUD completo sobre `livros`) está funcionalmente fechada: criar, listar, pesquisar, atualizar, remover — todas testadas, incluindo casos-limite. Próximo salto grande do projeto: **GUI desktop**. Decisão ainda por tomar na próxima sessão: `tkinter` (biblioteca padrão, sem instalar nada) vs. `PySide`/`PyQt` (mais poderoso, mas dependência externa — implicaria ativar o `venv` para tudo a partir daí).

## Regras de trabalho (lembrete permanente)

- Nunca assumir nada sobre o ambiente ou ficheiros — confirmar sempre com Miguel antes de agir, especialmente antes de apagar/sobrepor ficheiros.
- Avançar em passos pequenos, um conceito de cada vez, com explicação, código comentado, forma de testar, e um exercício ou pergunta de consolidação.
- Comunicação em Português Europeu (PT-PT). Código e nomes de variáveis/funções em inglês.
- Atualizar este ficheiro sempre que se fechar um bloco de trabalho coerente (fim de fase, ou marco relevante dentro de uma fase).
- No fim de cada sessão, sugerir um título em `kebab-case` (formato `isto-vai-ser-um-titulo`) resumindo o que foi feito, para facilitar localizar sessões antigas mais tarde.

## Título desta sessão

`crud-completo-pesquisa-normalizada-update-delete`
