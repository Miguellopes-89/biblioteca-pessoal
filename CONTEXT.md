# CONTEXT.md — Registo de progresso do projeto Biblioteca Pessoal

> Este ficheiro é a memória entre sessões deste projeto. No início de
> cada sessão nova, deve ser consultado antes de qualquer ação. Deve
> ser atualizado no fim de alterações relevantes.

## Estado atual (última atualização: 31 de julho de 2026)

**Fase:** Interface gráfica (Tkinter) implementada com paridade total
de funcionalidades face à CLI, testada e a funcionar. Repositório
Git/GitHub criado e publicado. Preenchimento automático de metadados
via ISBN implementado em ambas as interfaces.

O programa corre localmente, guarda os dados numa base de dados SQLite
e suporta as operações essenciais: adicionar, listar, filtrar por
estado de leitura, procurar, atualizar estado e remover livros.

Repositório local criado (`git init`) com o primeiro commit feito
(hash `98cff42`), e publicado no GitHub como repositório público:
https://github.com/Miguellopes-89/biblioteca-pessoal — via `gh repo
create --source=. --remote=origin --push`. `origin/master` sincronizado
com o `master` local.

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
| Preenchimento automático via ISBN | Implementado com a API da Open Library (gratuita, sem chave) | Sem custos, sem burocracia de registo; qualidade de dados suficiente para uso pessoal. Google Books fica como alternativa se a cobertura da Open Library se revelar insuficiente — o módulo `metadados_isbn.py` foi isolado propositadamente para facilitar a troca |
| Dependência externa `requests` | Adicionada (primeira dependência externa do projeto), registada em `requirements.txt` | Alternativa era `urllib.request` da biblioteca padrão (zero dependências), mas o código de tratamento de erros de rede fica bem mais limpo com `requests` |
| Fluxo de confirmação do ISBN | Dados da API mostrados ao utilizador, que pode aceitar (Enter) ou corrigir antes de gravar — nunca grava automaticamente sem confirmação | Evita erros silenciosos se a Open Library devolver dados incorretos ou de uma edição diferente do livro |
| Género na pesquisa por ISBN | Continua sempre a ser escolhido manualmente pelo utilizador, nunca vem da API | A API não tem um conceito de género que corresponda de forma fiável à lista fixa em `constantes.py` |
| Interface gráfica: biblioteca de widgets | Tkinter + ttk (widgets modernizados), ambos incluídos no Python | Zero dependências novas; ttk dá um aspeto menos "anos 90" que o Tkinter puro, alinhado com a preferência por design minimalista |
| Interface gráfica: alcance da primeira versão | Paridade total de funcionalidades com a CLI já na primeira entrega (listar, procurar, filtrar por estado, adicionar com ISBN, atualizar estado, remover), em vez de crescer aos poucos | Toda a lógica de dados já estava testada via CLI; a GUI é só uma camada de apresentação nova sobre código já fiável, o que reduz o risco de entregar tudo de uma vez |
| Ordenação por coluna na tabela da GUI | Clicar no cabeçalho ordena pela coluna (ascendente/descendente ao clicar outra vez), com seta ▲/▼ a indicar a coluna ativa; a ordenação não é guardada entre atualizações da lista (pesquisa/filtro/adicionar/remover repõe a ordem por título) | Pedido do utilizador. Ordena as linhas já carregadas em memória (não volta a consultar a base de dados), usando a mesma normalização de texto (insensível a acentos) da pesquisa, para consistência |
| `gui.py` não mexe em `database.py`, `metadados_isbn.py` nem `cli.py` | Reutiliza tudo tal como está | Mesma separação de responsabilidades já usada entre `cli.py` e o resto; `cli.py` continua a funcionar normalmente como alternativa à GUI |
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
├── metadados_isbn.py  # Pesquisa de título/autor por ISBN via API da Open Library
├── requirements.txt   # Dependências externas (atualmente só `requests`)
├── cli.py              # Menu interativo, ponto de entrada (`python cli.py`)
├── gui.py              # Interface gráfica Tkinter, ponto de entrada (`python gui.py`)
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
- Preenchimento automático via ISBN (`metadados_isbn.py`) testado com:
  ISBN válido com e sem hífens (normalização confirmada), ISBN
  inexistente (devolve `None` corretamente, sem rebentar), e string
  vazia (idem). Testado também o fluxo completo via `cli.py`: adicionar
  livro com ISBN real, aceitar título/autor sugeridos com Enter, e
  confirmar que o livro fica gravado corretamente na base de dados
  (livro de teste removido no final, para não poluir a biblioteca real
  do utilizador).
- Interface gráfica (`gui.py`) testada interativamente (janela real,
  cliques reais, não só leitura de código): lista principal carrega
  corretamente os livros existentes; ordenação por coluna testada no
  cabeçalho "Título" (ascendente, depois descendente ao clicar outra
  vez) e ao mudar para a coluna "Autor" (reordena e move a seta ▲/▼
  para a nova coluna, como esperado); abrir a janela modal "Adicionar
  Livro" testado com sucesso.

## Próximos passos

1. Utilizador usar a interface gráfica (`gui.py`) no dia a dia — a CLI
   (`cli.py`) continua disponível e funcional em paralelo — e trazer
   fricções reais: campos confusos, falta de atalhos, comportamento
   inesperado.
2. Nada mais planeado por agora além de responder ao feedback do uso
   real. Uma possível interface web local com Flask ficou mencionada
   desde o início como fase eventual, mas sem urgência.

~~Criar o repositório Git local e publicar no GitHub~~ — feito a 25
de julho de 2026 (ver "Estado atual" acima).
~~Implementar preenchimento automático de metadados via ISBN~~ — feito
a 26 de julho de 2026, com a API da Open Library.
~~Avançar para a interface gráfica com Tkinter~~ — feito a 31 de julho
de 2026, com paridade total de funcionalidades face à CLI, incluindo
ordenação por coluna.

## Notas sobre o ambiente do utilizador

- SO: Windows
- **Atenção — versão do Python mudou:** o `python` no PATH deixou de
  apontar para a instalação original (Python 3.12.10) e passou a
  resolver para uma instalação diferente, **Python 3.14.6** (via alias
  de aplicação do WindowsApps), aparentemente como efeito colateral de
  reinstalações/reinício do sistema feitas a 31 de julho de 2026 para
  resolver um problema de ligação do Windows-MCP (ver abaixo). Isto já
  causou um bug real: o `requests` (instalado na instalação antiga) não
  existia na nova, e o `gui.py` rebentava ao arrancar com
  `ModuleNotFoundError`. Reinstalado o `requests` na instalação atual
  (3.14.6) e confirmado que tudo volta a funcionar. Não se sabe ao
  certo qual das várias instalações de Python presentes no sistema
  (3.11, 3.14 standalone, 3.14 via WindowsApps, o Python gerido pelo
  `uv`) vai estar ativa da próxima vez — se aparecer outro
  `ModuleNotFoundError` inesperado, começar por confirmar com
  `python --version` e `where.exe python`.
- Git 2.55 instalado e confirmado
- Editor: Zed
- Acesso Claude: Filesystem (pasta `C:\Users\User\Projetos`, e desde
  31 de julho de 2026 também `C:\` na íntegra) e Windows-MCP (terminal
  e sistema completo)
- **Instabilidade conhecida do Windows-MCP:** o conector já ficou sem
  resposta várias vezes durante sessões de trabalho (erro "tool not
  found" ou timeout de 4 minutos). A causa original identificada foi
  `uv` (usado para lançar o servidor) não estar no PATH do sistema —
  resolvido com a reinstalação do conector. Ficou também um padrão
  suspeito por confirmar: nas duas vezes em que o servidor ficou
  travado a meio de uma sessão, tinha acontecido logo a seguir a um
  comando `Stop-Process -Force` a terminar processos `python` — pode
  ser coincidência, mas vale a pena evitar essa combinação e, em vez
  disso, fechar janelas de teste manualmente (clicar no X) quando
  possível. Quando a ligação trava, o procedimento que resultou foi
  sempre: fechar a Claude Desktop por completo (confirmar no Gestor de
  Tarefas que não sobra nenhum `claude.exe`) e reabrir.
