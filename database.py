import sqlite3

DB_NAME = "biblioteca.db"


def connect():
    """Abre ligação à base de dados e ativa verificação de chaves estrangeiras."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite não valida FKs por omissão
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
            isbn TEXT UNIQUE
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


def add_book(titulo, editora, colecao, genero, isbn, autores_str):
    """
    Insere um livro e associa-o aos seus autores.
    autores_str: nomes separados por vírgula, ex. "Fabcaro, Conrad"
    """
    autores = [nome.strip() for nome in autores_str.split(",") if nome.strip()]

    conn = connect()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO livros (titulo, editora, colecao, genero, isbn)
            VALUES (?, ?, ?, ?, ?)
        """, (titulo, editora, colecao, genero, isbn))
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


if __name__ == "__main__":
    create_tables()
    print("Base de dados e tabelas criadas com sucesso.")
