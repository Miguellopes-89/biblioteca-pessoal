# database.py
#
# Este módulo é a única parte do programa que fala diretamente com a
# base de dados SQLite. Isto é uma escolha deliberada: se um dia
# quisermos trocar SQLite por outra base de dados, ou mudar a forma
# como as tabelas estão desenhadas, só precisamos de mexer aqui — o
# resto do programa (o menu, cli.py) não precisa de saber como os
# dados são guardados, só precisa de chamar estas funções.

import sqlite3
import unicodedata
from pathlib import Path

from constantes import ESTADOS_LEITURA, LIMITE_NOTA
from metadados_isbn import normalizar_isbn

# Caminho para o ficheiro da base de dados. Path(__file__).parent dá-nos
# a pasta onde este ficheiro está, e juntamos "data/biblioteca.db" a
# seguir. Assim, não importa de onde corres o programa — o caminho para
# a base de dados está sempre correto.
CAMINHO_BD = Path(__file__).parent / "data" / "biblioteca.db"


def normalizar_texto(texto):
    """
    Remove acentos e converte para minúsculas, para permitir pesquisas
    que ignoram tanto a capitalização como a acentuação — ex.: procurar
    "meditacoes" encontra "Meditações", "sao paulo" encontra "São Paulo".

    Funciona decompondo cada letra acentuada nas suas partes: a letra
    base + o sinal diacrítico (ex.: 'ç' vira 'c' + cedilha, 'õ' vira
    'o' + til). A categoria Unicode 'Mn' ("Mark, nonspacing") identifica
    esses sinais, que descartamos, ficando só com as letras base. Esta
    técnica funciona para qualquer acento latino (português, espanhol,
    francês, alemão, etc.) sem precisarmos de listar caracteres à mão.
    """
    sem_acentos = unicodedata.normalize("NFKD", texto)
    sem_acentos = "".join(c for c in sem_acentos if unicodedata.category(c) != "Mn")
    return sem_acentos.lower()


def obter_ligacao():
    """
    Abre e devolve uma ligação à base de dados.

    row_factory = sqlite3.Row faz com que cada linha devolvida por uma
    consulta se comporte como um dicionário (podemos escrever linha["titulo"]
    em vez de termos de saber a posição numérica de cada coluna). Isto
    torna o código que usa estes dados muito mais legível.
    """
    ligacao = sqlite3.connect(CAMINHO_BD)
    ligacao.row_factory = sqlite3.Row
    return ligacao


def criar_tabela():
    """
    Cria a tabela 'livros' se ainda não existir. É seguro chamar esta
    função sempre que o programa arranca — "CREATE TABLE IF NOT EXISTS"
    não faz nada se a tabela já lá estiver.

    Nota sobre o CHECK do estado_leitura: como só existem três estados
    possíveis e não esperamos que essa lista cresça (ao contrário dos
    géneros), faz sentido a base de dados garantir essa regra por si
    própria, e não só a aplicação.
    """
    # Nota técnica: o SQLite não permite usar parâmetros (o "?" que
    # usamos nas outras funções para evitar SQL injection) dentro de
    # CHECK constraints — só aceita valores literais escritos na
    # própria instrução SQL. Como LIMITE_NOTA vem de constantes.py (não
    # é escrito pelo utilizador), é seguro inseri-lo diretamente na
    # string com um f-string.
    ligacao = obter_ligacao()
    ligacao.execute(
        f"""
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            autor TEXT NOT NULL,
            isbn TEXT,
            genero TEXT NOT NULL,
            estado_leitura TEXT NOT NULL CHECK (estado_leitura IN ('lido', 'a ler', 'por ler')),
            nota TEXT CHECK (length(nota) <= {LIMITE_NOTA}),
            data_adicionado TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    ligacao.commit()
    ligacao.close()


def adicionar_livro(titulo, autor, genero, estado_leitura, isbn=None, nota=None):
    """
    Insere um novo livro na base de dados.

    isbn e nota são opcionais (podem ficar a None / vazio), tudo o
    resto é obrigatório. Devolve o id do livro recém-criado, que é
    útil se quisermos, por exemplo, confirmar ao utilizador ou usá-lo
    logo a seguir noutra operação.

    O ISBN é normalizado (hífens e espaços removidos, via
    normalizar_isbn() de metadados_isbn.py) antes de ser guardado.
    Sem isto, "978-989-23-1234-5" e "9789892312345" ficariam gravados
    como valores diferentes, mesmo sendo o mesmo número — o que
    tornaria a deteção de duplicados em buscar_livro_por_isbn() pouco
    fiável. Reutilizamos a mesma função que já usávamos só para
    pesquisa, para não ter duas normalizações de ISBN divergentes no
    projeto.
    """
    if estado_leitura not in ESTADOS_LEITURA:
        raise ValueError(f"Estado de leitura inválido: {estado_leitura}")

    isbn_normalizado = normalizar_isbn(isbn) if isbn else None

    ligacao = obter_ligacao()
    cursor = ligacao.execute(
        """
        INSERT INTO livros (titulo, autor, isbn, genero, estado_leitura, nota)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (titulo, autor, isbn_normalizado, genero, estado_leitura, nota),
    )
    ligacao.commit()
    novo_id = cursor.lastrowid
    ligacao.close()
    return novo_id


