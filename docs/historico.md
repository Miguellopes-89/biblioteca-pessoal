# historico.md — Biblioteca Pessoal

> Arquivo de consulta a pedido: incidentes resolvidos, decisões tomadas e o detalhe das alterações por ficheiro. **Não é carregado em cada sessão** — ler só quando o tema for relevante (chamadas de rede, basedpyright/CI, testes, decisões da fase web, dúvidas do tipo "porque é que fizemos X?"). O estado atual está em `context.md`.

## Incidentes resolvidos (não repetir)

1. **Google Books API sem chave devolve HTTP 429** — quota global partilhada. Fallback para Open Library é essencial.
2. **`requests`/`urllib3` com ligações resetadas** pela Open Library nesta máquina — resolvido com `urllib.request` + retry.
3. **Bug do botão "Procurar" preso indefinidamente** — erro de indentação ao colar código (`emit()` só corria dentro do `if`).
4. **basedpyright: suspeita inicial errada.** Suspeitou-se que os erros estariam no padrão `self.tabela_livros.item(...).text()` sem verificar `None`. Estava errado — esse padrão nunca gerou erro nenhum. Os erros reais eram: `dict` sem argumentos de tipo em `isbn_lookup.py` (4×) e um erro de indentação colada em `gui.py`. Lição: **correr o basedpyright a partir do terminal e ler a lista completa (ficheiro:linha:mensagem) antes de assumir onde está o problema** — o contador agregado na barra de estado do Zed (visível ao lado do separador de um ficheiro) é do projeto inteiro, não desse ficheiro.
5. **Quarta ocorrência de falha simultânea das duas APIs de ISBN**, confirmada isoladamente com `Invoke-WebRequest` por API: Google Books com 429 (quota diária esgotada), Open Library com 503. Sem indicação de bug de código, mas já a quarta vez — começa a ser um padrão a vigiar, não só coincidência. Confirmação visual da capa continua por fazer.
6. **O basedpyright reprova por omissão com avisos.** A primeira execução do CI falhou com `0 errors, 145 warnings` e exit code 1: no basedpyright, `failOnWarnings` vem ligado por omissão (diferente do pyright). Claude tinha afirmado, sem verificar, que avisos não reprovavam. Resolvido com `"failOnWarnings": false` em `pyrightconfig.json`. Lição: o código de saída de uma ferramenta nova confirma-se na prática (`gh run view --log-failed`), não se assume.
7. **`pytest` "não reconhecido" depois de mover a pasta para o OneDrive (2026-10-11).** Causa: `venv` não ativada (prompt sem `(venv)`), não a mudança de pasta. Com a venv ativa, `python -m pytest` funcionou sem recriar a venv. Lição: ver o prefixo `(venv)` do prompt antes de suspeitar do ambiente.

## Alterações detalhadas por ficheiro

- `database.py` — `get_book(livro_id) -> dict | None` acrescentado (mesmo formato de `list_books()`; usado pela rota de editar da web). Alterado em 2026-10-03: `DB_NAME` passou a caminho absoluto (`Path(__file__).resolve().parent / "biblioteca.db"`); `connect()` regista a função SQL `normalizar` (= `normalize_text`) em todas as ligações; `list_books()` e `search_books()` ordenam por `normalizar(titulo), titulo` (antes: ordem por bytes — maiúsculas antes de minúsculas, títulos acentuados no fim; bug descoberto por um teste).
- `isbn_lookup.py` — `_pedir_json` devolve `dict[str, Any] | None` (JSON de API externa é genuinamente arbitrário); `_fetch_google_books`, `_fetch_open_library`, `lookup_isbn` devolvem `dict[str, str] | None`.
- `gui.py` — dois bugs de indentação corrigidos (`QMessageBox.warning` em `pesquisar_isbn`; bloco de `linha_selecionada` que tinha ficado como código morto dentro do `if`). `PesquisaISBNThread.run()` constrói um dict novo (`{**resultado, "capa_bytes": ...}`) tipado `dict[str, str | bytes | None]`, em vez de alargar o tipo de retorno de `lookup_isbn()`.
- Lookup de ISBN na web: `GET /pesquisar-isbn?isbn=...` devolve 400 (ISBN vazio/inválido), 404 (não encontrado) ou 200 com o dict. Não usa `baixar_capa()` — o browser carrega `capa_url` num `<img>`. Caminho de sucesso nunca validado visualmente: 3 ISBNs válidos testados, sempre bloqueados pelo 429 da Google Books. **Decisão de Miguel: arrumar este assunto.** Via mais fiável se for retomado: chave de API gratuita da Google Books.
- Resolvido em 2026-10-03: o aviso "correr sempre a partir da raiz" deixou de ser necessário (`DB_NAME` absoluto).
- Modo debug do Flask (`debug=True`): recarrega ao gravar `.py`; mudanças em `database.py` também são apanhadas.

