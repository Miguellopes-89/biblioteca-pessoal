[![Testes Automáticos](https://github.com/Miguellopes-89/biblioteca-pessoal/actions/workflows/ci.yml/badge.svg)](https://github.com/Miguellopes-89/biblioteca-pessoal/actions/workflows/ci.yml)

# Biblioteca Pessoal

Aplicação local para registo e inventário da minha coleção pessoal de
livros. Nasceu da vontade simples de saber "que livros é que eu tenho,
o que já li, e o que ainda está por ler" — e tornou-se também um
projeto para aprender e documentar arquitetura de software na prática.

## Funcionalidades atuais

- Adicionar livros (título, autor, ISBN opcional, género, estado de
  leitura, nota pessoal)
- Listar todos os livros ou filtrar por estado de leitura
  (**lido** / **a ler** / **por ler**)
- Procurar por título ou autor
- Atualizar o estado de leitura de um livro
- Remover livros

## Stack técnica

- **Python 3.12** — linguagem principal
- **SQLite** — base de dados local, guardada num único ficheiro
  (`data/biblioteca.db`), sem necessidade de servidor

## Como correr

```bash
python cli.py
```

A base de dados é criada automaticamente na primeira execução.

## Estrutura do projeto

```
Biblioteca Pessoal/
├── cli.py           # Interface de linha de comandos (ponto de entrada)
├── database.py      # Acesso à base de dados: esquema e operações CRUD
├── constantes.py     # Valores fixos partilhados (géneros, estados de leitura)
└── data/
    └── biblioteca.db # Base de dados SQLite (não incluída no repositório)
```

## Roteiro de evolução

Este projeto está a ser construído de forma incremental, e o histórico
de commits reflete essa evolução:

1. **CLI (atual)** — interface de linha de comandos, foco na lógica de
   dados
2. **Interface gráfica local** — com Tkinter, mantendo tudo local
3. **Possível interface web local** — com Flask, sempre a correr
   apenas no próprio computador, sem hosting externo

## Nota

Projeto pessoal, desenvolvido com apoio do Claude (Anthropic) como
arquiteto/engenheiro, num processo colaborativo de decisão de produto
e implementação técnica.
