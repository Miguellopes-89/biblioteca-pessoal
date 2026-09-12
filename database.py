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


if __name__ == "__main__":
    create_tables()
    print("Base de dados e tabelas criadas com sucesso.")
