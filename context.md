# context.md — Biblioteca Pessoal

> Este ficheiro é o "estado da sessão" do projeto. Cola o conteúdo no início de uma nova conversa com o Claude para retomar exatamente onde ficámos, sem reexplicar nada.

## Sobre o projeto

Aplicação desktop em Python para catalogar livros pessoais (título, autor(es), editora, coleção, género, ISBN, estado de leitura), com inserção manual e/ou por leitura de ISBN via APIs gratuitas (Google Books + Open Library, em cascata) — **implementado nesta sessão** —, base de dados SQLite local, GUI desktop em PySide6, funcionamento offline. **Publicado no GitHub** como parte do portefólio: https://github.com/Miguellopes-89/biblioteca-pessoal (repositório público). Fase web é possibilidade futura (Docker pode entrar aí).

Claude atua como tutor sénior: explica o "porquê" de cada decisão, avança passo a passo, nunca assume conhecimento prévio, nunca assume factos sobre o ambiente sem confirmar.

## Ambiente

- **SO:** Windows
- **Python:** 3.14.6
- **Git:** 2.55.0
- **GitHub CLI (`gh`):** 2.96.0, autenticado como `Miguellopes-89` (scopes: gist, read:org, repo, workflow)
- **Editor:** Zed
- **Docker:** instalado, não relevante ainda (fase web futura)
- **Caminho do projeto:** `C:\Users\User\Projetos\biblioteca-pessoal`
- **Ambiente virtual:** pasta `venv/`, ativar sempre no início de cada sessão de terminal nova:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Dependências externas instaladas:** `PySide6` 6.11.2. `requests` 2.34.2 também está instalado no `venv`, mas **já não é usado** (ver secção "Incidentes" — foi substituído por `urllib.request` da standard library). Pode ser desinstalado (`pip uninstall requests`) sem afetar nada; não é urgente.
- **`pyrightconfig.json`** criado na raiz do projeto (`{"venvPath": ".", "venv": "venv"}`) para o linter do Zed (`basedpyright`) apontar para o interpretador do `venv` em vez do Python global do Windows. Resolveu os falsos erros de importação do PySide6.

## Estado atual do repositório Git

