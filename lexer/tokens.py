# Qual é a função deste arquivo?
# Ele define o que o lexer produz: os tokens reconhecidos e os erros léxicos.

from dataclasses import dataclass, field


@dataclass
class Token:
    tipo: str  # ex.: "TT_INT", "TT_IDENT", "TT_SE"
    lexema: str  # trecho exato do código-fonte
    valor: object  # lexema convertido (int, float, texto sem aspas) ou o próprio lexema
    linha: int  # começa em 1
    coluna: int  # começa em 1
    automato: str = ""  # nome do autômato que reconheceu o token
    passos: list = field(default_factory=list, repr=False)  # caminho de estados (lista de Passo)

    def __repr__(self):
        return f"{self.tipo}:{self.lexema}"


@dataclass
class ErroLexico:
    mensagem: str  # ex.: "caractere desconhecido '@'"
    lexema: str  # trecho que causou o erro
    linha: int
    coluna: int
    texto_linha: str = ""  # linha inteira do código, para mostrar onde foi o erro
    arquivo: str = "<stdin>"
    passos: list = field(default_factory=list, repr=False)  # caminho até o autômato travar (se houver)

    def como_texto(self):
        """Mensagem pronta para mostrar ao usuário, com a linha e uma seta no erro."""
        resultado = f"Erro léxico: {self.mensagem}\n"
        resultado += f"  Arquivo {self.arquivo}, linha {self.linha}, coluna {self.coluna}\n"
        if self.texto_linha:
            resultado += f"    {self.texto_linha}\n"
            resultado += "    " + " " * (self.coluna - 1) + "^" * max(1, len(self.lexema))
        return resultado
