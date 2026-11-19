# Pacote do interpretador (parser + avaliador). O que o shell e os testes usam:
#
#   from interpretador import Interpretador, rodar
#   interp = Interpretador()
#   erros = rodar(linguagem, "x = 2 + 3\nmostrar x", interp)
#
# Fluxo de rodar(): lexer (tokens) -> parser (árvore) -> interpretador (execução).

from lexer import tokenizar

from .avaliador import Interpretador, formatar
from .erros import ErroExecucao, ErroLinguagem, ErroSintatico
from .sintatico import Parser

__all__ = [
    "ErroExecucao",
    "ErroLinguagem",
    "ErroSintatico",
    "Interpretador",
    "Parser",
    "formatar",
    "rodar",
]


def rodar(linguagem, texto, interpretador, arquivo="<stdin>", eco=None):
    """
    Analisa e executa o texto. Devolve a lista de erros (vazia se deu tudo certo).
    O programa só começa a executar depois de passar pelo lexer e pelo parser sem erro.
    """
    tokens, erros = tokenizar(linguagem, texto, arquivo)
    if erros:
        return erros

    try:
        programa = Parser(tokens).analisar()
        interpretador.executar(programa, eco)
    except ErroLinguagem as erro:
        erro.preencher(texto, arquivo)
        return [erro]
    return []
