# context.md — Biblioteca Pessoal

> Este ficheiro é o "estado da sessão" do projeto. Cola o conteúdo no início de uma nova conversa com o Claude para retomar exatamente onde ficámos, sem reexplicar nada.

## Sobre o projeto

Aplicação desktop em Python para catalogar livros pessoais (título, autor(es), editora, coleção, género, ISBN, estado de leitura), com inserção manual e/ou por leitura de ISBN via API gratuita (Open Library ou Google Books) — ainda não implementado —, base de dados SQLite local, GUI desktop em PySide6, funcionamento offline. Publicável no GitHub como parte do portefólio. Fase web é possibilidade futura (Docker pode entrar aí).

Claude atua como tutor sénior: explica o "porquê" de cada decisão, avança passo a passo, nunca assume conhecimento prévio, nunca assume factos sobre o ambiente sem confirmar.

## Ambiente

- **SO:** Windows
- **Python:** 3.14.6
- **Git:** 2.55.0
- **Editor:** Zed
- **Docker:** instalado, não relevante ainda (fase web futura)
- **Caminho do projeto:** `C:\Users\User\Projetos\biblioteca-pessoal`
- **Ambiente virtual:** pasta `venv/`, ativar sempre no início de cada sessão de terminal nova:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Dependência externa instalada:** `PySide6` 6.11.2 (primeira dependência fora da standard library — `venv` agora obrigatório para correr `gui.py`, não só recomendado).
- **`pyrightconfig.json`** criado na raiz do projeto (`{"venvPath": ".", "venv": "venv"}`) para o linter do Zed (`basedpyright`) apontar para o interpretador do `venv` em vez do Python global do Windows. Resolveu os falsos erros de importação do PySide6.

## Estado atual do repositório Git

- Branch única: `main`
- Sem remoto configurado (ainda não ligado ao GitHub)
- **9 commits feitos até ao início desta sessão** (ver histórico anterior). **Nesta sessão ainda não foi feito nenhum commit** — há trabalho substancial por commitar (ver secção "Ficheiros existentes"). Sugestão: pelo menos dois commits separados — um para a coluna `estado_leitura` + correções de bugs no `database.py`, outro para a GUI PySide6 completa (`gui.py` + `pyrightconfig.json`).
- `.gitignore` cobre: `venv/`, `__pycache__/`, `*.pyc`, `.env`, `*.db`

## Ficheiros existentes

- `.gitignore`
- `main.py` — smoke test original, sem lógica da aplicação. Não usado pela GUI.
- `pyrightconfig.json` — novo nesta sessão (ver acima).
- `database.py` — módulo da base de dados SQLite. Mudanças nesta sessão:
  - Nova coluna `estado_leitura` (TEXT, NOT NULL, DEFAULT 'não lido') na tabela `livros`, com valores esperados: `"não lido"`, `"a ler"`, `"lido"`.
  - `create_tables()` — migração idempotente: verifica via `PRAGMA table_info(livros)` se a coluna já existe; se não, corre `ALTER TABLE ADD COLUMN`. Seguro correr em bases de dados já existentes sem perder dados.
  - `add_book(...)` — novo parâmetro `estado_leitura="não lido"` (omissão sensata).
  - `list_books()` e `search_books()` — `SELECT` atualizado para incluir `livros.estado_leitura`.
  - `update_book(...)` — novo parâmetro `estado_leitura=None` (segue o padrão dos outros campos opcionais: `None` = não mexer).
  - Continua a expor: `normalize_text`, `connect`, `create_tables`, `get_or_create_author`, `add_book`, `list_books`, `search_books`, `update_book`, `delete_book`.
