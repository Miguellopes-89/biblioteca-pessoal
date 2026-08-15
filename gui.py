# gui.py
#
# Interface gráfica da Biblioteca Pessoal, construída com Tkinter e o
# seu conjunto de widgets modernizados (ttk) — ambos vêm incluídos no
# Python, não é preciso instalar nada de novo.
#
# Este ficheiro só se preocupa em desenhar janelas e reagir a cliques;
# toda a lógica de dados continua em database.py, e a pesquisa por
# ISBN continua em metadados_isbn.py — exatamente a mesma separação de
# responsabilidades que já tínhamos entre cli.py e o resto do
# programa. É por isso que esta interface gráfica não precisou de
# tocar em database.py: só reutiliza o que já estava testado e a
# funcionar através da CLI. cli.py continua a funcionar normalmente —
# esta é só uma segunda forma de usar a mesma biblioteca.

import tkinter as tk
from tkinter import ttk, messagebox

import database
import metadados_isbn
from constantes import ESTADOS_LEITURA, GENEROS, LIMITE_NOTA

FILTRO_TODOS = "Todos"


class JanelaPrincipal(tk.Tk):
    """Janela principal: lista de livros, pesquisa, filtro e botões de ação."""

    def __init__(self):
        super().__init__()
        self.title("Biblioteca Pessoal")
        self.geometry("900x500")
        self.minsize(700, 400)

        database.criar_tabela()

        self._construir_barra_pesquisa()
        self._construir_tabela()
        self._construir_barra_botoes()

        self.atualizar_lista()

    # ------------------------------------------------------------------
    # Construção da interface
    # ------------------------------------------------------------------

    def _construir_barra_pesquisa(self):
        moldura = ttk.Frame(self, padding=10)
        moldura.pack(fill="x")

        ttk.Label(moldura, text="Procurar:").pack(side="left")
        self.campo_pesquisa = ttk.Entry(moldura, width=30)
        self.campo_pesquisa.pack(side="left", padx=(5, 10))
        self.campo_pesquisa.bind("<Return>", lambda evento: self.atualizar_lista())

        ttk.Label(moldura, text="Estado:").pack(side="left")
        self.filtro_estado = ttk.Combobox(
            moldura,
            values=[FILTRO_TODOS] + ESTADOS_LEITURA,
            state="readonly",
            width=12,
        )
        self.filtro_estado.set(FILTRO_TODOS)
        self.filtro_estado.pack(side="left", padx=(5, 10))
        self.filtro_estado.bind("<<ComboboxSelected>>", lambda evento: self.atualizar_lista())

        ttk.Button(moldura, text="Procurar", command=self.atualizar_lista).pack(side="left")
        ttk.Button(moldura, text="Limpar", command=self._limpar_pesquisa).pack(side="left", padx=(5, 0))

    def _construir_tabela(self):
        moldura = ttk.Frame(self, padding=(10, 0))
        moldura.pack(fill="both", expand=True)

        colunas = ("titulo", "autor", "genero", "estado", "isbn")
        self.tabela = ttk.Treeview(moldura, columns=colunas, show="headings", selectmode="browse")

        self._titulos_colunas = {
            "titulo": "Título",
            "autor": "Autor",
            "genero": "Género",
            "estado": "Estado",
            "isbn": "ISBN",
        }
        larguras = {"titulo": 220, "autor": 160, "genero": 140, "estado": 80, "isbn": 120}

        # Estado da ordenação atual: nenhuma coluna escolhida ainda, e a
        # próxima ordenação começa sempre ascendente.
        self._coluna_ordenada = None
        self._ordem_ascendente = True

        for coluna in colunas:
            # O parâmetro `command` do cabeçalho é suportado nativamente
            # pelo ttk.Treeview: clicar no cabeçalho chama esta função,
            # sem precisarmos de detetar cliques manualmente.
            self.tabela.heading(
                coluna,
                text=self._titulos_colunas[coluna],
                command=lambda c=coluna: self._ordenar_coluna(c),
            )
            self.tabela.column(coluna, width=larguras[coluna], anchor="w")

        barra_scroll = ttk.Scrollbar(moldura, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra_scroll.set)

        self.tabela.pack(side="left", fill="both", expand=True)
        barra_scroll.pack(side="right", fill="y")

        # Duplo clique numa linha mostra a nota pessoal desse livro
        # (não cabe numa coluna da tabela sem a tornar demasiado larga).
        self.tabela.bind("<Double-1>", lambda evento: self._mostrar_nota_selecionada())

    def _construir_barra_botoes(self):
        moldura = ttk.Frame(self, padding=10)
        moldura.pack(fill="x")

        ttk.Button(moldura, text="Adicionar Livro", command=self._abrir_janela_adicionar).pack(side="left")
        ttk.Button(
            moldura, text="Atualizar Estado", command=self._abrir_janela_atualizar_estado
        ).pack(side="left", padx=(10, 0))
        ttk.Button(
            moldura, text="Remover Livro", command=self._remover_livro_selecionado
        ).pack(side="left", padx=(10, 0))
        ttk.Button(moldura, text="Atualizar Lista", command=self.atualizar_lista).pack(side="right")

        self.rotulo_total = ttk.Label(moldura, text="")
        self.rotulo_total.pack(side="right", padx=(0, 15))

    # ------------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------------

    def _limpar_pesquisa(self):
        self.campo_pesquisa.delete(0, "end")
        self.filtro_estado.set(FILTRO_TODOS)
        self.atualizar_lista()

    def _ordenar_coluna(self, coluna):
        """
        Ordena as linhas da tabela pela coluna cujo cabeçalho foi
        clicado. Clicar outra vez na mesma coluna inverte a ordem
        (ascendente/descendente) — o comportamento habitual em
        cabeçalhos de tabela clicáveis.

        Esta ordenação age só sobre as linhas já visíveis na tabela
        (não volta a consultar a base de dados) — reordenar uma
        centena de livros em memória é instantâneo, não há razão
        para complicar isto com SQL.
        """
        linhas = [(self.tabela.set(item_id, coluna), item_id) for item_id in self.tabela.get_children("")]

        if self._coluna_ordenada == coluna:
            self._ordem_ascendente = not self._ordem_ascendente
        else:
            self._ordem_ascendente = True
        self._coluna_ordenada = coluna

        # normalizar_texto ignora acentos e maiúsculas/minúsculas, para
        # a ordenação ser consistente com a pesquisa (ex.: "Meditações"
        # ordena como "meditacoes", não fica fora de sítio por causa do
        # acento).
        linhas.sort(key=lambda par: database.normalizar_texto(par[0]), reverse=not self._ordem_ascendente)

        for indice, (_valor, item_id) in enumerate(linhas):
            self.tabela.move(item_id, "", indice)

        self._atualizar_texto_cabecalhos()

    def _atualizar_texto_cabecalhos(self):
        """
        Reescreve o texto de todos os cabeçalhos, acrescentando uma
        seta (▲ ascendente / ▼ descendente) só à coluna atualmente
        ordenada — sinal visual comum para indicar a ordenação ativa.
        """
        for coluna, titulo in self._titulos_colunas.items():
            if coluna == self._coluna_ordenada:
                seta = " ▲" if self._ordem_ascendente else " ▼"
                self.tabela.heading(coluna, text=titulo + seta)
            else:
                self.tabela.heading(coluna, text=titulo)

    def atualizar_lista(self):
        """
        Vai buscar os livros à base de dados, aplicando o filtro de
        estado e o termo de pesquisa atualmente escolhidos, e volta a
        desenhar a tabela. É chamada sempre que algo muda (pesquisa,
        filtro, ou depois de adicionar/atualizar/remover um livro) —
        é mais simples recarregar tudo do que tentar atualizar só a
        linha que mudou, e para uma biblioteca pessoal (não milhares
        de livros) isto é instantâneo.
        """
        estado_selecionado = self.filtro_estado.get()
        estado_filtro = None if estado_selecionado in ("", FILTRO_TODOS) else estado_selecionado
        livros = database.listar_livros(estado_leitura=estado_filtro)

        termo = self.campo_pesquisa.get().strip()
        if termo:
            termo_normalizado = database.normalizar_texto(termo)
            livros = [
                livro
                for livro in livros
                if termo_normalizado in database.normalizar_texto(livro["titulo"])
                or termo_normalizado in database.normalizar_texto(livro["autor"])
            ]

        self.tabela.delete(*self.tabela.get_children())
        self._notas_por_id = {}
        # Uma nova lista (pesquisa, filtro, ou depois de adicionar/
        # remover um livro) volta sempre à ordem por omissão da base
        # de dados (título, alfabética) — a ordenação por coluna
        # clicada é só para a vista atual, não é "lembrada" entre
        # atualizações.
        self._coluna_ordenada = None
        self._ordem_ascendente = True
        self._atualizar_texto_cabecalhos()
        for livro in livros:
            self.tabela.insert(
                "",
                "end",
                iid=str(livro["id"]),
                values=(
                    livro["titulo"],
                    livro["autor"],
                    livro["genero"],
                    livro["estado_leitura"],
                    livro["isbn"] or "",
                ),
            )
            self._notas_por_id[str(livro["id"])] = livro["nota"]

        self.rotulo_total.config(text=f"{len(livros)} livro(s)")

    def _obter_id_selecionado(self):
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showinfo("Nenhum livro selecionado", "Seleciona primeiro um livro na lista.")
            return None
        return int(selecao[0])

    def _mostrar_nota_selecionada(self):
        selecao = self.tabela.selection()
        if not selecao:
            return
        nota = self._notas_por_id.get(selecao[0])
        titulo = self.tabela.item(selecao[0], "values")[0]
        messagebox.showinfo(f"Nota — {titulo}", nota if nota else "(sem nota)")

    def _remover_livro_selecionado(self):
        livro_id = self._obter_id_selecionado()
        if livro_id is None:
            return
        titulo = self.tabela.item(str(livro_id), "values")[0]
        confirmar = messagebox.askyesno(
            "Confirmar remoção",
            f'Tens a certeza que queres remover "{titulo}"? Esta ação não pode ser desfeita.',
        )
        if confirmar:
            database.remover_livro(livro_id)
            self.atualizar_lista()

    def _abrir_janela_adicionar(self):
        JanelaAdicionarLivro(self)

    def _abrir_janela_atualizar_estado(self):
        livro_id = self._obter_id_selecionado()
        if livro_id is None:
            return
        JanelaAtualizarEstado(self, livro_id)


