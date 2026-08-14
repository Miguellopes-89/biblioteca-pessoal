# tests/test_database.py
#
# Testes para database.py: esquema, CRUD e as regras de negócio que
# vivem tanto em Python (ValueError para estados inválidos) como na
# própria base de dados (CHECK constraints).

import sqlite3

import pytest

import database
from constantes import LIMITE_NOTA


# --- criar_tabela --------------------------------------------------

def test_criar_tabela_e_idempotente(bd_temporaria):
    """Chamar criar_tabela() outra vez não deve rebentar nem apagar dados."""
    database.adicionar_livro("Livro Teste", "Autor Teste", "Ficção", "por ler")
    database.criar_tabela()  # segunda chamada, não deve fazer nada
    assert len(database.listar_livros()) == 1


# --- adicionar_livro -------------------------------------------------

def test_adicionar_livro_devolve_id(bd_temporaria):
    id_livro = database.adicionar_livro("1984", "George Orwell", "Ficção Científica", "lido")
    assert isinstance(id_livro, int)
    assert id_livro > 0


def test_adicionar_livro_campos_opcionais_ausentes(bd_temporaria):
    """isbn e nota são opcionais — devem poder ficar None."""
    id_livro = database.adicionar_livro("Livro Sem ISBN", "Autor X", "Ensaio", "a ler")
    livro = database.listar_livros()[0]
    assert livro["id"] == id_livro
    assert livro["isbn"] is None
    assert livro["nota"] is None


def test_adicionar_livro_estado_invalido_lanca_valueerror(bd_temporaria):
    with pytest.raises(ValueError):
        database.adicionar_livro("Livro X", "Autor X", "Ensaio", "a meio")


def test_bd_rejeita_estado_leitura_invalido_diretamente(bd_temporaria):
    """
    Confirma que a regra não depende só do ValueError em Python — a
    CHECK constraint da própria tabela também protege os dados, mesmo
    que alguém insira via SQL direto (ex.: um script de migração).
    """
    ligacao = database.obter_ligacao()
    with pytest.raises(sqlite3.IntegrityError):
        ligacao.execute(
            "INSERT INTO livros (titulo, autor, genero, estado_leitura) VALUES (?, ?, ?, ?)",
            ("Livro X", "Autor X", "Ensaio", "estado_inventado"),
        )
    ligacao.close()


def test_bd_rejeita_nota_acima_do_limite(bd_temporaria):
    """
    O limite de LIMITE_NOTA caracteres é aplicado pela CHECK constraint
    da base de dados, não por validação em Python — este teste confirma
    que essa proteção existe mesmo sem passar por adicionar_livro().
    """
    nota_demasiado_longa = "x" * (LIMITE_NOTA + 1)
    ligacao = database.obter_ligacao()
    with pytest.raises(sqlite3.IntegrityError):
        ligacao.execute(
            "INSERT INTO livros (titulo, autor, genero, estado_leitura, nota) VALUES (?, ?, ?, ?, ?)",
            ("Livro X", "Autor X", "Ensaio", "por ler", nota_demasiado_longa),
        )
    ligacao.close()


def test_nota_no_limite_exato_e_aceite(bd_temporaria):
    """O limite é <=, por isso exatamente LIMITE_NOTA caracteres deve passar."""
    nota_no_limite = "x" * LIMITE_NOTA
    database.adicionar_livro("Livro X", "Autor X", "Ensaio", "por ler", nota=nota_no_limite)
    assert database.listar_livros()[0]["nota"] == nota_no_limite


# --- listar_livros -----------------------------------------------------

def test_listar_livros_sem_filtro_devolve_todos_ordenados_por_titulo(bd_temporaria):
    database.adicionar_livro("Zebra", "Autor A", "Ficção", "lido")
    database.adicionar_livro("Abelha", "Autor B", "Ficção", "lido")
    titulos = [livro["titulo"] for livro in database.listar_livros()]
    assert titulos == ["Abelha", "Zebra"]


def test_listar_livros_com_filtro_de_estado(bd_temporaria):
    database.adicionar_livro("Livro Lido", "Autor A", "Ficção", "lido")
    database.adicionar_livro("Livro Por Ler", "Autor B", "Ficção", "por ler")
    resultado = database.listar_livros(estado_leitura="lido")
    assert len(resultado) == 1
    assert resultado[0]["titulo"] == "Livro Lido"


def test_listar_livros_sem_livros_devolve_lista_vazia(bd_temporaria):
    assert database.listar_livros() == []


# --- procurar_livros -----------------------------------------------

def test_procurar_livros_ignora_acentos(bd_temporaria):
    database.adicionar_livro("Meditações", "Marco Aurélio", "Filosofia", "lido")
    resultado = database.procurar_livros("meditacoes")
    assert len(resultado) == 1
    assert resultado[0]["titulo"] == "Meditações"


def test_procurar_livros_ignora_maiusculas(bd_temporaria):
    database.adicionar_livro("Duna", "Frank Herbert", "Ficção Científica", "por ler")
    assert len(database.procurar_livros("DUNA")) == 1


def test_procurar_livros_por_autor(bd_temporaria):
    database.adicionar_livro("Cem Anos de Solidão", "García Márquez", "Ficção", "lido")
    assert len(database.procurar_livros("garcia marquez")) == 1


def test_procurar_livros_sem_correspondencia(bd_temporaria):
    database.adicionar_livro("Duna", "Frank Herbert", "Ficção Científica", "por ler")
    assert database.procurar_livros("inexistente") == []


# --- atualizar_estado_leitura ----------------------------------------

def test_atualizar_estado_leitura(bd_temporaria):
    id_livro = database.adicionar_livro("Livro X", "Autor X", "Ensaio", "por ler")
    database.atualizar_estado_leitura(id_livro, "lido")
    assert database.listar_livros()[0]["estado_leitura"] == "lido"


def test_atualizar_estado_leitura_invalido_lanca_valueerror(bd_temporaria):
    id_livro = database.adicionar_livro("Livro X", "Autor X", "Ensaio", "por ler")
    with pytest.raises(ValueError):
        database.atualizar_estado_leitura(id_livro, "estado_inventado")


# --- remover_livro -----------------------------------------------------

def test_remover_livro(bd_temporaria):
    id_livro = database.adicionar_livro("Livro X", "Autor X", "Ensaio", "por ler")
    database.remover_livro(id_livro)
    assert database.listar_livros() == []


def test_remover_livro_id_inexistente_nao_rebenta(bd_temporaria):
    """Remover um id que não existe deve ser uma operação silenciosa, não um erro."""
    database.remover_livro(9999)


# --- normalizar_texto (função auxiliar) -----------------------------

@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("Meditações", "meditacoes"),
        ("SÃO PAULO", "sao paulo"),
        ("García Márquez", "garcia marquez"),
        ("já sem acentos", "ja sem acentos"),
        ("", ""),
    ],
)
def test_normalizar_texto(entrada, esperado):
    assert database.normalizar_texto(entrada) == esperado