## Decisões tomadas

### App desktop
Cascata de APIs, `urllib.request`, retry simples, `QThread` para a rede, validação de ISBN antes do lookup, preenchimento seletivo pós-lookup, PySide6, type hints modernos em `database.py`, capa como pré-visualização não persistida.

### basedpyright
- `dict[str, Any]` só onde os dados são genuinamente arbitrários (JSON de API externa, em `_pedir_json`); `dict[str, str]` onde a forma é conhecida (`_fetch_*` e `lookup_isbn`).
- Conflito entre `dict[str, str]` (retorno de `lookup_isbn`) e a necessidade de juntar `capa_bytes` (`bytes`) resolvido construindo um dict novo em `gui.py`, não alargando a assinatura pública em `isbn_lookup.py` — mantém a função geral com o tipo mais preciso possível.

### Testes e CI (2026-10-03)
- Cada função de `database.py` abre e fecha a sua própria ligação, por isso `:memory:` não serve (desaparece quando a ligação fecha). Solução: fixture `isolated_db` em `tests/conftest.py`, `autouse=True`, que dá a cada teste um ficheiro temporário (`tmp_path`) e troca `database.DB_NAME` com `monkeypatch` — sem mexer nas assinaturas, e com garantia de que nenhum teste toca no `biblioteca.db` real.
- Ficheiros: `tests/test_isbn.py` (`validar_isbn`, 13 casos), `tests/test_normalize.py` (`normalize_text`, 7 casos), `tests/test_database.py` (19 testes: CRUD, pesquisa, ordenação, vários autores, vários livros sem ISBN, autor mantido ao apagar livro).
- Fluxo "vermelho → verde" usado de propósito: o teste de ordenação foi escrito primeiro, falhou como previsto, e só depois se corrigiu `database.py`.
- CI: o ambiente no runner chama-se `venv` para coincidir com `pyrightconfig.json` (`venvPath`/`venv`); o PySide6 é instalado porque o basedpyright verifica `gui.py` e precisa dos pacotes para resolver tipos. Só erros reprovam, por decisão de Miguel; exigir zero avisos fica como melhoria posterior.

### Fase web
- **Framework: Flask**, não FastAPI nem Django. Django descartado (o ORM substituiria o `database.py` escrito à mão). FastAPI adiado, não descartado — a migração futura é barata porque `database.py`/`isbn_lookup.py` não sabem qual framework os chama; só a camada de rotas mudaria.
- App desktop **não é substituída** — as duas interfaces coexistem sobre a mesma base de dados.
- Estrutura: pasta `web/` com `app.py` + `templates/`, lógica de negócio na raiz, reutilizada por importação direta (com ajuste de `sys.path`).
- Dependências da web isoladas em `requirements-web.txt`, sem tocar no `requirements.txt` original.
- Padrão de formulário: uma view function por recurso, a tratar `GET` (mostrar) e `POST` (processar) — escolhido em vez de rotas separadas, por ser o padrão idiomático do Flask para casos simples.
- Ações destrutivas (remover) só aceitam `POST`, nunca `GET`; confirmação via `confirm()` de JavaScript, equivalente ao `QMessageBox.question` da GUI.
- `get_book()` está em `database.py` (não em `web/app.py`) porque é lógica de acesso a dados, reutilizável por qualquer interface.