def buscar_livro_por_isbn(isbn):
    """
    Devolve o livro já existente com este ISBN, ou None se não houver
    nenhum. isbn é normalizado antes da procura, pelo mesmo motivo de
    adicionar_livro() — para que "978-989-23-1234-5" encontre um
    livro gravado como "9789892312345".

    Usada para avisar o utilizador de um possível duplicado antes de
    gravar um livro novo. Propositadamente não impede a inserção (não
    há UNIQUE na coluna isbn): o ADR-001 já rejeitou "formatos
    duplicados" como cenário real desta biblioteca, mas nada impede
    que o utilizador tenha mesmo duas cópias físicas do mesmo livro —
    um bloqueio rígido tiraria essa possibilidade. Quem decide é o
    utilizador, avisado; a base de dados não decide por ele.
    """
    if not isbn:
        return None

    isbn_normalizado = normalizar_isbn(isbn)
    if not isbn_normalizado:
        return None

    ligacao = obter_ligacao()
    linha = ligacao.execute(
        "SELECT * FROM livros WHERE isbn = ?", (isbn_normalizado,)
    ).fetchone()
    ligacao.close()
    return linha


def listar_livros(estado_leitura=None):
    """
    Devolve todos os livros, ou só os que têm um determinado estado de
    leitura, se esse filtro for indicado. Os resultados vêm ordenados
    alfabeticamente pelo título.
    """
    ligacao = obter_ligacao()
    if estado_leitura:
        linhas = ligacao.execute(
            "SELECT * FROM livros WHERE estado_leitura = ? ORDER BY titulo COLLATE NOCASE",
            (estado_leitura,),
        ).fetchall()
    else:
        linhas = ligacao.execute(
            "SELECT * FROM livros ORDER BY titulo COLLATE NOCASE"
        ).fetchall()
    ligacao.close()
    return linhas


def procurar_livros(termo):
    """
    Procura livros cujo título ou autor contenham o termo de pesquisa,
    ignorando maiúsculas/minúsculas e acentos.

    Nota de arquitetura: em vez de fazer esta comparação em SQL (como
    fazíamos antes com LIKE), trazemos todos os livros para a memória
    do programa e filtramos aqui em Python usando normalizar_texto().
    O SQLite não tem, de fábrica, uma forma de ignorar acentos numa
    pesquisa — só sabe comparar bytes. Para uma biblioteca pessoal
    (dezenas ou centenas de livros, não milhões), filtrar em Python
    é perfeitamente rápido e muito mais simples do que configurar
    extensões SQLite para lidar com acentuação.
    """
    termo_normalizado = normalizar_texto(termo)

    ligacao = obter_ligacao()
    todos_os_livros = ligacao.execute(
        "SELECT * FROM livros ORDER BY titulo COLLATE NOCASE"
    ).fetchall()
    ligacao.close()

    return [
        livro
        for livro in todos_os_livros
        if termo_normalizado in normalizar_texto(livro["titulo"])
        or termo_normalizado in normalizar_texto(livro["autor"])
    ]


def atualizar_estado_leitura(livro_id, novo_estado):
    """Muda o estado de leitura de um livro já existente."""
    if novo_estado not in ESTADOS_LEITURA:
        raise ValueError(f"Estado de leitura inválido: {novo_estado}")

    ligacao = obter_ligacao()
    ligacao.execute(
        "UPDATE livros SET estado_leitura = ? WHERE id = ?",
        (novo_estado, livro_id),
    )
    ligacao.commit()
    ligacao.close()


def remover_livro(livro_id):
    """Remove um livro da base de dados pelo seu id."""
    ligacao = obter_ligacao()
    ligacao.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
    ligacao.commit()
    ligacao.close()
