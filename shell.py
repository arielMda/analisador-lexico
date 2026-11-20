# Qual a função deste arquivo?
# Ele é o terminal para o usuário interagir com nossa linguagem: lê o texto digitado,
# passa pelo lexer (autômatos em JSON), pelo parser e executa. As variáveis ficam
# guardadas enquanto o shell estiver aberto.
#
# Blocos em várias linhas: se o código ainda está incompleto (ex.: um "{" sem o "}"),
# o shell mostra o prompt "... >" e espera mais linhas. Linha vazia cancela.

from pathlib import Path

from interpretador import ErroSintatico, Interpretador, formatar, rodar
from lexer import Linguagem

LINGUAGEM = Linguagem.de_arquivo(Path(__file__).parent / "config" / "linguagem.json")

interpretador = Interpretador()
pendente = ""  # linhas já digitadas de um comando ainda incompleto


def mostrar_valor(valor):
    print(formatar(valor, aspas=True))


while True:
    try:
        linha = input("... > " if pendente else "basic > ")
    except (EOFError, KeyboardInterrupt):
        break

    if pendente and not linha.strip():
        print("(entrada cancelada)")
        pendente = ""
        continue

    texto = pendente + linha + "\n"
    erros = rodar(LINGUAGEM, texto, interpretador, eco=mostrar_valor)

    incompleto = len(erros) == 1 and isinstance(erros[0], ErroSintatico) and erros[0].fim_inesperado
    if incompleto:
        pendente = texto
        continue

    pendente = ""
    for erro in erros:
        print(erro.como_texto())
