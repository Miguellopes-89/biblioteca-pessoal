# constantes.py
#
# Este ficheiro guarda valores fixos que são usados em vários sítios do
# programa (base de dados e interface). Ao centralizá-los aqui, se um dia
# quisermos adicionar um género novo ou mudar o texto de um estado de
# leitura, só precisamos de editar este ficheiro — não temos de procurar
# por todo o código.

# Lista fixa de géneros literários. A ordem aqui é a ordem que vai
# aparecer no menu quando o utilizador escolher um género.
GENEROS = [
    "Ficção",
    "Não-Ficção",
    "Ensaio",
    "Divulgação Científica",
    "Biografia",
    "Poesia",
    "Banda Desenhada",
    "Fantasia",
    "Ficção Científica",
    "Terror",
    "Romance",
    "Policial/Thriller",
    "Infantil/Juvenil",
    "Técnico/Académico",
    "Economia, Finanças e Contabilidade",
    "Outro",
]

# Os três estados de leitura possíveis. A ordem da lista também define
# a ordem em que aparecem nos menus.
ESTADOS_LEITURA = ["lido", "a ler", "por ler"]

# Limite de caracteres para o campo de notas pessoais.
LIMITE_NOTA = 160
