import re
import sqlite3
import unicodedata

DB_NAME = "biblioteca.db"


def normalize_text(texto):
    """
    Normaliza texto para comparação/pesquisa insensível a acentos, maiúsculas e pontuação.
    Ex.: "É, Um Ólá!" -> "e um ola"
    """
    if texto is None:
        return ""

    # NFKD decompõe caracteres acentuados em (letra base + marca de acento separada)
    texto = unicodedata.normalize("NFKD", texto)
    # unicodedata.combining() identifica essas marcas de acento; filtramo-las fora
    texto = "".join(c for c in texto if not unicodedata.combining(c))

    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)  # remove pontuação, mantém letras/números/espaços
    texto = re.sub(r"\s+", " ", texto).strip()  # colapsa espaços múltiplos

    return texto


def connect():
    """Abre ligação à base de dados e ativa verificação de chaves estrangeiras."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite não valida FKs por omissão
    conn.row_factory = sqlite3.Row  # permite aceder às colunas por nome e converter para dict()
    return conn


def create_tables():
    """Cria as tabelas se ainda não existirem. Seguro chamar repetidamente."""
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY,
            titulo TEXT NOT NULL,
            editora TEXT,
            colecao TEXT,
            genero TEXT,
            isbn TEXT UNIQUE,
            estado_leitura TEXT NOT NULL DEFAULT 'não lido'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS autores (
            id INTEGER PRIMARY KEY,
            nome TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS livro_autor (
            livro_id INTEGER NOT NULL,
            autor_id INTEGER NOT NULL,
            PRIMARY KEY (livro_id, autor_id),
            FOREIGN KEY (livro_id) REFERENCES livros(id),
            FOREIGN KEY (autor_id) REFERENCES autores(id)
        )
    """)

    # Migração: se a base de dados já existia antes desta coluna ser introduzida,
    # o CREATE TABLE IF NOT EXISTS acima não a adiciona (só corre em tabelas novas).
    cursor.execute("PRAGMA table_info(livros)")
    colunas_existentes = [linha[1] for linha in cursor.fetchall()]
    if "estado_leitura" not in colunas_existentes:
        cursor.execute(
            "ALTER TABLE livros ADD COLUMN estado_leitura TEXT NOT NULL DEFAULT 'não lido'"
        )

    conn.commit()
    conn.close()


def get_or_create_author(cursor, nome):
    """Devolve o id do autor. Se não existir (comparação insensível a maiúsculas), cria-o."""
    cursor.execute(
        "SELECT id FROM autores WHERE LOWER(nome) = LOWER(?)", (nome,)
    )
    resultado = cursor.fetchone()

    if resultado:
        return resultado[0]  # autor já existia

    cursor.execute("INSERT INTO autores (nome) VALUES (?)", (nome,))
    return cursor.lastrowid  # id do autor recém-criado


def add_book(titulo, editora, colecao, genero, isbn, autores_str, estado_leitura="não lido"):
    """
    Insere um livro e associa-o aos seus autores.
    autores_str: nomes separados por vírgula, ex. "Fabcaro, Conrad"
    """
    autores = [nome.strip() for nome in autores_str.split(",") if nome.strip()]

    conn = connect()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO livros (titulo, editora, colecao, genero, isbn, estado_leitura)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (titulo, editora, colecao, genero, isbn, estado_leitura))
    except sqlite3.IntegrityError:
        print(f"Este livro já existe na biblioteca (ISBN '{isbn}' duplicado).")
        conn.close()
        return None

    livro_id = cursor.lastrowid

    for nome_autor in autores:
        autor_id = get_or_create_author(cursor, nome_autor)
        cursor.execute("""
            INSERT INTO livro_autor (livro_id, autor_id) VALUES (?, ?)
        """, (livro_id, autor_id))

    conn.commit()
    conn.close()
    return livro_id


def list_books():
    """
    Devolve todos os livros como uma lista de dicionários, ordenados por título.
    Cada dicionário inclui os autores associados numa única string (separados por vírgula).
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            livros.id,
            livros.titulo,
            livros.editora,
            livros.colecao,
            livros.genero,
            livros.isbn,
            livros.estado_leitura,
            GROUP_CONCAT(autores.nome, ', ') AS autores
        FROM livros
        LEFT JOIN livro_autor ON livros.id = livro_autor.livro_id
        LEFT JOIN autores ON livro_autor.autor_id = autores.id
        GROUP BY livros.id
        ORDER BY livros.titulo
    """)

    resultados = cursor.fetchall()
    conn.close()

    return [dict(linha) for linha in resultados]