- Branch única: `main`
- **Remoto configurado:** `origin` → `https://github.com/Miguellopes-89/biblioteca-pessoal.git` (público)
- Working tree limpa, tudo commitado e sincronizado com o GitHub no fim desta sessão
- `.gitignore` cobre: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`
- **12 commits no total.** Os 3 feitos nesta sessão:
  - `Adiciona lookup de ISBN via Google Books/Open Library com QThread`
  - `Redimensiona colunas da tabela automaticamente (ID encolhe, Titulo estica)`
  - (commit implícito do `gh repo create --push`, que enviou o histórico completo para o GitHub)

## Ficheiros existentes

- `.gitignore`
- `main.py` — smoke test original, sem lógica da aplicação. Não usado pela GUI.
- `pyrightconfig.json`
- `database.py` — módulo da base de dados SQLite. Sem alterações nesta sessão. Expõe: `normalize_text`, `connect`, `create_tables`, `get_or_create_author`, `add_book`, `list_books`, `search_books`, `update_book`, `delete_book`.
- `isbn_lookup.py` — **novo nesta sessão**. Módulo de consulta de metadados por ISBN, sem qualquer dependência do PySide6 (testável isoladamente no terminal). Contém:
  - `_pedir_json(url)` — GET genérico com `urllib.request`, `User-Agent` próprio, e **retry automático** (`TENTATIVAS = 3`, 1s de pausa entre tentativas) para lidar com falhas de rede intermitentes detetadas nesta máquina (ver "Incidentes").
  - `_fetch_google_books(isbn)` / `_fetch_open_library(isbn)` — uma função por fonte, cada uma devolve um dict normalizado (`titulo`, `autores_str`, `editora`, `genero`) ou `None`.
  - `lookup_isbn(isbn)` — função pública, cascata: tenta Google Books primeiro, só tenta Open Library se a primeira não encontrar nada. **Não funde campos das duas fontes** (decisão deliberada — evita inconsistências).
  - Nenhuma das duas APIs expõe de forma fiável um campo "coleção" (série) — esse campo continua sempre a preenchimento manual.
- `gui.py` — Interface desktop em PySide6 (`QMainWindow`). Alterações nesta sessão:
  - **`PesquisaISBNThread(QThread)`** — nova classe, corre `lookup_isbn()` em thread separada, emite `resultado_pronto` (Signal) com o dict (ou `None`) no fim. A instância fica guardada em `self.thread_pesquisa_isbn` (atributo da instância, não variável local) para não ser recolhida pelo garbage collector a meio da execução.
  - Botão **"Procurar"** ao lado do campo ISBN → `pesquisar_isbn()` lança o thread (com proteção contra duplo-clique via `isRunning()`), desativa o botão e muda o texto para "A procurar..." enquanto espera.
  - `ao_receber_resultado_isbn(resultado)` — slot ligado ao `resultado_pronto`; reativa o botão; se `None`, mostra aviso "Não encontrado"; caso contrário preenche Título/Autores/Editora/Género (só os campos que a API devolveu com conteúdo, não sobrescreve Coleção nem Estado de leitura).
  - **Colunas da tabela agora redimensionam automaticamente**: coluna ID em `ResizeToContents` (fica sempre estreita), coluna Título em `Stretch` (ocupa o espaço sobrante), restantes em `ResizeToContents`. Resolve o corte da coluna "Estado" em janelas estreitas.
- `biblioteca.db` — gerado localmente, não versionado. Contém atualmente 4 livros de teste (os 3 anteriores + "Clean Code", adicionado via lookup de ISBN nesta sessão).

## Modelo de dados (schema SQLite)

- **livros**: `id` (PK), `titulo`, `editora`, `colecao`, `genero`, `isbn` (UNIQUE), `estado_leitura` (NOT NULL, DEFAULT 'não lido')
- **autores**: `id` (PK), `nome` (UNIQUE)
- **livro_autor**: `livro_id` + `autor_id` (PK composta, FKs) — permite um livro ter vários autores e um autor ter vários livros

## Testado e validado nesta sessão

- `isbn_lookup.py` testado isoladamente no terminal (sem GUI) com ISBN real (Clean Code, 9780132350884) — sucesso via Open Library depois do retry.
- Lookup via GUI: botão "Procurar" com ISBN válido → campos preenchidos automaticamente, janela manteve-se responsiva durante a chamada de rede (thread a funcionar corretamente).
- ISBN inexistente (`0000000000000`) → aviso "Não encontrado", sem crash.
- Duplo-clique no botão "Procurar" → não lança pesquisas em paralelo.
- Livro obtido por lookup guardado com sucesso via "Adicionar Livro" (campos Coleção/Género preenchidos manualmente a seguir, como esperado — a API não os fornece de forma fiável).
- Redimensionamento da janela — colunas ajustam-se corretamente, "Estado" deixou de ficar cortada.
- `gh repo create --push` — repositório criado, código enviado, `git status` confirma sincronização completa com o `origin`.

## Incidentes resolvidos nesta sessão (histórico, não repetir)

1. **Google Books API sem chave devolve HTTP 429 (quota excedida)** — quota global partilhada por todos os utilizadores anónimos do mundo, esgotada com frequência. Não é um bug nosso; por isso o fallback para Open Library é essencial, não apenas "bónus".
2. **Biblioteca `requests` (via `urllib3`) com ligações recusadas/resetadas pela Open Library nesta máquina**, mesmo com `User-Agent` customizado — `ConnectionResetError` (WinError 10054). `urllib.request` (standard library) e `Invoke-WebRequest` do PowerShell não tinham o mesmo problema. Diagnóstico: `Get-MpComputerStatus` confirmou o **Network Inspection System (NIS)** do Windows Defender ativo — o componente de inspeção profunda de pacotes, conhecido por interferir ocasionalmente com TLS de processos "não-browser". Solução aplicada: `isbn_lookup.py` usa só `urllib.request` (remove também uma dependência externa do projeto) **e** implementa retry automático (`TENTATIVAS = 3`), porque mesmo com `urllib` a falha continuou a acontecer de forma intermitente (não é 100% resolvida pela troca de biblioteca — é mesmo o sistema a interferir às vezes). Não se tentou desativar proteções de segurança — o retry é a resposta correta a nível de aplicação, e seria a prática certa de qualquer forma (redes reais falham).

## Notas técnicas / decisões tomadas

- **Cascata de APIs, não fusão de campos:** Google Books primeiro (melhor qualidade média), Open Library só como reserva se a primeira não encontrar nada. Fundir campos das duas fontes foi considerado e rejeitado — complexidade desproporcional ao ganho, risco de dados inconsistentes.
- **`urllib.request` em vez de `requests`:** decisão pragmática pós-diagnóstico (ver "Incidentes"), com o benefício adicional de zero dependências externas para este módulo.
- **Retry com backoff simples (não exponencial):** 3 tentativas, 1s de pausa fixa entre elas. Suficiente para o nível de instabilidade observado; não se justificou complexidade adicional (backoff exponencial, jitter) para este caso de uso.
- **`QThread` para a chamada de rede:** decisão consciente para não bloquear a GUI durante o lookup (pode demorar vários segundos, sobretudo com os retries). A referência ao thread é guardada num atributo da instância (`self.thread_pesquisa_isbn`) — nunca numa variável local, que seria recolhida pelo garbage collector a meio da execução e rebentaria a app.
- **Preenchimento seletivo dos campos após lookup:** só os campos que a API devolveu com conteúdo são escritos no formulário; Coleção e Estado de leitura nunca são tocados pelo lookup (a API não os fornece).
- Escolha de biblioteca de GUI: **PySide6** (não `tkinter`) — decisão consciente para portefólio.
- Todas as decisões anteriores sobre o modelo de dados (ISBN como chave de duplicado, `LOWER()` para autores, autores em string separada por vírgulas, normalização de pesquisa via `unicodedata`, autores órfãos mantidos após remover livro) continuam válidas e inalteradas.
- **Repositório GitHub público**, com descrição em inglês (maior alcance junto de recrutadores de tecnologia), mencionando deliberadamente que o projeto foi feito no contexto de mudança de carreira — enquadrado como sinal de iniciativa.

## Próximo passo

As três prioridades da sessão anterior estão todas fechadas: lookup de ISBN, polimento visual, publicação no GitHub. Possíveis direções para a próxima sessão (por decidir com o Miguel, nenhuma é urgente):

1. **`README.md`** — o repositório está público mas ainda sem README. Para um projeto de portefólio, isto é provavelmente a próxima prioridade lógica: é a primeira coisa que um recrutador vê.
2. **`requirements.txt`** — o projeto só tem uma dependência externa (`PySide6`); ainda assim, é boa prática ter isto explícito para quem clonar o repositório.
3. **Limpeza do `venv`** — desinstalar `requests` (já não é usado).
4. **Fase web (Docker)** — mencionada desde o início como possibilidade futura, ainda sem prazo definido.
5. Outras melhorias funcionais à GUI (ex.: validação de ISBN com dígito de controlo antes de pesquisar, capa do livro via `cover` que a Open Library já devolve na resposta).

## Regras de trabalho (lembrete permanente)

- Nunca assumir nada sobre o ambiente ou ficheiros — confirmar sempre com Miguel antes de agir, especialmente antes de apagar/sobrepor ficheiros. Ficheiros no computador do Miguel são lidos e escritos diretamente via ferramentas de filesystem do Windows (com leitura prévia antes de qualquer escrita).
- Avançar em passos pequenos, um conceito de cada vez, com explicação, código comentado, forma de testar, e um exercício ou pergunta de consolidação.
- Comunicação em Português Europeu (PT-PT). Código e nomes de variáveis/funções em inglês. Exceção deliberada desta sessão: descrição do repositório GitHub em inglês, para alcance junto de recrutadores.
- Atualizar este ficheiro sempre que se fechar um bloco de trabalho coerente (fim de fase, ou marco relevante dentro de uma fase).
- No fim de cada sessão, sugerir um título em `kebab-case` resumindo o que foi feito, para facilitar localizar sessões antigas mais tarde.
- Ao colar blocos de código grandes, verificar sempre a indentação final.
- Sempre que uma chamada de rede falhar de forma inesperada, testar primeiro com uma ferramenta fora do Python (`Invoke-WebRequest`) antes de assumir que é bug de código — pode ser interferência do sistema (antivírus, firewall), como aconteceu nesta sessão.

## Título desta sessão

`isbn-lookup-polimento-gui-publicacao-github`
