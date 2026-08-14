# CONTEXT.md — Registo de progresso do projeto Biblioteca Pessoal

> Este ficheiro é a memória entre sessões deste projeto. No início de
> cada sessão nova, deve ser consultado antes de qualquer ação. Deve
> ser atualizado no fim de alterações relevantes.
>
> **Gestão de sessões:** é responsabilidade do Claude (ou de outro
> modelo a dar continuidade a este projeto) monitorizar a duração e
> complexidade da sessão em curso. Quando a sessão começar a ficar
> longa — muitas trocas, muitos ficheiros discutidos, tópicos
> variados — o modelo deve avisar proativamente que é boa altura para
> encerrar, apresentar a atualização deste ficheiro, e sugerir
> continuar numa sessão nova. Isto evita esgotar tokens a meio de uma
> tarefa e reduz o risco de alucinações que tende a aumentar em
> sessões muito longas. Não esperar que o utilizador peça — propor.

## Estado atual (última atualização: 14 de agosto de 2026)

**Fase:** MVP maduro. CLI e GUI (Tkinter) com paridade total de
funcionalidades, preenchimento automático via ISBN, Docker,
CI funcional com testes reais (`pytest`), e primeira decisão de
arquitetura documentada formalmente (ADR-001).

O programa corre localmente, guarda os dados numa base de dados SQLite
e suporta as operações essenciais: adicionar, listar, filtrar por
estado de leitura, procurar, atualizar estado e remover livros.

Repositório público no GitHub:
https://github.com/Miguellopes-89/biblioteca-pessoal

## Decisões tomadas

| Decisão | Escolha | Porquê |
|---|---|---|
| Tipo de aplicação | Local, sem hosting externo | Simplicidade, sem custos, controlo total dos dados |
| Base de dados | SQLite | Ficheiro único, sem servidor, embutida no Python |
| Interface inicial | CLI (linha de comandos) | Ponto de partida simples para aprender a lógica antes de complicar com UI |
| Evolução planeada | CLI → Tkinter (GUI local) → Docker + CI → possível Flask (web local) | Progressão didática, cada etapa fica documentada no histórico Git |
| Estados de leitura | `lido` / `a ler` / `por ler` | Substituiu a ideia inicial de "à espera", considerada pouco clara |
| Géneros literários | Lista fixa, definida em `constantes.py` (não em CHECK constraint da BD) | Fácil de expandir sem precisar de migração de esquema |
| Limite de notas pessoais | 160 caracteres | Definido pelo utilizador — quer notas curtas, não ensaios |
| Preenchimento automático via ISBN | API da Open Library (gratuita, sem chave) | Sem custos nem burocracia; `metadados_isbn.py` isolado propositadamente para facilitar troca de fornecedor |
| Fluxo de confirmação do ISBN | Dados mostrados ao utilizador, que aceita (Enter) ou corrige — nunca grava automaticamente | Evita erros silenciosos com dados de edições erradas |
| Interface gráfica: biblioteca de widgets | Tkinter + ttk | Zero dependências novas; aspeto mais moderno que Tkinter puro |
| Interface gráfica: alcance da primeira versão | Paridade total com a CLI logo na primeira entrega | Lógica de dados já testada via CLI; GUI é só nova camada de apresentação |
| Pesquisa (título/autor) | Insensível a maiúsculas/minúsculas e a acentos, via normalização Unicode (NFKD) em Python, não em SQL | Corrige falha real detetada pelo utilizador; aceitável em performance à escala de biblioteca pessoal |
| **Modelo de dados: manter simples (sem Obra/Edição/Exemplar/Autor N:N)** | **Decisão registada em `docs/adr/001-modelo-de-dados-simples.md`** | **Nenhum dos cenários que justificaria a complexidade (edições diferentes, formatos duplicados, localização física) se aplica à biblioteca real do utilizador — confirmado diretamente, não assumido** |
| Cenário "multi-utilizador" futuro | Não tratado como requisito atual; mencionado no ADR-001 como possibilidade a avaliar separadamente no futuro, com o seu próprio ADR | Implicaria autenticação, isolamento de dados e possivelmente sair de SQLite ficheiro-único — âmbito muito maior do que o modelo de dados, não deve influenciar decisões de hoje |
| Refatorização hexagonal (domain/application/infrastructure/presentation) proposta por revisão externa | Rejeitada por agora | Com o modelo de dados simples mantido, 4 camadas para um CRUD é cerimónia sem retorno; esforço redirecionado para testes e documentação de decisões |
| Testes automatizados | `pytest`, com base de dados temporária isolada por teste (`tmp_path` + `monkeypatch`), chamadas de rede simuladas em `metadados_isbn.py` | Testes reais em vez do smoke test que existia antes; corrige a distância entre o badge de CI e a cobertura real |
| CI (`ci.yml`) | Corre `python -m pytest -v` + smoke test da CLI a cada push | `python -m pytest` evita problemas de PATH que já ocorreram localmente no Windows do utilizador |
| README — secção "Nota" | Reformulada para deixar claro que as decisões de produto são do utilizador e o Claude é parceiro de implementação; sem mencionar ferramentas de IA específicas (ChatGPT/DeepSeek) | Foco no que interessa a um entrevistador: capacidade de decisão e supervisão técnica, não a lista de ferramentas usadas |
| `relatorio-deepseek.md` | Mantido só localmente (não versionado); conteúdo relevante absorvido neste ficheiro | Já cumpriu a função — a decisão pendente que continha está resolvida |
| Gestão de sessões | Claude monitoriza a duração/complexidade da sessão e propõe proativamente encerrar e atualizar este ficheiro, em vez de esperar pedido do utilizador | Pedido explícito do utilizador (14 de agosto de 2026) — poupa tokens e reduz risco de alucinação em sessões longas |