## Modelo de dados

Sem alterações de schema desde a última sessão (só `get_book`, uma função de leitura). Descrição das tabelas no README.

## Docker (2026-10-04)

- **Persistência: volume do Docker + variável `BIBLIOTECA_DB`** (opção B). Rejeitada a opção A (montar o `biblioteca.db` real no container): o SQLite protege contra escritas simultâneas com bloqueios do sistema operativo, que não atravessam a fronteira Windows/container; GUI e container a escrever ao mesmo tempo podiam corromper a BD. Custo assumido: o container tem a sua BD, separada da da desktop, o que contraria a ideia de "mesma base de dados" da fase web (válida só em desenvolvimento local). Consequência: `database.py` alterado numa linha (`DB_NAME = os.environ.get("BIBLIOTECA_DB", <caminho anterior>)`), comportamento por omissão igual; 39 testes continuaram a passar.
- **`create_tables()` no `CMD`**: o `gunicorn` não passa pelo bloco `__main__` do `app.py`, por isso, numa BD nova e vazia, a app arrancaria sem tabelas. Resolvido no `Dockerfile` sem tocar no `app.py`.
- **`debug=True`** deixa de estar ativo no container pelo mesmo motivo (fecha o risco de execução remota de código do debugger do Werkzeug).
- **`gunicorn==26.2.0` só na imagem**, não em `requirements-web.txt` (não corre em Windows). Versão fixada a partir do log do primeiro build.
- **`.dockerignore`** exclui `*.db`, `.env`, `venv/`, `.git`, `tests/`, `docs/`; o `Dockerfile` copia só `database.py`, `isbn_lookup.py` e `web/`, para os dados pessoais não ficarem embutidos na imagem.
- Incidente menor: o primeiro `docker run` falhou com "failed to connect to the docker API" porque o Docker Desktop não estava aberto (o CLI instalado não chega: o daemon tem de estar ativo).
- Teste de persistência: livro adicionado no browser, container parado com Ctrl+C e relançado com o mesmo volume; o livro continuou lá.
- CSRF no formulário de remover continua por tratar (aceitável em localhost; documentado no README).

## Testes das rotas Flask (2026-10-11)

- `tests/test_web.py` (17 testes): fixture `client` (`test_client` do Flask, `TESTING=True`) sobre a `isolated_db` já existente (autouse). A app lê `DB_NAME` em cada chamada de `connect()`, por isso o isolamento chega: nenhum teste web toca no `biblioteca.db` real. A fixture vive no próprio ficheiro e não no `conftest.py`, para um erro de import da app não partir os testes da base de dados.
- Lookup simulado: `monkeypatch.setattr("web.app.lookup_isbn", ...)`. A troca faz-se em `web.app` (onde o nome é usado, por causa do `from isbn_lookup import lookup_isbn`), não em `isbn_lookup`. A fixture `block_isbn_network` (autouse no ficheiro) faz rebentar qualquer chamada não simulada, para nenhum teste ir à rede por engano. Valida o caminho de sucesso **da rota**; **não** valida o parsing de `_fetch_google_books`/`_fetch_open_library`.
- Cobertura: lista vazia; adicionar (sucesso, título vazio, ISBN duplicado); pesquisa sem acentos; editar (pré-preenchimento e gravação, 404, título vazio, ISBN duplicado); remover (sucesso, GET dá 405 sem apagar, id inexistente dá 302); `/pesquisar-isbn` (400 sem ISBN, 400 com dígito de controlo errado, 404, 200).
- **Bug encontrado (por leitura do código, confirmado por teste):** `update_book` trata `None` como "manter o valor atual" e as rotas convertem campo vazio em `None`, logo esvaziar editora/coleção/género/ISBN ao editar não limpa o campo (web e desktop). Registado como `xfail(strict=True)` em `test_edit_can_clear_optional_field`: documenta o bug sem reprovar o CI, e o `strict` avisa quando for corrigido. Correção adiada: `update_book` é partilhada com a GUI e a solução limpa (valor sentinela em vez de `None`) altera a assinatura, obrigando a rever `gui.py` e `test_database.py`.
- Comportamento atual fixado em teste: remover um id inexistente redireciona (302) em vez de dar 404.
- Pasta do projeto movida para o OneDrive (backup, decisão do Miguel). Risco assumido por agora: `venv/` e `.git/` sincronizados (bloqueios de ficheiros, sincronização lenta, risco pequeno de corromper o `.git/` a meio de um commit). Mitigação: `git push` no fim de cada sessão. Decidido a seguir: ver a secção "Venv fora do OneDrive (2026-10-11)" abaixo.