class JanelaAdicionarLivro(tk.Toplevel):
    """Janela modal para adicionar um livro novo, com pesquisa opcional por ISBN."""

    def __init__(self, janela_principal):
        super().__init__(janela_principal)
        self.janela_principal = janela_principal
        self.title("Adicionar Livro")
        self.geometry("420x430")
        self.resizable(False, False)
        self.transient(janela_principal)
        self.grab_set()  # torna a janela modal — bloqueia a janela principal até esta fechar

        moldura = ttk.Frame(self, padding=15)
        moldura.pack(fill="both", expand=True)

        ttk.Label(moldura, text="ISBN (opcional):").grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.campo_isbn = ttk.Entry(moldura, width=24)
        self.campo_isbn.grid(row=0, column=1, pady=(0, 5), sticky="we")
        ttk.Button(moldura, text="Procurar ISBN", command=self._procurar_isbn).grid(
            row=0, column=2, padx=(5, 0)
        )

        ttk.Label(moldura, text="Título:").grid(row=1, column=0, sticky="w", pady=5)
        self.campo_titulo = ttk.Entry(moldura, width=30)
        self.campo_titulo.grid(row=1, column=1, columnspan=2, sticky="we", pady=5)

        ttk.Label(moldura, text="Autor:").grid(row=2, column=0, sticky="w", pady=5)
        self.campo_autor = ttk.Entry(moldura, width=30)
        self.campo_autor.grid(row=2, column=1, columnspan=2, sticky="we", pady=5)

        ttk.Label(moldura, text="Género:").grid(row=3, column=0, sticky="w", pady=5)
        self.campo_genero = ttk.Combobox(moldura, values=GENEROS, state="readonly", width=28)
        self.campo_genero.grid(row=3, column=1, columnspan=2, sticky="we", pady=5)
        self.campo_genero.current(0)

        ttk.Label(moldura, text="Estado:").grid(row=4, column=0, sticky="w", pady=5)
        self.campo_estado = ttk.Combobox(moldura, values=ESTADOS_LEITURA, state="readonly", width=28)
        self.campo_estado.grid(row=4, column=1, columnspan=2, sticky="we", pady=5)
        self.campo_estado.current(0)

        ttk.Label(moldura, text=f"Nota (até {LIMITE_NOTA} car.):").grid(
            row=5, column=0, sticky="nw", pady=5
        )
        self.campo_nota = tk.Text(moldura, width=30, height=4, wrap="word")
        self.campo_nota.grid(row=5, column=1, columnspan=2, sticky="we", pady=5)
        self.campo_nota.bind("<KeyRelease>", self._atualizar_contador_nota)

        self.rotulo_contador = ttk.Label(moldura, text=f"0/{LIMITE_NOTA}")
        self.rotulo_contador.grid(row=6, column=1, columnspan=2, sticky="e")

        moldura_botoes = ttk.Frame(moldura)
        moldura_botoes.grid(row=7, column=0, columnspan=3, pady=(15, 0))
        ttk.Button(moldura_botoes, text="Guardar", command=self._guardar).pack(side="left", padx=5)
        ttk.Button(moldura_botoes, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

        self.campo_isbn.focus_set()

    def _atualizar_contador_nota(self, evento=None):
        texto = self.campo_nota.get("1.0", "end-1c")
        self.rotulo_contador.config(text=f"{len(texto)}/{LIMITE_NOTA}")

    def _procurar_isbn(self):
        isbn = self.campo_isbn.get().strip()
        if not isbn:
            messagebox.showinfo("ISBN em falta", "Escreve um ISBN antes de procurar.")
            return

        try:
            encontrado = metadados_isbn.procurar_por_isbn(isbn)
        except metadados_isbn.ISBNNaoEncontrado:
            messagebox.showinfo(
                "Não encontrado",
                "Este ISBN não existe no catálogo da Open Library.\n"
                "Preenche o título e o autor à mão.",
            )
            return
        except metadados_isbn.ErroDeRede:
            messagebox.showwarning(
                "Sem ligação",
                "Não foi possível contactar a Open Library agora.\n"
                "Preenche o título e o autor à mão, ou tenta outra vez mais tarde.",
            )
            return

        # Preenche os campos, mas o utilizador continua livre para
        # corrigir tudo antes de guardar — nada é gravado sem passar
        # por este formulário e pelo botão "Guardar".
        self.campo_titulo.delete(0, "end")
        self.campo_titulo.insert(0, encontrado["titulo"])
        if encontrado["autor"]:
            self.campo_autor.delete(0, "end")
            self.campo_autor.insert(0, encontrado["autor"])

    def _guardar(self):
        titulo = self.campo_titulo.get().strip()
        autor = self.campo_autor.get().strip()
        isbn = self.campo_isbn.get().strip() or None
        genero = self.campo_genero.get()
        estado = self.campo_estado.get()
        nota = self.campo_nota.get("1.0", "end-1c").strip() or None

        if not titulo or not autor:
            messagebox.showerror("Dados em falta", "Título e autor são obrigatórios.")
            return
        if nota and len(nota) > LIMITE_NOTA:
            messagebox.showerror(
                "Nota demasiado longa", f"A nota tem {len(nota)} caracteres — o limite é {LIMITE_NOTA}."
            )
            return

        if isbn:
            # Aviso, não bloqueio — mesma decisão de cli.py: o
            # utilizador pode ter mesmo duas cópias físicas do mesmo
            # livro, por isso pergunta-se em vez de recusar.
            livro_existente = database.buscar_livro_por_isbn(isbn)
            if livro_existente:
                continuar = messagebox.askyesno(
                    "Possível duplicado",
                    f'Já existe um livro com este ISBN:\n"{livro_existente["titulo"]}" — '
                    f'{livro_existente["autor"]}.\n\nAdicionar mesmo assim?',
                )
                if not continuar:
                    return

        database.adicionar_livro(
            titulo=titulo, autor=autor, genero=genero, estado_leitura=estado, isbn=isbn, nota=nota
        )
        self.janela_principal.atualizar_lista()
        self.destroy()


class JanelaAtualizarEstado(tk.Toplevel):
    """Janela modal simples para mudar o estado de leitura de um livro."""

    def __init__(self, janela_principal, livro_id):
        super().__init__(janela_principal)
        self.janela_principal = janela_principal
        self.livro_id = livro_id
        self.title("Atualizar Estado de Leitura")
        self.geometry("300x150")
        self.resizable(False, False)
        self.transient(janela_principal)
        self.grab_set()

        moldura = ttk.Frame(self, padding=15)
        moldura.pack(fill="both", expand=True)

        ttk.Label(moldura, text="Novo estado de leitura:").pack(anchor="w", pady=(0, 10))
        self.campo_estado = ttk.Combobox(moldura, values=ESTADOS_LEITURA, state="readonly", width=20)
        self.campo_estado.pack()
        self.campo_estado.current(0)

        moldura_botoes = ttk.Frame(moldura)
        moldura_botoes.pack(pady=(15, 0))
        ttk.Button(moldura_botoes, text="Guardar", command=self._guardar).pack(side="left", padx=5)
        ttk.Button(moldura_botoes, text="Cancelar", command=self.destroy).pack(side="left", padx=5)

    def _guardar(self):
        novo_estado = self.campo_estado.get()
        database.atualizar_estado_leitura(self.livro_id, novo_estado)
        self.janela_principal.atualizar_lista()
        self.destroy()


def main():
    app = JanelaPrincipal()
    app.mainloop()


if __name__ == "__main__":
    main()
