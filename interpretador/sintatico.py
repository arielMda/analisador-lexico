# Qual é a função deste arquivo?
# Ele é o analisador sintático (parser): recebe os tokens do lexer e monta a árvore,
# conferindo se a ordem deles forma um programa válido. É um parser descendente
# recursivo: cada regra da gramática abaixo é um método.
#
# Gramática (precedência de baixo para cima: comparação < soma < termo < unário):
#
#   programa    := comando*
#   comando     := se | mostrar | atribuicao | expressao        (";" opcional no fim)
#   se          := "se" expressao bloco ( "senao" ( se | bloco ) )?
#   bloco       := "{" comando* "}"
#   mostrar     := "mostrar" expressao
#   atribuicao  := IDENT "=" expressao
#   expressao   := soma ( ("<" | "<=" | ">" | ">=" | "==" | "!=") soma )?
#   soma        := termo ( ("+" | "-") termo )*
#   termo       := unario ( ("*" | "/") unario )*
#   unario      := ("-" | "+") unario | primario
#   primario    := INT | FLOAT | STRING | IDENT | "(" expressao ")"
#
# Como o lexer descarta as quebras de linha, o fim de um comando é decidido assim:
# um operador que aparece numa linha NOVA (fora de parênteses) começa outro comando.
# Ex.: "x = 5" na linha 1 e "-3" na linha 2 são dois comandos, e não "5 - 3".

from .erros import ErroSintatico
from .nos import Atribuicao, Binario, Expressao, Literal, Mostrar, Se, Unario, Variavel

COMPARACAO = {"<", "<=", ">", ">=", "==", "!="}
SOMA = {"+", "-"}
TERMO = {"*", "/"}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.parenteses = 0  # profundidade de parênteses abertos

    def analisar(self):
        """Retorna o programa: uma lista de comandos."""
        programa = []
        while not self._fim():
            programa.append(self._comando())
        return programa

    # ------------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------------

    def _comando(self):
        token = self._atual()

        if token.tipo == "TT_SE":
            no = self._se()
        elif token.tipo == "TT_MOSTRAR":
            self.pos += 1
            no = Mostrar(token, self._expressao())
        elif token.tipo == "TT_IDENT" and self._proximo_e("TT_ATRIB"):
            self.pos += 2  # nome e "="
            no = Atribuicao(token, token.lexema, self._expressao())
        elif token.tipo == "TT_SENAO":
            raise ErroSintatico.em(token, "'senao' sem um 'se' antes")
        elif token.tipo == "TT_DELIM" and token.lexema == "}":
            raise ErroSintatico.em(token, "'}' sem um '{' correspondente")
        else:
            no = Expressao(self._expressao())

        if self._e("TT_DELIM", ";"):
            self.pos += 1
        return no

    def _se(self):
        token = self._consumir("TT_SE", "'se'")
        condicao = self._expressao()
        entao = self._bloco()
        senao = None
        if self._e("TT_SENAO"):
            self.pos += 1
            if self._e("TT_SE"):
                senao = [self._se()]  # "senao se ..." é um novo "se" dentro do senao
            else:
                senao = self._bloco()
        return Se(token, condicao, entao, senao)

    def _bloco(self):
        self._consumir("TT_DELIM", "'{'", "{")
        comandos = []
        while not self._e("TT_DELIM", "}"):
            if self._fim():
                raise self._erro_fim("'}' para fechar o bloco")
            comandos.append(self._comando())
        self.pos += 1  # "}"
        return comandos

    # ------------------------------------------------------------------
    # Expressões
    # ------------------------------------------------------------------

    def _expressao(self):
        esquerda = self._soma()
        if self._operador(COMPARACAO):  # sem encadear: 1 < 2 < 3 não é permitido
            operador = self._avancar()
            esquerda = Binario(esquerda, operador, self._soma())
        return esquerda

    def _soma(self):
        esquerda = self._termo()
        while self._operador(SOMA):
            operador = self._avancar()
            esquerda = Binario(esquerda, operador, self._termo())
        return esquerda

    def _termo(self):
        esquerda = self._unario()
        while self._operador(TERMO):
            operador = self._avancar()
            esquerda = Binario(esquerda, operador, self._unario())
        return esquerda

    def _unario(self):
        token = self._atual()
        if token is not None and token.tipo == "TT_OP" and token.lexema in SOMA:
            self.pos += 1
            return Unario(token, self._unario())
        return self._primario()

    def _primario(self):
        token = self._atual()
        if token is None:
            raise self._erro_fim("uma expressão")

        if token.tipo in ("TT_INT", "TT_FLOAT", "TT_STRING"):
            self.pos += 1
            return Literal(token, token.valor)
        if token.tipo == "TT_IDENT":
            self.pos += 1
            return Variavel(token, token.lexema)
        if token.tipo == "TT_DELIM" and token.lexema == "(":
            self.pos += 1
            self.parenteses += 1
            no = self._expressao()
            self._consumir("TT_DELIM", "')'", ")")
            self.parenteses -= 1
            return no

        raise ErroSintatico.em(token, f"esperava uma expressão, mas encontrei {token.lexema!r}")

    # ------------------------------------------------------------------
    # Utilitários
    # ------------------------------------------------------------------

    def _fim(self):
        return self.pos >= len(self.tokens)

    def _atual(self):
        return None if self._fim() else self.tokens[self.pos]

    def _avancar(self):
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _proximo_e(self, tipo):
        return self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].tipo == tipo

    def _e(self, tipo, lexema=None):
        """O token atual é desse tipo (e desse lexema, se informado)?"""
        token = self._atual()
        return token is not None and token.tipo == tipo and (lexema is None or token.lexema == lexema)

    def _operador(self, conjunto):
        """O token atual é um operador binário do conjunto, ainda na mesma expressão?"""
        token = self._atual()
        if token is None or token.tipo != "TT_OP" or token.lexema not in conjunto:
            return False
        # Fora de parênteses, operador em linha nova começa outro comando
        if self.parenteses == 0 and self.pos > 0 and token.linha != self.tokens[self.pos - 1].linha:
            return False
        return True

    def _consumir(self, tipo, descricao, lexema=None):
        if self._fim():
            raise self._erro_fim(descricao)
        if not self._e(tipo, lexema):
            token = self._atual()
            raise ErroSintatico.em(token, f"esperava {descricao}, mas encontrei {token.lexema!r}")
        return self._avancar()

    def _erro_fim(self, esperado):
        """Erro para quando o código acaba no meio de um comando."""
        if self.tokens:
            ultimo = self.tokens[-1]
            linha, coluna = ultimo.linha, ultimo.coluna + len(ultimo.lexema)
        else:
            linha, coluna = 1, 1
        return ErroSintatico(
            f"o código terminou, mas esperava {esperado}", linha, coluna, fim_inesperado=True
        )
