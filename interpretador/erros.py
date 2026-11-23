# Qual é a função deste arquivo?
# Ele define os erros das fases depois do lexer: erro sintático (a sequência de
# tokens não forma um programa válido) e erro de execução (ex.: divisão por zero).
# O formato da mensagem é o mesmo do ErroLexico, com linha, coluna e uma seta.


class ErroLinguagem(Exception):
    tipo = "da linguagem"

    def __init__(self, mensagem, linha=1, coluna=1, lexema="", fim_inesperado=False):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna
        self.lexema = lexema
        # True quando o programa acabou antes da hora (ex.: falta fechar "}").
        # O shell usa isso para pedir mais linhas em vez de mostrar erro.
        self.fim_inesperado = fim_inesperado
        self.texto_linha = ""
        self.arquivo = "<stdin>"

    @classmethod
    def em(cls, token, mensagem, **extra):
        """Cria o erro apontando para a posição de um token."""
        return cls(mensagem, token.linha, token.coluna, token.lexema, **extra)

    def preencher(self, texto, arquivo):
        """Completa o erro com a linha do código-fonte e o nome do arquivo."""
        linhas = texto.splitlines()
        if 0 < self.linha <= len(linhas):
            self.texto_linha = linhas[self.linha - 1]
        self.arquivo = arquivo

    def como_texto(self):
        resultado = f"Erro {self.tipo}: {self.mensagem}\n"
        resultado += f"  Arquivo {self.arquivo}, linha {self.linha}, coluna {self.coluna}\n"
        if self.texto_linha:
            resultado += f"    {self.texto_linha}\n"
            resultado += "    " + " " * (self.coluna - 1) + "^" * max(1, len(self.lexema))
        return resultado


class ErroSintatico(ErroLinguagem):
    tipo = "sintático"


class ErroExecucao(ErroLinguagem):
    tipo = "de execução"