- `gui.py` — **novo nesta sessão**. Interface desktop em PySide6 (`QMainWindow`). Contém:
  - Formulário (`QFormLayout`) com campos para todos os atributos do livro, incluindo `QComboBox` para estado de leitura.
  - Dois botões: "Adicionar Livro" / "Guardar Alterações" (o mesmo botão, texto muda consoante o modo) e "Remover Livro".
  - Campo de pesquisa com botões "Pesquisar" e "Limpar", ligado a `search_books`.
  - Tabela (`QTableWidget`, só leitura) a listar todos os livros, com 8 colunas (ID, Título, Autores, Editora, Coleção, Género, ISBN, Estado).
  - Clicar numa linha da tabela carrega os dados no formulário e entra em "modo edição" (`self.livro_selecionado_id` guarda o id; `None` = modo adicionar).
  - `guardar_livro()` decide entre `add_book` (modo adicionar) e `update_book` (modo edição) consoante `self.livro_selecionado_id`.
  - `remover_livro()` pede confirmação via `QMessageBox.question` antes de chamar `delete_book`.
  - `preencher_tabela(livros)` — método auxiliar partilhado entre `atualizar_tabela()` (lista completa) e `executar_pesquisa()` (resultados filtrados), para não duplicar a lógica de preencher a `QTableWidget`.
  - Depois de guardar/remover, a tabela volta sempre à lista completa (não mantém filtro de pesquisa ativo) — simplificação deliberada, documentada no código.
- `biblioteca.db` — gerado localmente, não versionado. Contém atualmente 3 livros de teste ("A Quinta Dos Animais", "Meditações", "O Despertar do Império").

## Modelo de dados (schema SQLite)

- **livros**: `id` (PK), `titulo`, `editora`, `colecao`, `genero`, `isbn` (UNIQUE), `estado_leitura` (NOT NULL, DEFAULT 'não lido') — coluna nova nesta sessão
- **autores**: `id` (PK), `nome` (UNIQUE)
- **livro_autor**: `livro_id` + `autor_id` (PK composta, FKs) — permite um livro ter vários autores e um autor ter vários livros

## Testado e validado nesta sessão

- Instalação do PySide6 no `venv`, confirmada versão 6.11.2.
- Janela mínima (`QMainWindow`) a abrir corretamente.
- Formulário completo visível e funcional.
- Migração da coluna `estado_leitura` — corre sem apagar dados existentes.
- `add_book` via GUI — testado com sucesso, ISBN duplicado, e título vazio (os três casos dão o aviso/sucesso esperado).
- Tabela de listagem — pré-preenchida no arranque, atualiza-se sozinha após adicionar.
- Edição via seleção na tabela — campos preenchem-se ao clicar numa linha, `update_book` chamado corretamente, tabela atualiza.
- Remoção via seleção — pede confirmação, `delete_book` chamado corretamente.
- **Bug encontrado e corrigido**: depois de guardar/remover, `limpar_campos()` chama `tabela_livros.clearSelection()`, que dispara `itemSelectionChanged` outra vez. `linha_selecionada()` usava `currentRow()` (que não é reposto por `clearSelection()`), reentrando em modo edição imediatamente. Corrigido verificando `self.tabela_livros.selectedItems()` no início de `linha_selecionada()` antes de usar `currentRow()`.
- Pesquisa — testada com termo existente (filtra corretamente), "Limpar" (volta à lista completa), termo inexistente (tabela vazia sem erro), e edição a partir dos resultados da pesquisa (funciona, tabela volta à lista completa depois de guardar).

## Incidentes resolvidos nesta sessão (histórico, não repetir)

1. **Falsos erros do linter (`basedpyright`) a apontar para o Python global do Windows em vez do `venv`** — resolvido com `pyrightconfig.json` (ver secção Ambiente). O Zed não tem um comando "Select Interpreter" como o VS Code; a configuração é feita por ficheiro de projeto.
2. **`database.py` colado pelo Miguel com bugs estruturais na função `update_book`**: a leitura de `livro_atual` da base de dados tinha desaparecido do código, com variáveis a serem usadas antes de definidas, e duas instruções `UPDATE` duplicadas. Corrigido reescrevendo a função com a ordem correta (SELECT → calcular novos valores → UPDATE único).
3. **`gui.py` colado pelo Miguel com bug de indentação**: o método `atualizar_tabela` tinha ficado fora da classe `JanelaPrincipal` (a seguir ao bloco `if __name__ == "__main__":`), e havia uma linha órfã `widget_central.setLayout(layout)` a referenciar uma variável (`layout`) que já não existia. Corrigido movendo o método para dentro da classe e removendo a linha órfã.
4. **Aviso "24 erros / 110 avisos" no Zed** — investigado, confirmado ser apenas avisos de type hints em falta (`reportUnknownParameterType`, `reportMissingParameterType` do `basedpyright`), zero impacto funcional. Baixa prioridade, não corrigido.

