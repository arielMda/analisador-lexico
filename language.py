# Qual é a função deste arquivo?
# Ele guardará todo o código da nossa linguagem, o código que vai
# interpretar o que o usuário escreveu e julgar se é válido ou não

# TOKENS

TT_INT = "TT_INT"
TT_FLOAT = "TT_FLOAT"
TT_PLUS = "TT_PLUS"
TT_MINUS = "MINUS"
TT_MUL = "MUL"
TT_DIV = "DIV"
TT_LPAREN = "TT_LPAREN"
TT_RPAREN = "TT_RPAREN"

# Constante para verificar se o que foi digitado é um número
DIGITS = "0123456789"


# Classe para manipulação de erros
# Tem o nome do erro, pos. inicial, pos. final e detalhes do erro
class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.error_name = error_name
        self.details = details
        self.pos_start = pos_start
        self.pos_end = pos_end

    # Formatação do erro
    def as_string(self):
        result = f"{self.error_name}: {self.details}"
        result += f"Arquivo {self.pos_start.fn}, linha {self.pos_start.ln + 1}"
        return result


# Classe para tratar o erro de caractere ilegal
class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Caractere Ilegal", details)


# Classe para identificar a posição da leitura dos caracteres e o arquivo onde o erro aconteceu
# (como ainda não é possível escrever código em outros arquivos isso não é útil ainda)
class Position:
    def __init__(self, index, ln, col, fn, ftxt):
        self.fn = fn  # Nome do arquivo
        self.ftxt = ftxt  # Código escrito na linha do erro
        self.idx = index  # Índice atual do caractere
        self.ln = ln  # Linha
        self.col = col  # Coluna

    # Avança o cursor para o próximo caractere
    def advance(self, current_char):
        self.idx += 1
        self.col += 1

        if current_char == "\n":
            self.ln += 1
            self.col = 0
        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)


class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        if self.value:
            return f"{self.type}:{self.value}"
        else:
            return f"{self.type}"


# Classe do interpretador de código
class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = (
            self.text[self.pos.idx] if self.pos.idx < len(self.text) else None
        )

    def make_tokens(self):
        tokens = []

        # Verificações dos caracteres
        while self.current_char is not None:
            if self.current_char in " \t":
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char == "+":
                tokens.append(Token(TT_PLUS))
                self.advance()
            elif self.current_char == "-":
                tokens.append(Token(TT_MINUS))
                self.advance()
            elif self.current_char == "*":
                tokens.append(Token(TT_MUL))
                self.advance()
            elif self.current_char == "/":
                tokens.append(Token(TT_DIV))
                self.advance()

            elif self.current_char == "(":
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TT_RPAREN))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'\n")
        return tokens, None

    # Função para ler um número por completo a partir dos caracteres individuais
    def make_number(self):
        num_str = ""
        dot_count = 0

        while self.current_char is not None and self.current_char in DIGITS + ".":
            if self.current_char == ".":
                if dot_count == 1:
                    break
                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TT_INT, int(num_str))
        else:
            return Token(TT_FLOAT, float(num_str))


def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    return tokens, error
