# Contrato do projeto (formato dos arquivos e interfaces)

Este documento define o que cada parte do projeto espera das outras, para que cada um trabalhe na sua branch sem travar ninguém.

## Estrutura de pastas

```
analisador-lexico/
├── lexer/                  # pacote do analisador (Luis)
│   ├── automato.py         # AFD lido de JSON + simulação passo a passo
│   ├── linguagem.py        # carrega config/linguagem.json
│   ├── lexer.py            # analisador léxico (maior casamento + recuperação de erro)
│   └── tokens.py           # classes Token e ErroLexico
├── config/                 # definição da NOSSA linguagem (Ariel)
│   ├── linguagem.json
│   └── automatos/*.json    # um AFD por tipo de token
├── exemplos/               # programas de exemplo, válidos e inválidos (Artur)
├── tests/                  # testes automáticos (fixtures = linguagem de teste)
├── docs/CONTRATO.md        # este arquivo
├── main.py                 # CLI (Artur)
└── README.md               # manual (Artur)
```

## 1. Formato de um autômato (`config/automatos/*.json`)

Cada arquivo descreve um AFD M = (Q, Σ, δ, q0, F) que reconhece **um tipo de token**.

```json
{
  "nome": "identificador",
  "token": "TT_IDENT",
  "prioridade": 10,
  "reservadas": true,
  "estados": ["q0", "q1"],
  "alfabeto": {
    "letra": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_",
    "digito": "0123456789"
  },
  "transicoes": {
    "q0": { "letra": "q1" },
    "q1": { "letra": "q1", "digito": "q1" }
  },
  "inicial": "q0",
  "finais": ["q1"]
}
```

| Campo | Obrigatório | Significado |
|---|---|---|
| `nome` | sim | Nome do autômato (aparece nas mensagens e no passo a passo). Não pode repetir. |
| `token` | sim | Tipo do token gerado, ex.: `TT_INT`. |
| `estados` | sim | **Q**: lista de estados. |
| `alfabeto` | sim | **Σ**, agrupado em classes: `"classe": "caracteres"`. Cada caractere só pode estar em **uma** classe, senão o AFD deixaria de ser determinístico e o arquivo é rejeitado. |
| `transicoes` | sim | **δ**: `"estado": { "classe": "destino" }`. Se uma transição não existe, o autômato trava ali. |
| `inicial` | sim | **q0**. |
| `finais` | sim | **F**: estados de aceitação. |
| `prioridade` | não (padrão 100) | Desempate quando dois autômatos reconhecem um lexema do mesmo tamanho: o **menor** número vence. |
| `reservadas` | não (padrão `false`) | Se `true`, o lexema é procurado na tabela `palavras_reservadas`. Use no identificador. |
| `ignorar` | não (padrão `false`) | Se `true`, o token é reconhecido e descartado. Use em comentários. |
| `converter` | não | `"int"`, `"float"` ou `"string"` (tira as aspas). Define o `valor` do token. |

**Classe complementar ("qualquer caractere exceto…").** Uma classe pode ser `{"exceto": "..."}`. Ela casa com qualquer caractere que **não** esteja nas outras classes do autômato **nem** no `exceto`. Só pode haver uma por autômato. Ela é útil para strings e comentários:

```json
"alfabeto": {
  "aspas": "\"",
  "outro": { "exceto": "\n" }
}
```

Espaço, tab e quebra de linha são descartados pelo lexer antes de rodar os autômatos, então **não** é preciso criar um autômato para eles.

## 2. Formato da linguagem (`config/linguagem.json`)

```json
{
  "nome": "NomeDaLinguagem",
  "automatos": [
    "automatos/identificador.json",
    "automatos/inteiro.json",
    "automatos/float.json"
  ],
  "palavras_reservadas": {
    "se": "TT_SE",
    "senao": "TT_SENAO"
  }
}
```

- Os caminhos em `automatos` são relativos à pasta do `linguagem.json`.
- As palavras reservadas precisam ser reconhecidas por um autômato com `"reservadas": true`, que normalmente é o identificador.

## 3. Como o lexer escolhe o token

Em cada posição do código, o lexer roda **todos** os autômatos e escolhe o vencedor assim:

1. **Maior casamento:** vence o lexema mais longo (`<=` vira um token, não `<` e `=`).
2. **Empate:** vence a menor `prioridade`.
3. **Empate de novo:** vence o que aparece primeiro em `automatos`.

Se nenhum autômato aceita nada, o lexer gera um `ErroLexico` e **continua** a análise:
- **token incompleto:** algum autômato começou a ler, mas travou fora de um estado final (ex.: `"string sem fechar`);
- **caractere desconhecido:** nenhum autômato aceita o caractere. Caracteres desconhecidos seguidos (`@@@`) viram um erro só.

## 4. Interface em Python (o que `main.py` e os testes usam)

```python
from lexer import Linguagem, tokenizar, formatar_caminho, ErroAutomato

try:
    linguagem = Linguagem.de_arquivo("config/linguagem.json")
except ErroAutomato as erro:
    print(erro)          # mensagem pronta: arquivo, problema, linha/coluna do JSON
    ...

tokens, erros = tokenizar(linguagem, codigo_fonte, arquivo="programa.txt")
```

**`Token`** (`lexer/tokens.py`)
| Atributo | Exemplo |
|---|---|
| `tipo` | `"TT_INT"` |
| `lexema` | `"42"` |
| `valor` | `42` |
| `linha`, `coluna` | `3`, `5` (começam em 1) |
| `automato` | `"inteiro"` |
| `passos` | lista de `Passo(origem, caractere, classe, destino)` |

**`ErroLexico`**: `mensagem`, `lexema`, `linha`, `coluna`, `texto_linha`, `arquivo`, `passos` e o método `como_texto()`, que devolve a mensagem formatada com uma seta `^` apontando o erro.

**Passo a passo.** `formatar_caminho(token.passos)` devolve, por exemplo:
```
q0 --'<'--> menor --'='--> menor_igual
```

**Simulação de uma palavra isolada** (útil na apresentação):
```python
from lexer import Automato
afd = Automato.de_arquivo("config/automatos/float.json")
aceita, passos = afd.reconhecer("3.14")
```

## 5. Divisão de tarefas

| Quem | Branch | Entrega |
|---|---|---|
| Luis | `feat/automato` | `lexer/` (motor do AFD, lexer, validação dos JSONs) + este contrato + testes do núcleo |
| Ariel | `feat/linguagem` | `config/linguagem.json` e `config/automatos/*.json`: nome da linguagem, tokens, palavras reservadas, AFDs de identificador, inteiro, float, string, operadores, delimitadores e comentário |
| Artur | `feat/cli-docs` | `main.py` (arquivo, modo interativo e `--passo-a-passo`), `exemplos/`, mensagens para arquivo inexistente ou vazio, README/manual, `.gitignore` |

A pasta `tests/fixtures/` tem uma linguagem de teste completa, que serve de exemplo para os JSONs do Ariel e para o Artur testar o `main.py` antes de a linguagem final ficar pronta.

Rodar os testes: `python3 -m unittest discover tests`
