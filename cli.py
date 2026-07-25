# cli.py
#
# Este é o ponto de entrada do programa — o ficheiro que corres para
# usar a Biblioteca Pessoal. A ideia é que este ficheiro só se
# preocupe com "conversar" com o utilizador (mostrar menus, pedir
# dados, mostrar resultados). Toda a lógica de acesso aos dados fica
# em database.py. Esta separação chama-se "separação de
# responsabilidades" — facilita perceber onde procurar quando algo
# precisa de mudar, e é a mesma razão pela qual, mais tarde, vai ser
# fácil trocar este menu de texto por uma interface gráfica sem termos
# de tocar em database.py.

import database
from constantes import ESTADOS_LEITURA, GENEROS, LIMITE_NOTA


def escolher_de_lista(opcoes, titulo):
    """
    Mostra uma lista numerada de opções e pede ao utilizador para
    escolher uma. Repete a pergunta até receber um número válido.
    Usada tanto para escolher o género como o estado de leitura —
    evita repetir esta lógica em vários sítios do código.
    """
    print(f"\n{titulo}")
    for indice, opcao in enumerate(opcoes, start=1):
        print(f"  {indice}. {opcao}")

    while True:
        escolha = input("Escolha o número: ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            return opcoes[int(escolha) - 1]
        print("Opção inválida, tenta outra vez.")


def pedir_nota():
    """
    Pede ao utilizador uma nota pessoal opcional, respeitando o limite
    de caracteres definido em constantes.py. Se o utilizador não
    escrever nada, devolve None (sem nota).
    """
    while True:
        nota = input(f"Nota pessoal (opcional, até {LIMITE_NOTA} caracteres): ").strip()
        if not nota:
            return None
        if len(nota) <= LIMITE_NOTA:
            return nota
        print(f"A nota tem {len(nota)} caracteres — o limite é {LIMITE_NOTA}. Encurta um pouco.")


def mostrar_livro(livro):
    """
    Imprime um livro de forma legível. 'livro' é uma sqlite3.Row,
    que se comporta como um dicionário graças ao row_factory que
    configurámos em database.py.
    """
    print(f"\n[{livro['id']}] {livro['titulo']} — {livro['autor']}")
    print(f"    Género: {livro['genero']} | Estado: {livro['estado_leitura']}")
    if livro["isbn"]:
        print(f"    ISBN: {livro['isbn']}")
    if livro["nota"]:
        print(f"    Nota: {livro['nota']}")


def mostrar_lista(livros):
    """Imprime uma lista de livros, ou uma mensagem se estiver vazia."""
    if not livros:
        print("\nNenhum livro encontrado.")
        return
    for livro in livros:
        mostrar_livro(livro)
    print(f"\nTotal: {len(livros)} livro(s)")


def accao_adicionar_livro():
    """Recolhe os dados de um livro novo e guarda-o na base de dados."""
    print("\n--- Adicionar novo livro ---")
    titulo = input("Título: ").strip()
    autor = input("Autor: ").strip()
    isbn = input("ISBN (opcional): ").strip() or None
    genero = escolher_de_lista(GENEROS, "Género:")
    estado = escolher_de_lista(ESTADOS_LEITURA, "Estado de leitura:")
    nota = pedir_nota()

    novo_id = database.adicionar_livro(
        titulo=titulo,
        autor=autor,
        genero=genero,
        estado_leitura=estado,
        isbn=isbn,
        nota=nota,
    )
    print(f"\n[OK] Livro adicionado com sucesso (id {novo_id}).")


def accao_listar_todos():
    """Mostra todos os livros da biblioteca."""
    livros = database.listar_livros()
    mostrar_lista(livros)


def accao_listar_por_estado():
    """Mostra só os livros com um determinado estado de leitura."""
    estado = escolher_de_lista(ESTADOS_LEITURA, "Filtrar por estado:")
    livros = database.listar_livros(estado_leitura=estado)
    mostrar_lista(livros)


def accao_procurar():
    """Procura livros por título ou autor."""
    termo = input("\nProcurar (título ou autor): ").strip()
    livros = database.procurar_livros(termo)
    mostrar_lista(livros)


def accao_atualizar_estado():
    """Muda o estado de leitura de um livro existente."""
    livro_id = input("\nId do livro a atualizar: ").strip()
    if not livro_id.isdigit():
        print("Id inválido.")
        return
    novo_estado = escolher_de_lista(ESTADOS_LEITURA, "Novo estado de leitura:")
    database.atualizar_estado_leitura(int(livro_id), novo_estado)
    print("[OK] Estado atualizado.")


def accao_remover():
    """Remove um livro da biblioteca, com confirmação prévia."""
    livro_id = input("\nId do livro a remover: ").strip()
    if not livro_id.isdigit():
        print("Id inválido.")
        return
    confirmacao = input("Tens a certeza? Esta ação não pode ser desfeita (s/n): ").strip().lower()
    if confirmacao == "s":
        database.remover_livro(int(livro_id))
        print("[OK] Livro removido.")
    else:
        print("Operação cancelada.")


# Mapa entre a opção do menu (texto que o utilizador vê) e a função
# que trata dessa ação. Usar um dicionário aqui em vez de uma cadeia
# de "if/elif" torna fácil adicionar novas ações no futuro — basta
# acrescentar uma linha.
MENU = {
    "1": ("Adicionar livro", accao_adicionar_livro),
    "2": ("Listar todos os livros", accao_listar_todos),
    "3": ("Listar por estado de leitura", accao_listar_por_estado),
    "4": ("Procurar livro", accao_procurar),
    "5": ("Atualizar estado de leitura", accao_atualizar_estado),
    "6": ("Remover livro", accao_remover),
}


def mostrar_menu():
    print("\n" + "=" * 40)
    print("BIBLIOTECA PESSOAL")
    print("=" * 40)
    for chave, (descricao, _) in MENU.items():
        print(f"  {chave}. {descricao}")
    print("  0. Sair")


def main():
    """Ponto de entrada: garante que a base de dados existe e corre o
    ciclo principal do menu até o utilizador escolher sair."""
    database.criar_tabela()

    while True:
        mostrar_menu()
        escolha = input("\nEscolha uma opção: ").strip()

        if escolha == "0":
            print("Até à próxima!")
            break

        if escolha in MENU:
            _, funcao = MENU[escolha]
            funcao()
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()
