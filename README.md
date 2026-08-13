[![Testes Automáticos](https://github.com/Miguellopes-89/biblioteca-pessoal/actions/workflows/ci.yml/badge.svg)](https://github.com/Miguellopes-89/biblioteca-pessoal/actions/workflows/ci.yml)

# Biblioteca Pessoal

Aplicação local para registo e inventário da minha coleção pessoal de
livros. Nasceu da vontade simples de saber "que livros é que eu tenho,
o que já li, e o que ainda está por ler" — e tornou-se também um
projeto para aprender e documentar arquitetura de software na prática.

## Funcionalidades atuais

- Adicionar livros (título, autor, ISBN opcional, género, estado de
  leitura, nota pessoal)
- Preenchimento automático de título/autor a partir do ISBN, via API
  da Open Library — os dados são sempre mostrados para confirmação
  antes de gravar
- Listar todos os livros ou filtrar por estado de leitura
  (**lido** / **a ler** / **por ler**)
- Procurar por título ou autor, insensível a maiúsculas e a acentos
- Ordenar a lista por qualquer coluna (clicar no cabeçalho, na
  interface gráfica)
- Atualizar o estado de leitura de um livro
- Remover livros

Duas interfaces disponíveis, com a mesma lógica de dados por baixo:

- **CLI** (`cli.py`) — linha de comandos
- **GUI** (`gui.py`) — interface gráfica com Tkinter

## Stack técnica

- **Python 3.12** — linguagem principal
- **SQLite** — base de dados local, num único ficheiro
  (`data/biblioteca.db`), sem necessidade de servidor
- **Tkinter/ttk** — interface gráfica, incluída na biblioteca padrão
- **requests** — chamadas à API da Open Library
- **Docker** — empacotamento para correr sem Python instalado no host
- **GitHub Actions** — integração contínua (build + smoke test a cada push)

## Como correr

### Localmente

python cli.py


ou

python gui.py


A base de dados é criada automaticamente na primeira execução.

### Com Docker

docker compose up


## Estrutura do projeto

Biblioteca Pessoal/
├── cli.py # Interface de linha de comandos
├── gui.py # Interface gráfica (Tkinter)
├── database.py # Acesso à base de dados: esquema e operações CRUD
├── metadados_isbn.py # Pesquisa de título/autor por ISBN (Open Library)
├── constantes.py # Valores fixos partilhados (géneros, estados de leitura)
├── requirements.txt # Dependências externas
├── Dockerfile
├── docker-compose.yml
├── .github/workflows/ # Pipeline de CI
└── data/
└── biblioteca.db # Base de dados SQLite (não incluída no repositório)


## Roteiro de evolução

Este projeto está a ser construído de forma incremental, e o histórico
de commits reflete essa evolução:

1. ~~CLI~~ — feito
2. ~~Interface gráfica local (Tkinter)~~ — feito
3. ~~Empacotamento com Docker e CI~~ — feito
4. Refatorização do modelo de domínio (em avaliação)
5. **Possível interface web local** — com Flask, sempre a correr
   apenas no próprio computador, sem hosting externo

## Nota

Projeto pessoal, desenvolvido com apoio do Claude (Anthropic) como
arquiteto/engenheiro, num processo colaborativo de decisão de produto
e implementação técnica.
