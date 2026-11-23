# Qual é a função deste arquivo?
# Ele é o interpretador: percorre a árvore criada pelo parser e executa o programa.
# Guarda as variáveis num dicionário (nome -> valor), que continua valendo entre
# uma execução e outra, e por isso o shell consegue lembrar do "x = 5" digitado antes.
#
# Tipos de valor: inteiro (int), decimal (float), texto (str) e lógico (bool).
# Todas as variáveis ficam num escopo só: os blocos { } não criam escopo novo.

from .erros import ErroExecucao
from .nos import Atribuicao, Binario, Expressao, Literal, Mostrar, Se, Unario, Variavel


def eh_numero(valor):
    # bool é subclasse de int em Python, mas aqui lógico NÃO é número
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def nome_do_tipo(valor):
    if isinstance(valor, bool):
        return "lógico"
    if isinstance(valor, int):
        return "inteiro"
    if isinstance(valor, float):
        return "decimal"
    return "texto"


def formatar(valor, aspas=False):
    """Como um valor aparece para o usuário (aspas=True mostra o texto entre aspas)."""
    if isinstance(valor, bool):
        return "verdadeiro" if valor else "falso"
    if isinstance(valor, str):
        return f'"{valor}"' if aspas else valor
    return str(valor)


class Interpretador:
    def __init__(self, saida=print):
        self.variaveis = {}
        self.saida = saida  # função chamada pelo "mostrar" (troque para capturar a saída)

    def executar(self, programa, eco=None):
        """
        Executa uma lista de comandos. Se "eco" for informado, ele é chamado com o
        valor de cada expressão solta de nível mais alto (é como o shell mostra "2+3").
        """
        for no in programa:
            if isinstance(no, Expressao):
                valor = self._avaliar(no.expressao)
                if eco is not None:
                    eco(valor)
            else:
                self._executar(no)

    # ------------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------------

    def _executar(self, no):
        if isinstance(no, Atribuicao):
            self.variaveis[no.nome] = self._avaliar(no.valor)
        elif isinstance(no, Mostrar):
            self.saida(formatar(self._avaliar(no.expressao)))
        elif isinstance(no, Se):
            self._executar_se(no)
        elif isinstance(no, Expressao):
            self._avaliar(no.expressao)  # dentro de um bloco o valor é descartado

    def _executar_se(self, no):
        condicao = self._avaliar(no.condicao)
        if isinstance(condicao, bool):
            verdadeira = condicao
        elif eh_numero(condicao):
            verdadeira = condicao != 0
        else:
            raise ErroExecucao.em(
                no.token,
                f"a condição do 'se' deve ser lógica ou numérica, mas é {nome_do_tipo(condicao)}",
            )

        escolhido = no.entao if verdadeira else no.senao
        for comando in escolhido or []:
            self._executar(comando)

    # ------------------------------------------------------------------
    # Expressões
    # ------------------------------------------------------------------

    def _avaliar(self, no):
        if isinstance(no, Literal):
            return no.valor
        if isinstance(no, Variavel):
            if no.nome not in self.variaveis:
                raise ErroExecucao.em(no.token, f"a variável {no.nome!r} não foi definida")
            return self.variaveis[no.nome]
        if isinstance(no, Unario):
            return self._unario(no)
        if isinstance(no, Binario):
            return self._binario(no)
        raise TypeError(f"nó desconhecido: {no!r}")

    def _unario(self, no):
        valor = self._avaliar(no.operando)
        if not eh_numero(valor):
            raise ErroExecucao.em(
                no.operador, f"o operador {no.operador.lexema!r} só funciona com números, não com {nome_do_tipo(valor)}"
            )
        return -valor if no.operador.lexema == "-" else valor

    def _binario(self, no):
        esquerda = self._avaliar(no.esquerda)
        direita = self._avaliar(no.direita)
        operador = no.operador.lexema

        if operador in ("==", "!="):
            iguais = _iguais(esquerda, direita)
            return iguais if operador == "==" else not iguais

        if operador in ("<", "<=", ">", ">="):
            mesmo_tipo = (eh_numero(esquerda) and eh_numero(direita)) or (
                isinstance(esquerda, str) and isinstance(direita, str)
            )
            if not mesmo_tipo:
                raise self._erro_tipos(no, esquerda, direita, "comparar")
            return {
                "<": esquerda < direita,
                "<=": esquerda <= direita,
                ">": esquerda > direita,
                ">=": esquerda >= direita,
            }[operador]

        if operador == "+" and isinstance(esquerda, str) and isinstance(direita, str):
            return esquerda + direita  # concatenação de textos

        if not (eh_numero(esquerda) and eh_numero(direita)):
            raise self._erro_tipos(no, esquerda, direita, "usar")

        if operador == "+":
            return esquerda + direita
        if operador == "-":
            return esquerda - direita
        if operador == "*":
            return esquerda * direita
        # operador == "/"
        if direita == 0:
            raise ErroExecucao.em(no.operador, "divisão por zero")
        if isinstance(esquerda, int) and isinstance(direita, int) and esquerda % direita == 0:
            return esquerda // direita  # 10 / 2 dá 5 (inteiro), 10 / 4 dá 2.5
        return esquerda / direita

    def _erro_tipos(self, no, esquerda, direita, verbo):
        return ErroExecucao.em(
            no.operador,
            f"não é possível {verbo} {no.operador.lexema!r} entre "
            f"{nome_do_tipo(esquerda)} e {nome_do_tipo(direita)}",
        )


def _iguais(a, b):
    """== entre valores: números comparam por valor; tipos diferentes nunca são iguais."""
    if eh_numero(a) and eh_numero(b):
        return a == b
    return type(a) is type(b) and a == b
