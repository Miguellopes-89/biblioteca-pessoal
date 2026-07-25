# CONTEXT.md — Registo de progresso do projeto Biblioteca Pessoal

> Este ficheiro é a memória entre sessões deste projeto. No início de
> cada sessão nova, deve ser consultado antes de qualquer ação. Deve
> ser atualizado no fim de alterações relevantes.

## Estado atual (última atualização: 24 de julho de 2026)

**Fase:** CLI (linha de comandos) — funcional, MVP completo.

O programa corre localmente, guarda os dados numa base de dados SQLite
e suporta as operações essenciais: adicionar, listar, filtrar por
estado de leitura, procurar, atualizar estado e remover livros.

Ainda **não foi criado o repositório Git/GitHub** — combinado
explicitamente com o utilizador: só criar o repositório quando o
projeto local estiver montado e testado.

## Decisões tomadas

| Decisão | Escolha | Porquê |
|---|---|---|
| Tipo de aplicação | Local, sem hosting externo | Simplicidade, sem custos, controlo total dos dados |
| Base de dados | SQLite | Ficheiro único, sem servidor, embutida no Python |
| Interface inicial | CLI (linha de comandos) | Ponto de partida simples para aprender a lógica antes de complicar com UI |
| Evolução planeada | CLI → Tkinter (GUI local) → possível Flask (web local) | Progressão didática, cada etapa fica documentada no histórico Git |
| Estados de leitura | `lido` / `a ler` / `por ler` | Substituiu a ideia inicial de "à espera", considerada pouco clara |
| Géneros literários | Lista fixa, definida em `constantes.py` (não em CHECK constraint da BD) | Fácil de expandir (uma linha de código) sem precisar de migração de esquema |
| Limite de notas pessoais | 160 caracteres | Definido pelo utilizador — quer notas curtas, não ensaios |
| Registo de preenchimento ISBN | A explorar as duas formas: manual e (no futuro) automática via API tipo Open Library/Google Books | Ainda não implementado — é um passo futuro, não faz parte do MVP atual |
| Editor de código do utilizador | Zed (instalado em `C:\Users\User\AppData\Local\Programs\Zed`) | Confirmado por verificação direta ao sistema |
| Géneros literários (atualização) | Adicionados "Divulgação Científica" e "Economia, Finanças e Contabilidade" | Pedido do utilizador — lista já considerada abrangente para já |
| Pesquisa (título/autor) | Insensível a maiúsculas/minúsculas **e** a acentos, feita em Python (não em SQL) via normalização Unicode (NFKD + remoção de marcas diacríticas) | Corrige falha real detetada pelo utilizador ("meditacoes" não encontrava "Meditações"). Filtrar em Python em vez de SQL é aceitável à escala de uma biblioteca pessoal |
| Gestão de sessões | Claude decide quando encerrar uma sessão de trabalho, e atualiza este ficheiro (CONTEXT.md) diretamente nesse momento, para o utilizador carregar no menu "Contexto" | Pedido explícito do utilizador — evita sessões longas (dificultam encontrar informação específica e gastam mais tokens a reler histórico) |

## Estrutura do projeto (ficheiros existentes)

```
Biblioteca Pessoal/
├── README.md         # Descrição do projeto para o GitHub
├── CONTEXT.md         # Este ficheiro
├── .gitignore         # Exclui __pycache__, data/ (dados pessoais), venv
├── constantes.py      # GENEROS, ESTADOS_LEITURA, LIMITE_NOTA
├── database.py        # Ligação SQLite + CRUD (criar_tabela, adicionar_livro,
│                       #   listar_livros, procurar_livros,
│                       #   atualizar_estado_leitura, remover_livro)
├── cli.py              # Menu interativo, ponto de entrada (`python cli.py`)
└── data/
    └── biblioteca.db   # Criada automaticamente na primeira execução (ignorada pelo Git)
```

## Esquema da base de dados (tabela `livros`)

```sql
CREATE TABLE livros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    autor TEXT NOT NULL,
    isbn TEXT,
    genero TEXT NOT NULL,
    estado_leitura TEXT NOT NULL CHECK (estado_leitura IN ('lido', 'a ler', 'por ler')),
    nota TEXT CHECK (length(nota) <= 160),
    data_adicionado TEXT DEFAULT CURRENT_TIMESTAMP
)
```

## Testado e validado

- Criação da tabela
- Inserção, listagem, pesquisa (título/autor), atualização de estado e
  remoção — testado via script manual diretamente no PC do utilizador
  (Windows, Python 3.12.10)
- Caracteres acentuados (português) confirmados a funcionar
  corretamente na base de dados. **Nota importante:** a consola do
  PowerShell por vezes mostra os acentos de forma incorreta
  (`Fic��o` em vez de `Ficção`) — isto é um problema de visualização
  da consola, não dos dados. Não é preciso "corrigir" nada se isto
  aparecer novamente; os dados armazenados estão corretos.
- Fluxo completo do menu `cli.py` testado de ponta a ponta (adicionar
  livro → listar → sair), com dados reais a passar corretamente pela
  base de dados.
- Corrigido um bug real durante os testes: o caracter “✓” nas
  mensagens de confirmação fazia o `cmd.exe` falhar em certas
  configurações de consola Windows (a mensagem não aparecia, apesar
  dos dados terem sido guardados corretamente). Substituído por
  `[OK]`, seguro em qualquer terminal.
- Confirmado pelo utilizador em uso real no terminal do Zed: adicionar
  livros funciona bem.
- Reparo do utilizador: a pesquisa por título/autor falhava sem
  acentos ("meditacoes" não encontrava "Meditações"). Corrigido — ver
  decisão na tabela acima. Validado com 8 casos de teste automatizados
  (acentos, maiúsculas, português e nomes espanhóis como "García
  Márquez"), todos a passar.

## Próximos passos

1. Utilizador usar o `cli.py` no dia a dia por algum tempo, para
   validar a experiência real e recolher fricções antes de avançar.
2. Criar o repositório Git local (`git init`), fazer o primeiro
   commit, e só depois criar o repositório remoto no GitHub e
   publicar.
3. Decidir e implementar o preenchimento automático de metadados via
   ISBN (API a escolher — Open Library é gratuita e sem necessidade de
   chave de API, Google Books é outra opção).
4. Após uso e feedback do utilizador sobre a CLI, avançar para a
   interface gráfica com Tkinter.

## Notas sobre o ambiente do utilizador

- SO: Windows
- Python 3.12.10, pip 25.0.1, Git 2.55 instalados e confirmados
- Editor: Zed
- Acesso Claude: Filesystem (pasta `C:\Users\User\Projetos`) e
  Windows-MCP (terminal e sistema completo)