def search_books(termo):
    """
    Pesquisa livros por título, editora ou nome de autor, ignorando acentos,
    maiúsculas e pontuação (usa normalize_text nos dois lados da comparação).
    Devolve a mesma estrutura que list_books(): lista de dicionários.

    Nota de implementação: a filtragem (WHERE) é feita numa subquery que só
    identifica os IDs dos livros correspondentes. A query exterior volta a
    fazer o JOIN completo a partir desses IDs, sem WHERE, para que o
    GROUP_CONCAT agregue TODOS os autores do livro — não apenas o autor que
    coincidiu com o termo de pesquisa.
    """
    termo_normalizado = normalize_text(termo)

    conn = connect()
    # regista normalize_text como função SQL "normalizar", utilizável dentro da query
    conn.create_function("normalizar", 1, normalize_text)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            livros.id,
            livros.titulo,
            livros.editora,
            livros.colecao,
            livros.genero,
            livros.isbn,
            livros.estado_leitura,
            GROUP_CONCAT(autores.nome, ', ') AS autores
        FROM livros
        LEFT JOIN livro_autor ON livros.id = livro_autor.livro_id
        LEFT JOIN autores ON livro_autor.autor_id = autores.id
        WHERE livros.id IN (
            SELECT livros.id
            FROM livros
            LEFT JOIN livro_autor ON livros.id = livro_autor.livro_id
            LEFT JOIN autores ON livro_autor.autor_id = autores.id
            WHERE normalizar(livros.titulo) LIKE '%' || ? || '%'
               OR normalizar(livros.editora) LIKE '%' || ? || '%'
               OR normalizar(autores.nome) LIKE '%' || ? || '%'
        )
        GROUP BY livros.id
        ORDER BY livros.titulo
    """, (termo_normalizado, termo_normalizado, termo_normalizado))

    resultados = cursor.fetchall()
    conn.close()

    return [dict(linha) for linha in resultados]


def update_book(livro_id, titulo=None, editora=None, colecao=None, genero=None, isbn=None, autores_str=None, estado_leitura=None):
    """
    Atualiza os campos fornecidos de um livro existente, identificado por livro_id.
    Campos não fornecidos (None) mantêm o valor atual — permite atualizações parciais,
    ex. update_book(1, isbn="novo-isbn") só muda o ISBN.

    Se autores_str for fornecido, substitui COMPLETAMENTE a lista de autores associados
    (mesmo formato do add_book: nomes separados por vírgula).

    Devolve True se o livro foi encontrado e atualizado, False caso contrário.
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM livros WHERE id = ?", (livro_id,))
    livro_atual = cursor.fetchone()

    if livro_atual is None:
        print(f"Livro com id {livro_id} não encontrado.")
        conn.close()
        return False

    novo_titulo = titulo if titulo is not None else livro_atual["titulo"]
    novo_editora = editora if editora is not None else livro_atual["editora"]
    novo_colecao = colecao if colecao is not None else livro_atual["colecao"]
    novo_genero = genero if genero is not None else livro_atual["genero"]
    novo_isbn = isbn if isbn is not None else livro_atual["isbn"]
    novo_estado_leitura = estado_leitura if estado_leitura is not None else livro_atual["estado_leitura"]

    try:
        cursor.execute("""
            UPDATE livros
            SET titulo = ?, editora = ?, colecao = ?, genero = ?, isbn = ?, estado_leitura = ?
            WHERE id = ?
        """, (novo_titulo, novo_editora, novo_colecao, novo_genero, novo_isbn, novo_estado_leitura, livro_id))
    except sqlite3.IntegrityError:
        print(f"Não foi possível atualizar: o ISBN '{novo_isbn}' já pertence a outro livro.")
        conn.close()
        return False

    if autores_str is not None:
        autores = [nome.strip() for nome in autores_str.split(",") if nome.strip()]
        cursor.execute("DELETE FROM livro_autor WHERE livro_id = ?", (livro_id,))
        for nome_autor in autores:
            autor_id = get_or_create_author(cursor, nome_autor)
            cursor.execute("""
                INSERT INTO livro_autor (livro_id, autor_id) VALUES (?, ?)
            """, (livro_id, autor_id))

    conn.commit()
    conn.close()
    return True


def delete_book(livro_id):
    """
    Remove um livro e as suas associações a autores (linhas em livro_autor).
    Os autores em si NÃO são removidos, mesmo que fiquem sem nenhum livro associado
    (decisão deliberada: preserva o registo do autor para reutilização futura).

    Devolve True se o livro existia e foi removido, False se o id não existia.
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM livro_autor WHERE livro_id = ?", (livro_id,))
    cursor.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
    livro_existia = cursor.rowcount > 0

    conn.commit()
    conn.close()

    return livro_existia


if __name__ == "__main__":
    create_tables()
    print("Base de dados e tabelas criadas com sucesso.")