## Notas técnicas / decisões tomadas

- Escolha de biblioteca de GUI: **PySide6** (não `tkinter`) — decisão consciente para portefólio: visual mais moderno, widgets mais ricos, mostra mais capacidade técnica, apesar da dependência externa. Licença LGPL (diferença face ao PyQt, que é GPL/comercial).
- Modo adicionar vs. modo edição na GUI é controlado por um único atributo (`self.livro_selecionado_id`, `None` ou um `id`), não por duas telas/formulários separados — mantém a GUI simples com um único conjunto de campos reutilizado.
- Botão "Adicionar Livro" / "Guardar Alterações" é o mesmo widget, só muda o texto — evita duplicar lógica de validação.
- `QMessageBox.question` usado para confirmar remoção (ação irreversível); `QMessageBox.information`/`.warning` para feedback de sucesso/erro nas outras ações.
- `NoEditTriggers` na tabela — edição feita exclusivamente via formulário, não célula-a-célula diretamente na tabela.
- Todas as decisões anteriores sobre o modelo de dados (ISBN como chave de duplicado, `LOWER()` para autores, autores em string separada por vírgulas, normalização de pesquisa via `unicodedata`, autores órfãos mantidos após remover livro) continuam válidas e inalteradas.

## Próximo passo

CRUD completo (criar, listar, pesquisar, editar, remover) está agora implementado e testado tanto na camada de dados como na GUI. Três direções possíveis para a próxima sessão, por ordem de prioridade sugerida:

1. **Fazer os commits em falta** — há trabalho substancial desde o último commit (coluna `estado_leitura`, `gui.py` completo, `pyrightconfig.json`). Deve ser o primeiro passo da próxima sessão, antes de continuar a desenvolver.
2. **Polimento visual da GUI** — redimensionar colunas automaticamente (a coluna "Estado" fica cortada em janelas mais estreitas), considerar esconder/encolher a coluna ID.
3. **Lookup de ISBN via API** (Open Library ou Google Books) — próximo salto funcional grande: chamada de rede, tratamento de falhas/timeouts, preenchimento automático do formulário a partir da resposta da API.
4. **Publicar no GitHub** — repositório local pronto, falta criar o repo remoto e fazer o primeiro `push`.

## Regras de trabalho (lembrete permanente)

- Nunca assumir nada sobre o ambiente ou ficheiros — confirmar sempre com Miguel antes de agir, especialmente antes de apagar/sobrepor ficheiros. Nesta sessão, ficheiros no computador do Miguel foram lidos e escritos diretamente via ferramenta de filesystem do Windows (com leitura prévia antes de qualquer escrita, para confirmar que o conteúdo em disco correspondia ao esperado).
- Avançar em passos pequenos, um conceito de cada vez, com explicação, código comentado, forma de testar, e um exercício ou pergunta de consolidação.
- Comunicação em Português Europeu (PT-PT). Código e nomes de variáveis/funções em inglês.
- Atualizar este ficheiro sempre que se fechar um bloco de trabalho coerente (fim de fase, ou marco relevante dentro de uma fase).
- No fim de cada sessão, sugerir um título em `kebab-case` resumindo o que foi feito, para facilitar localizar sessões antigas mais tarde.
- Ao colar blocos de código grandes, verificar sempre a indentação final (já aconteceu duas vezes nesta sessão: métodos a ficarem fora da classe por engano).

## Título desta sessão

`gui-pyside6-crud-completo-com-pesquisa`
