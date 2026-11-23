# analisador-lexico 
Analisador léxico de uma linguagem simplificada criada em Python.
Usamos esta [playlist de vídeos] como base para nosso projeto. (https://www.youtube.com/watch?v=Eythq9848Fg&list=PLZQftyCk7_SdoVexSmwy_tBgs7P0b97yD)

## Tarefas a fazer
- Implementar o Lexer
- Dar um nome para a nossa linguagem
- Adicionar informações sobre o que é um lexer e afins aqui neste README.
- Apagar essa parte depois que o projeto estiver completo
- Adicionar suporte a if, strings, entre outros.

## A linguagem (cálculos, variáveis e condições)

Definida em `config/` (autômatos em JSON) e executada pelo pacote `interpretador/`.
Fluxo: **lexer** (tokens) → **parser** (`interpretador/sintatico.py`, árvore) → **interpretador** (`interpretador/avaliador.py`).

```
x = 10                       # variável (inteiro, decimal "2.5" ou texto "oi")
y = (x + 2) * 3 - 1 / 4      # + - * /  com precedência e parênteses
mostrar y                    # imprime o valor

se y > 20 {                  # comparações: < <= > >= == !=
    mostrar "maior que 20"
} senao se y == 20 {
    mostrar "igual a 20"
} senao {
    mostrar "menor que 20"
}
```

- Fim de comando: quebra de linha ou `;`. Um operador que começa uma linha nova (fora de parênteses) inicia outro comando.
- Os blocos `{ }` não criam escopo novo: existe um só conjunto de variáveis.
- A condição do `se` pode ser lógica (`x > 1`) ou numérica (`0` é falso, o resto é verdadeiro).
- `+` também concatena textos. Divisão exata de inteiros devolve inteiro (`10 / 2` → `5`).
- Rodar o terminal: `python3 shell.py`. Dentro de um bloco aberto o prompt vira `... >`; linha vazia cancela.
- Testes: `python3 -m unittest discover tests`
