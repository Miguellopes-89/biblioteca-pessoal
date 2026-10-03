"""web/app.py — servidor Flask que reutiliza a lógica de negócio já existente
(database.py, isbn_lookup.py) sem qualquer alteração. Serve a mesma base de
dados SQLite que a app desktop (gui.py) usa — não é uma cópia dos dados,
é a mesma base de dados, vista a partir de outra interface.

Corre-se com:

    python web/app.py

Nota: desde que database.py passou a usar um caminho absoluto para
"biblioteca.db", já não importa a pasta de onde este comando é lançado —
a base de dados é sempre a mesma que a app desktop usa.
"""

import os
import sys

# database.py e isbn_lookup.py estão na pasta-mãe (raiz do projeto), não
# dentro de web/. Sem esta linha, o Python não os encontra ao correr este
# ficheiro a partir da subpasta web/.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, redirect, render_template, request, url_for

from database import add_book, create_tables, delete_book, get_book, list_books, search_books, update_book
from isbn_lookup import lookup_isbn, validar_isbn

app = Flask(__name__)


@app.route("/")
def index():
    """Página inicial: lista todos os livros, ou os resultados da pesquisa
    se houver um termo em ?q=... na URL.

    GET (não POST) é a escolha certa aqui: pesquisar não cria nem altera
    nada, e ter o termo na URL (em vez de num formulário POST) torna o
    resultado pesquisável, partilhável e sujeito ao botão "recuar" do
    browser, tal como uma pesquisa no Google.
    """
    termo = request.args.get("q", "").strip()
    livros = search_books(termo) if termo else list_books()
    return render_template("index.html", livros=livros, termo=termo)


@app.route("/pesquisar-isbn")
def pesquisar_isbn():
    """Endpoint JSON chamado por fetch() a partir do botão "Procurar" em
    adicionar.html. Reutiliza validar_isbn() e lookup_isbn() sem qualquer
    alteração — exatamente a mesma lógica da GUI, só sem QThread: este
    pedido HTTP fica bloqueado até a cascata Google Books -> Open Library
    (com as suas repetições) terminar.

    Não chama baixar_capa(): ao contrário da GUI (que precisa dos bytes
    para um QPixmap), o browser consegue carregar a imagem diretamente a
    partir de capa_url num <img src="...">, sem passar pelo servidor.

    Usa códigos de estado HTTP (400/404) em vez de um campo "encontrado"
    no corpo — o JavaScript em adicionar.html já verifica resposta.ok.
    """
    isbn = request.args.get("isbn", "").strip()

    if not isbn:
        return {"erro": "Escreve um ISBN no campo antes de procurar."}, 400

    if not validar_isbn(isbn):
        return {
            "erro": "Este ISBN não tem um dígito de controlo válido — confirma se não há nenhum algarismo trocado.",
        }, 400

    resultado = lookup_isbn(isbn)
    if resultado is None:
        return {
            "erro": "Não foi possível encontrar este ISBN (nem na Google Books, nem na Open Library).",
        }, 404

    # Flask converte um dict devolvido diretamente numa resposta JSON,
    # sem precisar de chamar jsonify() explicitamente.
    return resultado


@app.route("/adicionar", methods=["GET", "POST"])
def adicionar():
    """GET: mostra o formulário vazio. POST: processa o que foi submetido.

    O mesmo padrão de preenchimento parcial da GUI aplica-se aqui: campos
    vazios no formulário (editora, colecao, genero, isbn) são convertidos
    para None antes de chegar a add_book(), tal como database.py espera.
    """
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autores_str = request.form.get("autores_str", "").strip()
        editora = request.form.get("editora", "").strip() or None
        colecao = request.form.get("colecao", "").strip() or None
        genero = request.form.get("genero", "").strip() or None
        isbn = request.form.get("isbn", "").strip() or None
        estado_leitura = request.form.get("estado_leitura", "não lido")

        if not titulo:
            return render_template("adicionar.html", erro="O título não pode ficar vazio.")

        livro_id = add_book(
            titulo=titulo, editora=editora, colecao=colecao, genero=genero,
            isbn=isbn, autores_str=autores_str, estado_leitura=estado_leitura,
        )
        if livro_id is None:
            return render_template("adicionar.html", erro="Já existe um livro com este ISBN na biblioteca.")

        # Redirect (em vez de render_template direto) evita reenviar o
        # formulário se o utilizador atualizar a página (F5) depois de
        # adicionar — sem isto, o browser reenviaria o POST outra vez.
        return redirect(url_for("index"))

    return render_template("adicionar.html", erro=None)


@app.route("/livros/<int:livro_id>/editar", methods=["GET", "POST"])
def editar(livro_id: int):
    """<int:livro_id> na rota captura o número da URL e entrega-o aqui
    como argumento — é assim que sabemos QUAL livro estamos a editar,
    sem depender de uma seleção prévia numa tabela (como na GUI).
    """
    livro = get_book(livro_id)
    if livro is None:
        return "Livro não encontrado", 404

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autores_str = request.form.get("autores_str", "").strip()
        editora = request.form.get("editora", "").strip() or None
        colecao = request.form.get("colecao", "").strip() or None
        genero = request.form.get("genero", "").strip() or None
        isbn = request.form.get("isbn", "").strip() or None
        estado_leitura = request.form.get("estado_leitura", "não lido")

        if not titulo:
            return render_template("editar.html", livro=livro, erro="O título não pode ficar vazio.")

        sucesso = update_book(
            livro_id, titulo=titulo, editora=editora, colecao=colecao,
            genero=genero, isbn=isbn, autores_str=autores_str, estado_leitura=estado_leitura,
        )
        if not sucesso:
            return render_template(
                "editar.html", livro=livro,
                erro="Não foi possível atualizar (ISBN já usado por outro livro?).",
            )

        return redirect(url_for("index"))

    return render_template("editar.html", livro=livro, erro=None)


@app.route("/livros/<int:livro_id>/remover", methods=["POST"])
def remover(livro_id: int):
    """Só aceita POST, nunca GET — uma ação destrutiva nunca deve poder
    ser disparada por um simples link ou por um crawler a seguir URLs.
    A confirmação (equivalente ao QMessageBox.question da GUI) fica do
    lado do template, com um confirm() de JavaScript antes de submeter.
    """
    delete_book(livro_id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    create_tables()  # garante que as tabelas existem, tal como faz gui.py
    app.run(debug=True)
