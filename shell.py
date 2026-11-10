# Qual a função deste arquivo?
# Ele é o terminal para o usuário interagir com nossa linguagem:
# lê o texto digitado e passa pelo lexer novo (pacote lexer/, autômatos em JSON).

from pathlib import Path

from lexer import Linguagem, tokenizar

# Por enquanto usa a linguagem de teste; troque quando a definitiva existir
LINGUAGEM = Linguagem.de_arquivo(Path(__file__).parent / "tests" / "fixtures" / "linguagem.json")

while True:
    try:
        text = input("basic > ")
    except (EOFError, KeyboardInterrupt):
        break

    tokens, erros = tokenizar(LINGUAGEM, text)

    if erros:
        for erro in erros:
            print(erro.como_texto())
    else:
        print(tokens)
