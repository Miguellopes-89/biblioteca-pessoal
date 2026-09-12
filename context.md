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
- 6 commits feitos:
  1. `8099b85` — Configuração inicial: ambiente virtual e gitignore
  2. `a09d3eb` — Adiciona main.py como teste inicial do ambiente
  3. `b5c2bfb` — Adiciona context.md para continuidade entre sessões
  4. `168f3d1` — Adiciona database.py com criação das tabelas livros, autores e livro_autor
  5. `f70e979` — Adiciona *.db ao gitignore
  6. `c5fa4b8` — Adiciona funções add_book e get_or_create_author com proteção contra ISBN duplicado
- `.gitignore` cobre: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`

## Ficheiros existentes

- `.gitignore`
- `main.py` — script mínimo de teste de fumo (smoke test), só confirma que o Python corre e imprime texto. Ainda sem lógica da aplicação.
- `database.py` — módulo da base de dados SQLite. Contém:
  - `connect()` — abre ligação e ativa `PRAGMA foreign_keys = ON`
  - `create_tables()` — cria as tabelas `livros`, `autores`, `livro_autor` (schema relacional muitos-para-muitos entre livros e autores)
  - `get_or_create_author(cursor, nome)` — devolve o id de um autor existente (comparação insensível a maiúsculas via `LOWER()`) ou cria-o
  - `add_book(titulo, editora, colecao, genero, isbn, autores_str)` — insere um livro e associa-o aos autores (nomes separados por vírgula na string de entrada); captura `sqlite3.IntegrityError` e avisa em caso de ISBN duplicado, sem criar segunda entrada
- `biblioteca.db` — gerado localmente por `create_tables()`, não versionado (está no `.gitignore`)

## Modelo de dados (schema SQLite)

- **livros**: `id` (PK), `titulo`, `editora`, `colecao`, `genero`, `isbn` (UNIQUE)
- **autores**: `id` (PK), `nome` (UNIQUE)
- **livro_autor**: `livro_id` + `autor_id` (PK composta, FKs para as duas tabelas anteriores) — permite um livro ter vários autores e um autor ter vários livros (ex.: BD com argumentista e desenhador em coautoria)

## Testado e validado nesta sessão

- Inserção de um livro com dois autores (Astérix e o Grifo — Fabcaro + Conrad): confirmado que ficaram 1 linha em `livros`, 2 linhas em `autores`, 2 linhas em `livro_autor` ligando o mesmo `livro_id` aos dois `autor_id`.
- Proteção contra ISBN duplicado: reinserir o mesmo livro (mesmo ISBN) não cria segunda entrada, mostra mensagem de aviso e a função devolve `None`.
- Comparação de autores insensível a maiúsculas (`LOWER()`) implementada e por trás do `get_or_create_author`, para evitar duplicar o mesmo autor por diferenças de capitalização (ex. "Fabcaro" vs "fabcaro").

## Incidente resolvido (histórico, não repetir)

A pasta do projeto continha uma pasta `.git` oculta pré-existente (não criada por nós), com um remoto (`origin`) apontando para um repositório GitHub que **nunca existiu** (confirmado 404), e ficheiros fantasma nunca escritos nesta conversa (`cli.py`, `database.py`, `gui.py`, `Dockerfile`, testes, `docs/adr/`, etc.). Miguel não reconheceu nenhum desses ficheiros como trabalho próprio. A pasta `.git` foi apagada e recriada do zero (`git init`, branch `main`). Não há necessidade de investigar isto mais — está resolvido e o histórico atual é limpo.

## Notas técnicas / decisões tomadas

- Ativação do `venv` é por sessão de terminal, não persiste entre reinícios ou novos separadores — Miguel já interiorizou esta regra. Nota: `database.py` só usa a biblioteca padrão (`sqlite3`), por isso correr sem `venv` ativo não causa erro por agora — isto muda assim que se instalar a primeira dependência externa (ex. para a GUI ou chamadas à API de ISBN).
- O Zed mostra um aviso do `basedpyright` ("print is not defined") em `main.py` porque o linter está a apontar para um Python global do registo do Windows, não para o interpretador do `venv`. É cosmético, não afeta a execução. Não foi corrigido — baixa prioridade, resolver só se voltar a interferir de forma mais séria.
- Política de execução do PowerShell não bloqueou a ativação do `venv` neste computador (não foi preciso usar `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`), mas Claude tinha o comando pronto como contingência caso fosse preciso.
- Duplicação de livros: decidido que o ISBN é o único critério de deteção de duplicados (cada edição tem o seu próprio ISBN, por isso títulos semelhantes com ISBNs diferentes são livros legitimamente distintos). Aviso "soft" por título semelhante (sem correspondência de ISBN) foi discutido e adiado para a fase de construção da lógica de inserção na GUI — não implementado ainda.
- Pesquisa insensível a acentos/maiúsculas/pontuação: decidido usar a "rota 1" — normalizar strings em Python (`unicodedata` + `.lower()`) no momento da pesquisa, sem alterar o schema nem guardar colunas normalizadas na BD. Ainda não implementado — fica para a fase de pesquisa.
- Autores: nomes inseridos como string única separada por vírgulas (ex. "Fabcaro, Conrad"), não como prompts individuais — decisão consciente de Miguel para evitar fricção no fluxo de inserção, já que multi-autoria é caso raro na sua biblioteca.

## Próximo passo

Continuar a Fase de manipulação de dados: escrever funções de **leitura/pesquisa** (listar todos os livros, pesquisar por título/autor/editora) e, mais tarde, funções de atualização e remoção. A normalização de pesquisa (rota 1, acentos/maiúsculas) deve ser implementada nesta fase.

## Regras de trabalho (lembrete permanente)

- Nunca assumir nada sobre o ambiente ou ficheiros — confirmar sempre com Miguel antes de agir, especialmente antes de apagar/sobrepor ficheiros.
- Avançar em passos pequenos, um conceito de cada vez, com explicação, código comentado, forma de testar, e um exercício ou pergunta de consolidação.
- Comunicação em Português Europeu (PT-PT). Código e nomes de variáveis/funções em inglês.
- Atualizar este ficheiro sempre que se fechar um bloco de trabalho coerente (fim de fase, ou marco relevante dentro de uma fase).
- No fim de cada sessão, sugerir um título em `kebab-case` (formato `isto-vai-ser-um-titulo`) resumindo o que foi feito, para facilitar localizar sessões antigas mais tarde.

## Título desta sessão

`funcoes-insercao-livros-autores`