## Venv fora do OneDrive (2026-10-11)

- **Decisão (Miguel):** `C:\Users\User\OneDrive\Projetos` é a localização definitiva de todos os projetos. A `venv` não tem valor como backup (os caminhos ficam gravados lá dentro; recria-se com os três `requirements*.txt`) e é pesada para sincronizar (PySide6 sozinho tem centenas de MB), por isso passou para `C:\Users\User\venvs\biblioteca-pessoal` (`python -m venv` + `pip install` dos três ficheiros). A `venv/` antiga foi apagada. O `.git/` continua no OneDrive; mitigação: `git push` no fim de cada sessão.
- **Verificação:** na venv nova, 55 passed e 1 xfailed; basedpyright com 0 erros e 284 avisos (eram 145 antes de `tests/test_web.py`; só erros reprovam, sem alteração).
- **Incidente: `pyrightconfig.json` com `venvPath`/`venv` a apontar para a pasta apagada.** O basedpyright escrevia "venv subdirectory not found" e saiu com código 3 em vez de 0 (não verificado o significado exato do 3). A flag `--pythonpath` proposta por Claude era desnecessária em local: com a venv ativada, o basedpyright usa o Python ativo (0 erros sem flag). O primeiro teste dessa flag tinha sido feito com a `venv/` antiga ainda presente e por isso não provava nada. Correção (commit `77a1f4a`): `pyrightconfig.json` só com `failOnWarnings: false`; o CI passa `--pythonpath venv/bin/python`. CI verde no run seguinte ao push. Lição: um teste feito enquanto o recurso antigo ainda existe não valida a configuração nova; apagar primeiro, testar depois.
- **Zed ficou com o interpretador errado** ("Python 3.13.14 (uv)", 1 erro e 151 avisos falsos: `pytest` e Flask por resolver), porque uma venv fora da pasta do projeto não aparece sozinha no seletor (só o `uv` e o Python global do Windows). Resolvido com "Add Virtual Environment" (âmbito Project) a apontar para `C:\Users\User\venvs\biblioteca-pessoal`; ficou "Python 3.14.6.final.0 (venv)", 0 erros e 139 avisos (a contagem do Zed não coincide com os 284 da linha de comandos; razão não verificada). `git status` limpo: a escolha não cria ficheiros no repositório.

## Correção de campos vazios em `update_book`/`add_book` (2026-10-21)

