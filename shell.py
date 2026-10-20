# Qual a função deste arquivo?
# Ele será o terminal para o usuário interagir com nossa linguagem

import language

while True:
    text = input("basic > ")
    result, error = language.run("<stdin>", text)

    if error:
        print(error.as_string())
    else:
        print(result)
