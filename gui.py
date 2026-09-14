import sys
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFormLayout,
    QLineEdit, QPushButton, QMessageBox, QComboBox,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
)

from database import add_book, create_tables, list_books, update_book, delete_book, search_books
from isbn_lookup import lookup_isbn


class PesquisaISBNThread(QThread):
    """Corre lookup_isbn() num thread à parte, para não bloquear a GUI
    enquanto se espera pela resposta da rede (pode demorar vários
    segundos, sobretudo com as repetições em isbn_lookup.py).

    resultado_pronto emite o dict devolvido por lookup_isbn(), ou None
    se não foi encontrado nada em nenhuma das APIs.
    """
    resultado_pronto = Signal(object)

    def __init__(self, isbn):
        super().__init__()
        self.isbn = isbn

    def run(self):
        resultado = lookup_isbn(self.isbn)
        self.resultado_pronto.emit(resultado)


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Biblioteca Pessoal")
        self.resize(800, 600)

        # None = modo "adicionar novo livro"; um id = modo "a editar este livro"
        self.livro_selecionado_id = None

        # Referência ao thread de pesquisa ISBN em curso (None = nenhum a correr).
        # Tem de ficar guardada num atributo da instância, não numa variável local:
        # se não houver nenhuma referência viva, o Python recolhe o objeto (garbage
        # collection) a meio da execução do thread, e a app rebenta sem aviso.
        self.thread_pesquisa_isbn = None

        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        self.campo_titulo = QLineEdit()
        self.campo_autores = QLineEdit()
        self.campo_editora = QLineEdit()
        self.campo_colecao = QLineEdit()
        self.campo_genero = QLineEdit()
        self.campo_isbn = QLineEdit()
        self.campo_estado_leitura = QComboBox()
        self.campo_estado_leitura.addItems(["não lido", "a ler", "lido"])
        self.campo_autores.setPlaceholderText("separados por vírgula, ex.: Fabcaro, Conrad")

        # --- Campo ISBN + botão de procura ---
        self.botao_procurar_isbn = QPushButton("Procurar")
        self.botao_procurar_isbn.clicked.connect(self.pesquisar_isbn)

        isbn_layout = QHBoxLayout()
        isbn_layout.addWidget(self.campo_isbn)
        isbn_layout.addWidget(self.botao_procurar_isbn)

        self.botao_adicionar = QPushButton("Adicionar Livro")
        self.botao_adicionar.clicked.connect(self.guardar_livro)

        self.botao_remover = QPushButton("Remover Livro")
        self.botao_remover.clicked.connect(self.remover_livro)

        botoes_layout = QHBoxLayout()
        botoes_layout.addWidget(self.botao_adicionar)
        botoes_layout.addWidget(self.botao_remover)

        # --- Formulário ---
        form_layout = QFormLayout()
        form_layout.addRow("Título:", self.campo_titulo)
        form_layout.addRow("Autores:", self.campo_autores)
        form_layout.addRow("Editora:", self.campo_editora)
        form_layout.addRow("Coleção:", self.campo_colecao)
        form_layout.addRow("Género:", self.campo_genero)
        form_layout.addRow("ISBN:", isbn_layout)
        form_layout.addRow("Estado de leitura:", self.campo_estado_leitura)
        form_layout.addRow(botoes_layout)

        # --- Pesquisa ---
        self.campo_pesquisa = QLineEdit()
        self.campo_pesquisa.setPlaceholderText("Pesquisar por título, editora ou autor...")
        self.campo_pesquisa.returnPressed.connect(self.executar_pesquisa)

        self.botao_pesquisar = QPushButton("Pesquisar")
        self.botao_pesquisar.clicked.connect(self.executar_pesquisa)

        self.botao_limpar_pesquisa = QPushButton("Limpar")
        self.botao_limpar_pesquisa.clicked.connect(self.limpar_pesquisa)

        pesquisa_layout = QHBoxLayout()
        pesquisa_layout.addWidget(self.campo_pesquisa)
        pesquisa_layout.addWidget(self.botao_pesquisar)
        pesquisa_layout.addWidget(self.botao_limpar_pesquisa)

        # --- Tabela de listagem ---
        self.tabela_livros = QTableWidget()
        colunas = ["ID", "Título", "Autores", "Editora", "Coleção", "Género", "ISBN", "Estado"]
        self.tabela_livros.setColumnCount(len(colunas))
        self.tabela_livros.setHorizontalHeaderLabels(colunas)
        self.tabela_livros.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # só leitura, por agora
        self.tabela_livros.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela_livros.itemSelectionChanged.connect(self.linha_selecionada)

        # ID encolhe ao mínimo necessário; Título ocupa o espaço sobrante (é o
        # campo mais variável em comprimento); as restantes ajustam-se ao conteúdo.
        cabecalho = self.tabela_livros.horizontalHeader()
        cabecalho.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for coluna in range(2, len(colunas)):
            cabecalho.setSectionResizeMode(coluna, QHeaderView.ResizeMode.ResizeToContents)

        # --- Junta tudo num layout vertical: formulário, pesquisa, tabela ---
        layout_principal = QVBoxLayout()
        layout_principal.addLayout(form_layout)
        layout_principal.addLayout(pesquisa_layout)
        layout_principal.addWidget(self.tabela_livros)
        widget_central.setLayout(layout_principal)

        self.atualizar_tabela()

    def pesquisar_isbn(self):
        isbn = self.campo_isbn.text().strip()
        if not isbn:
            QMessageBox.warning(self, "ISBN em falta", "Escreve um ISBN no campo antes de procurar.")
            return

        # Evita lançar uma segunda pesquisa enquanto a primeira ainda está a correr
        if self.thread_pesquisa_isbn is not None and self.thread_pesquisa_isbn.isRunning():
            return

        self.botao_procurar_isbn.setEnabled(False)
        self.botao_procurar_isbn.setText("A procurar...")

        self.thread_pesquisa_isbn = PesquisaISBNThread(isbn)
        self.thread_pesquisa_isbn.resultado_pronto.connect(self.ao_receber_resultado_isbn)
        self.thread_pesquisa_isbn.start()

    def ao_receber_resultado_isbn(self, resultado):
        self.botao_procurar_isbn.setEnabled(True)
        self.botao_procurar_isbn.setText("Procurar")

        if resultado is None:
            QMessageBox.information(
                self, "Não encontrado",
                "Não foi possível encontrar este ISBN (nem na Google Books, nem na Open Library). "
                "Podes continuar a preencher o formulário manualmente.",
            )
            return

        # Só preenche os campos que a API efetivamente devolveu com conteúdo;
        # campos que a API não tem (ex.: coleção) ficam tal como estavam.
        if resultado["titulo"]:
            self.campo_titulo.setText(resultado["titulo"])
        if resultado["autores_str"]:
            self.campo_autores.setText(resultado["autores_str"])
        if resultado["editora"]:
            self.campo_editora.setText(resultado["editora"])
        if resultado["genero"]:
            self.campo_genero.setText(resultado["genero"])

    def linha_selecionada(self):
        # Usar selectedItems() em vez de currentRow(): clearSelection() dispara
        # este mesmo sinal (itemSelectionChanged), mas currentRow() continua a
        # apontar para a última célula em foco mesmo sem nada selecionado.
        # Sem esta verificação, limpar_campos() ao chamar clearSelection()
        # reentraria aqui e repunha o modo edição imediatamente a seguir a saíres dele.
        if not self.tabela_livros.selectedItems():
            return

        linha_atual = self.tabela_livros.currentRow()
        if linha_atual < 0:
            return

        self.livro_selecionado_id = int(self.tabela_livros.item(linha_atual, 0).text())
        self.campo_titulo.setText(self.tabela_livros.item(linha_atual, 1).text())
        self.campo_autores.setText(self.tabela_livros.item(linha_atual, 2).text())
        self.campo_editora.setText(self.tabela_livros.item(linha_atual, 3).text())
        self.campo_colecao.setText(self.tabela_livros.item(linha_atual, 4).text())
        self.campo_genero.setText(self.tabela_livros.item(linha_atual, 5).text())
        self.campo_isbn.setText(self.tabela_livros.item(linha_atual, 6).text())
        self.campo_estado_leitura.setCurrentText(self.tabela_livros.item(linha_atual, 7).text())

        self.botao_adicionar.setText("Guardar Alterações")

    def guardar_livro(self):
        titulo = self.campo_titulo.text().strip()

        if not titulo:
            QMessageBox.warning(self, "Campo obrigatório", "O título não pode ficar vazio.")
            return

        editora = self.campo_editora.text().strip()
        colecao = self.campo_colecao.text().strip()
        genero = self.campo_genero.text().strip()
        isbn = self.campo_isbn.text().strip()
        autores_str = self.campo_autores.text().strip()
        estado_leitura = self.campo_estado_leitura.currentText()

        if self.livro_selecionado_id is None:
            # --- Modo adicionar ---
            livro_id = add_book(
                titulo=titulo, editora=editora, colecao=colecao, genero=genero,
                isbn=isbn, autores_str=autores_str, estado_leitura=estado_leitura,
            )
            if livro_id is None:
                QMessageBox.warning(self, "ISBN duplicado", "Já existe um livro com este ISBN na biblioteca.")
                return
            QMessageBox.information(self, "Sucesso", f"Livro adicionado (id {livro_id}).")
        else:
            # --- Modo edição ---
            sucesso = update_book(
                self.livro_selecionado_id, titulo=titulo, editora=editora, colecao=colecao,
                genero=genero, isbn=isbn, autores_str=autores_str, estado_leitura=estado_leitura,
            )
            if not sucesso:
                QMessageBox.warning(self, "Erro ao atualizar", "Não foi possível atualizar (ISBN já usado por outro livro?).")
                return
            QMessageBox.information(self, "Sucesso", "Livro atualizado.")

        self.limpar_campos()
        self.atualizar_tabela()

    def remover_livro(self):
        if self.livro_selecionado_id is None:
            QMessageBox.warning(self, "Nenhum livro selecionado", "Seleciona um livro na tabela para remover.")
            return

        resposta = QMessageBox.question(
            self, "Confirmar remoção",
            f"Remover o livro '{self.campo_titulo.text()}'? Esta ação não pode ser desfeita.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return

        delete_book(self.livro_selecionado_id)
        self.limpar_campos()
        self.atualizar_tabela()

    def limpar_campos(self):
        self.campo_titulo.clear()
        self.campo_autores.clear()
        self.campo_editora.clear()
        self.campo_colecao.clear()
        self.campo_genero.clear()
        self.campo_isbn.clear()
        self.campo_estado_leitura.setCurrentIndex(0)  # volta a "não lido"
        self.livro_selecionado_id = None
        self.botao_adicionar.setText("Adicionar Livro")
        self.tabela_livros.clearSelection()

    def executar_pesquisa(self):
        termo = self.campo_pesquisa.text().strip()
        if not termo:
            self.atualizar_tabela()
            return
        self.preencher_tabela(search_books(termo))

    def limpar_pesquisa(self):
        self.campo_pesquisa.clear()
        self.atualizar_tabela()

    def atualizar_tabela(self):
        self.preencher_tabela(list_books())

    def preencher_tabela(self, livros):
        self.tabela_livros.setRowCount(len(livros))

        for linha, livro in enumerate(livros):
            self.tabela_livros.setItem(linha, 0, QTableWidgetItem(str(livro["id"])))
            self.tabela_livros.setItem(linha, 1, QTableWidgetItem(livro["titulo"]))
            self.tabela_livros.setItem(linha, 2, QTableWidgetItem(livro["autores"] or ""))
            self.tabela_livros.setItem(linha, 3, QTableWidgetItem(livro["editora"] or ""))
            self.tabela_livros.setItem(linha, 4, QTableWidgetItem(livro["colecao"] or ""))
            self.tabela_livros.setItem(linha, 5, QTableWidgetItem(livro["genero"] or ""))
            self.tabela_livros.setItem(linha, 6, QTableWidgetItem(livro["isbn"] or ""))
            self.tabela_livros.setItem(linha, 7, QTableWidgetItem(livro["estado_leitura"]))


if __name__ == "__main__":
    create_tables()  # garante que as tabelas existem antes da app arrancar
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())