## Estrutura do projeto (ficheiros existentes)

biblioteca-pessoal/
├── README.md # Descrição do projeto para o GitHub
├── CONTEXT.md # Este ficheiro
├── .gitignore
├── constantes.py # GENEROS, ESTADOS_LEITURA, LIMITE_NOTA
├── database.py # Ligação SQLite + CRUD + normalizar_texto
├── metadados_isbn.py # Pesquisa de título/autor por ISBN via Open Library
├── requirements.txt # Dependências de produção (requests)
├── requirements-dev.txt # Dependências de desenvolvimento (pytest)
├── cli.py # Menu interativo, ponto de entrada (python cli.py)
├── gui.py # Interface gráfica Tkinter (python gui.py)
├── Dockerfile
├── docker-compose.yml
├── docs/
│ └── adr/
│ └── 001-modelo-de-dados-simples.md
├── tests/
│ ├── conftest.py # Fixture bd_temporaria (isolamento por teste)
│ ├── test_database.py # 22 testes
│ └── test_metadados_isbn.py # 13 testes
├── .github/workflows/
│ └── ci.yml
└── data/
└── biblioteca.db # Criada automaticamente na primeira execução (ignorada pelo Git)


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

- CRUD completo, pesquisa insensível a acentos, preenchimento por ISBN
  (válido, inexistente, vazio) — todos testados manualmente em sessões
  anteriores (ver histórico Git para detalhe).
- Interface gráfica testada interativamente: lista, ordenação por
  coluna, janela modal de adicionar livro.
- **Suite `pytest` (35 testes) — todos a passar**, cobrindo:
  - CRUD e regras de negócio de `database.py`, incluindo as `CHECK
    constraints` da base de dados testadas diretamente por SQL (não
    só via `adicionar_livro()`), confirmando que protegem os dados
    mesmo por fora da camada Python.
  - `normalizar_texto()` parametrizado (acentos portugueses e
    espanhóis).
  - `metadados_isbn.py` com chamadas de rede simuladas
    (`monkeypatch`): encontrado com/sem autor, vários autores, não
    encontrado, ISBN vazio (confirma que não faz pedido de rede),
    timeout, erro de ligação, erro HTTP.
- **CI verde no GitHub Actions**, a correr `python -m pytest -v` +
  smoke test da CLI a cada push (workflow "Testes Automáticos").
- ADR-001 escrito e commitado, documentando a decisão de manter o
  modelo de dados simples.
- README reescrito para refletir o estado real do projeto (GUI,
  ISBN, Docker, CI, pytest) — corrigidos também erros de formatação
  Markdown (blocos de código sem vedação, secção duplicada) antes do
  commit final.

## Próximos passos

1. Utilizador usar a interface gráfica (`gui.py`) no dia a dia e
   trazer fricções reais.
2. Possível índice em `docs/adr/README.md` — só compensa quando
   existir um ADR-002.
3. Interface web local com Flask — mencionada desde o início como
   fase eventual, sem urgência nem gatilho concreto ainda.
4. Nada bloqueado neste momento — todas as decisões pendentes da
   sessão do relatório externo (13 de agosto de 2026) foram
   resolvidas.

## Notas sobre o ambiente do utilizador

- SO: Windows. Nome real da pasta do projeto:
  `C:\Users\User\Projetos\biblioteca-pessoal` (minúsculas, com
  hífen — corrigir se aparecer escrito de outra forma em registos
  antigos).
- **Python ativo no sistema:** `pythoncore-3.14-64`
  (`C:\Users\User\AppData\Local\Python\pythoncore-3.14-64`). Pacotes
  instalados com `pip install` vão para os `Scripts` desta instalação,
  que **não está no PATH** — por isso executáveis como `pytest.exe`
  não são reconhecidos diretamente na consola. Solução estável:
  invocar sempre via `python -m <ferramenta>` (ex.: `python -m
  pytest -v`) em vez do executável direto. Confirmado a funcionar.
- Múltiplas instalações de Python coexistem no sistema (histórico:
  3.12 original, 3.14 standalone, 3.14 via WindowsApps) — a ativa no
  PATH pode mudar após reinícios. Se aparecer `ModuleNotFoundError`
  inesperado, confirmar com `python --version` e `where.exe python`.
- Editor: Zed.
- Git 2.55 instalado. `gh` CLI autenticado.
- **Acesso do Claude nesta sessão:** apenas chat — sem Filesystem
  nem Windows-MCP ligados. Todo o trabalho foi feito por cópia manual
  de conteúdo (Claude fornece ficheiros/comandos, utilizador aplica e
  cola resultados de volta). Se numa sessão futura os conectores
  Filesystem/Windows-MCP estiverem disponíveis, preferir usá-los
  diretamente em vez deste fluxo manual.
- **Instabilidade histórica do Windows-MCP** (quando ligado):
  `Stop-Process -Force` em `python.exe` já causou o servidor a ficar
  sem resposta (~4 min) — preferir fechar janelas de teste
  manualmente. Recuperação: fechar a Claude Desktop por completo via
  Gestor de Tarefas e reabrir.