- **Premissa corrigida:** o registo de 2026-10-11 dizia que o bug afetava "web e desktop". Errado. A GUI nunca converteu campos vazios em `None`: envia `""` (texto vazio). Na GUI, esvaziar um campo ao editar funcionava, mas gravava `""` em vez de `NULL`. Só a web tinha o bug do `xfail`.
- **Bug novo, encontrado ao ler os chamadores e confirmado numa BD temporária:** na GUI, o segundo livro sem ISBN era recusado como "ISBN duplicado". `isbn` é `UNIQUE`; o SQLite aceita vários `NULL` mas só um `""`.
- **Opções consideradas:** (1) normalizar na camada de dados; (2) valor sentinela `UNSET` para "manter" e `None` para "limpar" (muda a assinatura, obriga a rever GUI e testes, e não resolve sozinha o `""` da GUI); (3) acabar com as atualizações parciais. **Escolhida a 1 (Miguel).**
- **Implementação (PR #1, branch `fix/update-book-clear-fields`, commit `25323fc`):** `database._empty_to_none` converte `""` (ou só espaços) em `None`. Aplicado em `add_book` aos quatro campos opcionais e em `update_book` só quando o campo é passado. Regra do `update_book`: `None` = manter; `""` = limpar (grava `NULL`); outro texto = grava. A rota web de editar passou a enviar `""` em vez de `None`; a de adicionar ficou como estava (`or None`, inofensivo). `gui.py` não foi alterado. Assinaturas inalteradas.
- **Testes:** removido o `xfail` de `test_edit_can_clear_optional_field`; 3 testes novos em `test_database.py` (`""` gravado como `NULL` no `add_book`; dois livros sem ISBN vindos da GUI; `""` limpa no `update_book`), escritos antes da correção e confirmados a falhar. Resultado: 59 passed, 0 xfail; basedpyright 0 erros, 283 avisos. CI verde no PR.
- **Verificação manual na GUI (PC novo, BD de teste vazia):** limpar editora e ISBN de um livro funcionou; um segundo livro com ISBN vazio foi aceite.
- **Dados antigos:** registos gravados pela GUI antes da correção podem ter `""`. Não houve migração: cada livro passa a `NULL` quando for editado e guardado na GUI. A regra `UNIQUE` garante que no máximo um livro tem ISBN `""`. Consulta de verificação (só leitura, a correr no PC original): `SELECT id, titulo FROM livros WHERE isbn='' OR editora='' OR colecao='' OR genero=''`.
- **Observado e não tratado:** a GUI aceitou `123456789` (9 dígitos) como ISBN. A validação do dígito de controlo só corre no botão "Procurar", não ao adicionar ou guardar.

## Segundo PC e push a partir da cloud (2026-10-21)

- **Novo fluxo:** o Claude Code trabalha numa cópia própria na cloud (clona o repositório, faz branch, commit, push e abre o PR). O Miguel testa no PC onde tem o Claude Code (`C:\Users\Utilizador\Desktop\biblioteca-pessoal`) e sincroniza o PC original (OneDrive) com `git pull`. O GitHub é a única fonte de verdade.
- **Setup do PC novo:** não tinha Git, Python nem `winget`. Instalados manualmente: Git 2.56 e Python 3.14.8 de 64 bits ("Add python.exe to PATH" marcado). A primeira cópia veio em ZIP (sem histórico nem ligação ao GitHub); foi substituída por `git clone`. Incidente: o clone ficou aninhado dentro da pasta do ZIP, por não se ter renomeado a pasta antes; corrigido com `Rename-Item` + `Move-Item`. Venv em `C:\Users\Utilizador\venvs\biblioteca-pessoal`, usada pelo caminho completo do `python.exe` (sem `Activate.ps1`, que a política de execução do PowerShell pode bloquear). Verificação: 55 passed, 1 xfail; basedpyright 0 erros, 284 avisos, iguais ao PC original e ao CI.
- **Incidente: janela errada do PowerShell.** A primeira tentativa foi numa janela "Administrator: Windows PowerShell (x86)". Não é precisa a de administrador, e a x86 é de 32 bits, o que é incompatível com o PySide6. Usar a "Windows PowerShell" normal.
- **Incidente: push recusado por privacidade de email.** A conta tem ativa a opção "Block command line pushes that expose my email", por isso o GitHub recusa commits com `miguellopes_89@protonmail.com`. Os commits passam a usar `279319592+Miguellopes-89@users.noreply.github.com`. Nos dois PCs: `git config --global user.email "279319592+Miguellopes-89@users.noreply.github.com"`.
- **Incidente: `gh pr create` falha nas sessões cloud** (GraphQL bloqueado). Os PRs abrem-se pela API REST (`gh api repos/.../pulls`).

## Validação e normalização do ISBN ao gravar (2026-10-21)

- **Problema:** a validação do dígito de controlo só corria no botão "Procurar". A GUI e a web gravavam ISBN como `123456789`. Risco adicional encontrado ao ler o código: `978-0-13-235088-4` e `9780132350884` passavam ambos no `validar_isbn`, mas ficavam gravados como textos diferentes, e o `UNIQUE` não os apanhava como duplicados.
- **Implementação (branch `feat/validate-isbn-on-save`, commit `4f28859`):** `isbn_lookup.normalize_isbn()` (sem hífenes nem espaços, `x` → `X`) reutilizada por `validar_isbn` e `lookup_isbn`. Em `database.py`: `_clean_isbn` (vazio → `NULL`; senão normaliza e valida) e a exceção `InvalidISBNError` (subclasse de `ValueError`), lançada por `add_book`/`update_book` **antes** de abrir a ligação. Foi escolhida uma exceção em vez de `None`/`False` porque esses valores já significam "duplicado", e a GUI mostraria a mensagem errada. `gui.py` e `web/app.py` apanham a exceção e mostram "ISBN inválido". Esquema da BD inalterado.
- **Decisões (Claude, reversíveis):** validar na camada de dados para cobrir as duas interfaces; gravar o ISBN na forma canónica; `update_book` com `isbn=None` (manter) não valida o valor antigo. Consequência: GUI e web enviam sempre o ISBN do formulário, por isso um livro antigo com ISBN inválido só volta a gravar-se depois de o ISBN ser corrigido ou apagado.
- **Testes:** 11 novos (4 `normalize_isbn`, 5 em `test_database.py`, 2 em `test_web.py`). Resultado: 70 passed; basedpyright 0 erros, 300 avisos (+17, todos do tipo já existente: 16 em testes, 1 `QMessageBox.warning` em `gui.py`; nenhum novo em `database.py`, `isbn_lookup.py` nem `web/app.py`).
- **GUI:** verificada só em modo `offscreen` (sem ecrã, caixas de mensagem simuladas): `123456789` recusado com "ISBN inválido" e nada gravado; `978-0-13-235088-4` gravado como `9780132350884`. Falta o teste visual real.
- **Dados antigos:** a BD real pode ter ISBN inválidos ou com hífenes. Consulta só de leitura (PC original, venv ativa, na raiz do projeto): `python -c "import database as d, isbn_lookup as i; [print(b['id'], b['titulo'], b['isbn']) for b in d.list_books() if b['isbn'] and (not i.validar_isbn(b['isbn']) or i.normalize_isbn(b['isbn']) != b['isbn'])]"`
- **Observado e não tratado:** na web, o formulário de adicionar volta vazio quando há erro (título vazio, duplicado, ISBN inválido), e o utilizador perde o que escreveu. Já acontecia antes desta alteração.
- **Incidente: eliminar branches remotas está bloqueado na sessão cloud.** `git push --delete` e `DELETE /git/refs` pela API REST devolvem 403 (regra do proxy, não do GitHub). O push de branches novas funciona. A branch `fix/update-book-clear-fields` (já integrada) ficou por apagar pelo Miguel.

### Revisão: assinalar em vez de recusar (2026-10-21, mesma branch)

- **Porquê:** a primeira versão recusava ISBN com dígito de controlo inválido, o que contradizia uma decisão já tomada pelo Miguel ("assinalar ao gravar, não recusar"). A sessão anterior não a consultou. Efeito colateral da versão recusadora: um livro antigo com ISBN inválido deixava de poder ser editado (a GUI e a web enviam sempre o ISBN do formulário).
- **Agora (commit `4558142`):** `_clean_isbn` só normaliza; `InvalidISBNError` removida. GUI: depois de gravar, se `validar_isbn` falhar, aparece "Gravado, mas o ISBN parece inválido" em vez de "Sucesso". Web: `app.add_template_global(validar_isbn, name="isbn_valido")` e `index.html` mostra "⚠ ISBN inválido" ao lado do ISBN. É persistente, por isso cobre também livros antigos. Optou-se por isto em vez de `flash` (mensagem de uma só vez do Flask), que exigiria uma `SECRET_KEY`.
- **Testes:** 4 testes de recusa reescritos para exigir gravação, mais 1 novo (ISBN válido sem aviso). Resultado: 71 passed; basedpyright 0 erros, 304 avisos (+4 face à primeira versão, todos em `tests/test_web.py`, `client` sem tipo).
- **GUI:** verificada só em `offscreen`. `123456789` é gravado e mostra o aviso; `978-0-13-235088-4` é gravado como `9780132350884` e mostra "Sucesso".
- **Incidente de processo:** o `context.md` carregado no Projeto vinha da `main`, mas a versão atualizada só existia na branch do PR #2, ainda por integrar. O `CLAUDE.md` do Projeto passou a exigir, no fim de cada sessão, a entrega do `context.md` como ficheiro com indicação da branch, e no início a verificação de PRs abertos.
- **Verificado no ecrã (PC novo):** depois de um `git pull` (a primeira tentativa correu a cópia local antiga da branch, parada em `c8b02e5`: `git switch` não atualiza uma branch que já existe localmente), `123456789` e `978-0-13-235088-5` gravam com o aviso, e `978-0-13-235088-4` é recusado como duplicado de `9780132350884`.
- **ISBN a vermelho (pedido do Miguel, como lembrete numa BD grande):** na GUI, `_celula_isbn` pinta a célula com `#c62828` e acrescenta uma explicação ao passar o rato; na web, a célula leva a classe `isbn-invalido` com a mesma cor. Só para dígito de controlo inválido: um ISBN antigo válido com hífenes fica a preto (é o mesmo número; normaliza-se na próxima edição).
- **Integração:** PR #2 integrado com o merge `952b1fd` depois de o Miguel ver a cor no ecrã.

## Testes do parsing das APIs de ISBN (2026-10-21)

- **Problema:** o caminho de sucesso de `_fetch_google_books`/`_fetch_open_library` nunca tinha sido testado. A Google Books dava 429 e os testes web simulavam o `lookup_isbn` inteiro, por isso o parsing ficava de fora.
- **Implementação (branch `test/isbn-fetch-parsing`):** `tests/test_isbn_fetch.py` troca `_pedir_json` (com `monkeypatch`) por funções que devolvem um dict escrito à mão. Cobre: resposta típica, vários autores/categorias/editoras, campos em falta, sem resultados, falha de rede, URL pedido, cascata Google → Open Library e JSON inválido em `_pedir_json`. A fixture autouse `no_network` troca `_pedir_bytes` por uma função que rebenta, para nenhum teste sair para a internet por engano.
- **Bug encontrado:** `dados["items"][0]` rebentava com `KeyError` quando a resposta trazia `totalItems > 0` sem `items`. Correção: decidir pela lista `items` e não pelo número `totalItems`. Testado pelo lado do `_fetch_google_books` e pelo lado da cascata.
- **Limite:** as respostas simuladas seguem a estrutura documentada das APIs (ISBN `9780132350884`) e não foram comparadas com uma resposta real. A rede da sessão cloud bloqueia `googleapis.com` e `openlibrary.org`; o WebFetch também falhou (robots.txt na Open Library, erro na Google). Os comandos `Invoke-RestMethod` para confirmar no PC estão no `context.md`.
- **Observado e não tratado:** (a) o título da Google ignora o `subtitle`; (b) o comentário diz que a Open Library não expõe `subjects` neste endpoint, o que fica por confirmar com a resposta real; (c) hipótese: `_pedir_bytes` não apanha `ConnectionResetError` durante `resposta.read()`.
- **Avisos:** os `# pyright: ignore` acrescentados de início (acesso a funções privadas `_fetch_*`) foram retirados, por o projeto não os usar em lado nenhum. Ficam +35 avisos em `tests/test_isbn_fetch.py`.

### Respostas reais comparadas com as simuladas (2026-10-21, noite, mesma branch)

- **Como:** a rede da sessão cloud continua a bloquear as duas APIs (403 do proxy). As respostas foram lidas no browser integrado da app Claude no PC do Miguel, com o ISBN `9780132350884`.
- **Open Library: confirmada.** As chaves que o código lê (`title`, `authors[].name`, `publishers[].name`, `cover.medium`) existem com a forma assumida. A resposta simulada passou a ser uma cópia encurtada da real (título "Clean Code", capa `15126503`, `subtitle`, `subjects`, `number_of_pages`). Testes: 89 passed; basedpyright 0 erros, 341 avisos (sem alteração).
- **Correção de um facto:** o comentário em `isbn_lookup.py` dizia que a Open Library não expõe `subjects` neste endpoint. Expõe: lista de `{name, url}` com temas detalhados ("Agile software development", "Coding theory"…), não um género. O código continua a ignorá-los; o comentário foi corrigido.
- **Google Books: continua por confirmar, e esperar não resolve.** Voltou a dar 429, mas os metadados do erro dizem `quota_limit: defaultPerDayPerProject` com `quota_limit_value: "0"` no projeto partilhado que a Google usa para pedidos sem chave. Ou seja, a quota anónima está a zero, não esgotada. Consequência prática: hoje a cascata cai sempre na Open Library, e cada pesquisa perde primeiro as 3 tentativas à Google (2 pausas de 1 s) por causa do retry em `_pedir_bytes`, que repete também erros HTTP 4xx.

## Sem retry para erros HTTP 4xx (2026-10-21, refeito)

- **Incidente de processo:** a primeira implementação (sessão da noite anterior, branch `fix/no-retry-on-http-4xx`, 7 testes) ficou só no disco da sessão cloud, sem push. As sessões cloud apagam o disco ao fechar, por isso o trabalho perdeu-se. O `context.md` entregue ao Miguel (96 testes, 349 avisos) descrevia esse estado; o GitHub estava em 89 testes e 341 avisos. Regra nova: **nas sessões cloud, push imediato depois de cada commit** (registada no `context.md` e a acrescentar ao `CLAUDE.md`).
- **Ordem:** o PR #3 foi integrado primeiro (merge `9448bda`, CI verde, confirmação do Miguel) e a branch foi recriada a partir da `main`, por isso o PR novo só tem os commits do retry.
- **Implementação (commit `c168502`):** `_pedir_bytes` apanha `urllib.error.HTTPError` antes de `URLError` (é subclasse dela). Código 400–499 → devolve `None` logo, sem pausa. 5xx → repete como antes. Falhas de rede (`URLError`, `TimeoutError`) → como antes.
- **Testes:** `tests/test_pedir_bytes.py`, 8 testes (4xx com 400/404/429/499 parametrizados; sucesso à primeira; 5xx que recupera; 5xx que esgota as tentativas; falha de rede que recupera). Trocam `urllib.request.urlopen` e `time.sleep` por versões falsas que contam pedidos e pausas. Os 4 testes de 4xx falham com o código antigo (confirmado com `git stash`). Resultado: 97 passed; basedpyright 0 erros, 346 avisos (+5, todos `reportPrivateUsage` por testar `_pedir_bytes`).
- **Por verificar:** o ganho real de tempo só se mede num PC (a cloud não chega às APIs).
