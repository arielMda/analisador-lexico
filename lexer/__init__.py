# Pacote do analisador léxico. O que os outros arquivos (main.py, testes) usam:
from .automato import Automato, ErroAutomato, Passo, ResultadoExecucao, formatar_caminho
from .lexer import Lexer, tokenizar
from .linguagem import Linguagem
from .tokens import ErroLexico, Token

__all__ = [
    "Automato",
    "ErroAutomato",
    "ErroLexico",
    "Lexer",
    "Linguagem",
    "Passo",
    "ResultadoExecucao",
    "Token",
    "formatar_caminho",
    "tokenizar",
]
