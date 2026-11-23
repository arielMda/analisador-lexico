# Qual é a função deste arquivo?
# Ele define os nós da árvore sintática (AST): o parser transforma a lista de
# tokens nesses nós e o avaliador percorre a árvore para executar o programa.
# Cada nó guarda o token de onde veio, para as mensagens de erro apontarem o lugar.

from dataclasses import dataclass


# ----- Expressões (produzem um valor) -----


@dataclass
class Literal:
    token: object
    valor: object  # int, float ou texto


@dataclass
class Variavel:
    token: object
    nome: str


@dataclass
class Unario:
    operador: object  # token do operador (+ ou -)
    operando: object


@dataclass
class Binario:
    esquerda: object
    operador: object  # token do operador (+, -, *, /, <, <=, >, >=, ==, !=)
    direita: object


# ----- Comandos (fazem alguma coisa) -----


@dataclass
class Expressao:
    """Expressão usada como comando, ex.: 2 + 3. O shell mostra o resultado."""

    expressao: object


@dataclass
class Atribuicao:
    token: object  # token do nome da variável
    nome: str
    valor: object


@dataclass
class Mostrar:
    token: object
    expressao: object


@dataclass
class Se:
    token: object
    condicao: object
    entao: list  # comandos do bloco do "se"
    senao: object = None  # lista de comandos; um "senao se" vira uma lista com um Se
