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
- 2 commits feitos:
  1. `8099b85` — Configuração inicial: ambiente virtual e gitignore
  2. `a09d3eb` — Adiciona main.py como teste inicial do ambiente
- `.gitignore` cobre: `venv/`, `__pycache__/`, `*.pyc`, `.env`

## Ficheiros existentes

- `.gitignore`
- `main.py` — script mínimo de teste de fumo (smoke test), só confirma que o Python corre e imprime texto. Ainda sem lógica da aplicação.

## Incidente resolvido (histórico, não repetir)

A pasta do projeto continha uma pasta `.git` oculta pré-existente (não criada por nós), com um remoto (`origin`) apontando para um repositório GitHub que **nunca existiu** (confirmado 404), e ficheiros fantasma nunca escritos nesta conversa (`cli.py`, `database.py`, `gui.py`, `Dockerfile`, testes, `docs/adr/`, etc.). Miguel não reconheceu nenhum desses ficheiros como trabalho próprio. A pasta `.git` foi apagada e recriada do zero (`git init`, branch `main`). Não há necessidade de investigar isto mais — está resolvido e o histórico atual é limpo.

## Notas técnicas / decisões tomadas

- Ativação do `venv` é por sessão de terminal, não persiste entre reinícios ou novos separadores — Miguel já interiorizou esta regra.
- O Zed mostra um aviso do `basedpyright` ("print is not defined") em `main.py` porque o linter está a apontar para um Python global do registo do Windows, não para o interpretador do `venv`. É cosmético, não afeta a execução. Não foi corrigido — baixa prioridade, resolver só se voltar a interferir de forma mais séria.
- Política de execução do PowerShell não bloqueou a ativação do `venv` neste computador (não foi preciso usar `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`), mas Claude tinha o comando pronto como contingência caso fosse preciso.

## Próximo passo

Iniciar a **modelação da base de dados** (Fase 2 do plano): desenhar a tabela de livros em SQLite — que campos, que tipos de dados, chave primária, e explicar o que é uma base de dados relacional e o módulo `sqlite3` do Python antes de escrever qualquer código.

## Regras de trabalho (lembrete permanente)

- Nunca assumir nada sobre o ambiente ou ficheiros — confirmar sempre com Miguel antes de agir, especialmente antes de apagar/sobrepor ficheiros.
- Avançar em passos pequenos, um conceito de cada vez, com explicação, código comentado, forma de testar, e um exercício ou pergunta de consolidação.
- Comunicação em Português Europeu (PT-PT). Código e nomes de variáveis/funções em inglês.
- Atualizar este ficheiro sempre que se fechar um bloco de trabalho coerente (fim de fase, ou marco relevante dentro de uma fase).
