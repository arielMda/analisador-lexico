# Qual é a função deste arquivo?
# Ele é o analisador léxico: percorre o código-fonte e, em cada posição,
# roda todos os autômatos da linguagem para descobrir qual é o próximo token.
#
# Regras usadas para escolher o token:
#   1. Maior casamento (maximal munch): vence o autômato que reconheceu o
#      lexema mais longo. Ex.: "<=" vira um token só, e não "<" seguido de "=".
#   2. Empate no tamanho: vence o autômato com menor "prioridade".
#      Ex.: "se" é reconhecido como identificador e como palavra "se";
#      a palavra reservada vem da tabela de reservadas (ver _criar_token).
#   3. Empate na prioridade: vence o que aparece primeiro no linguagem.json.
#
# Quando nenhum autômato reconhece nada, o lexer registra um erro léxico,
# pula o trecho problemático e continua, para mostrar TODOS os erros de uma vez.

from .tokens import ErroLexico, Token

# Caracteres que só separam tokens e são descartados
ESPACOS = " \t\r\n"


class Lexer:
    def __init__(self, linguagem, texto, arquivo="<stdin>"):
        self.linguagem = linguagem
        self.texto = texto
        self.arquivo = arquivo
        self.linhas = texto.splitlines()

        # Posição atual (índice no texto, linha e coluna começando em 1)
        self.indice = 0
        self.linha = 1
        self.coluna = 1

    def tokenizar(self):
        """Retorna (tokens, erros). O lexer não para no primeiro erro."""
        tokens = []
        erros = []

        while self.indice < len(self.texto):
            if self.texto[self.indice] in ESPACOS:
                self._avancar(1)
                continue

            melhor = self._maior_casamento(self.indice)
            if melhor is None:
                erros.append(self._criar_erro())
                continue

            automato, resultado = melhor
            if not automato.ignorar:  # comentários, por exemplo, são descartados
                tokens.append(self._criar_token(automato, resultado))
            self._avancar(len(resultado.lexema))

        return tokens, erros

    # ------------------------------------------------------------------
    # Escolha do token
    # ------------------------------------------------------------------

    def _maior_casamento(self, inicio):
        """Roda todos os autômatos em texto[inicio:] e devolve (automato, resultado) do vencedor."""
        melhor = None
        for ordem, automato in enumerate(self.linguagem.automatos):
            resultado = automato.executar(self.texto, inicio)
            if not resultado.aceito:
                continue
            # Maior lexema primeiro; depois menor prioridade; depois ordem no arquivo
            chave = (-len(resultado.lexema), automato.prioridade, ordem)
            if melhor is None or chave < melhor[0]:
                melhor = (chave, automato, resultado)

        if melhor is None:
            return None
        return melhor[1], melhor[2]

    def _criar_token(self, automato, resultado):
        lexema = resultado.lexema
        tipo = automato.token

        # Palavras reservadas: o lexema foi reconhecido como identificador,
        # mas está na tabela de reservadas, então ganha o tipo da palavra.
        if automato.reservadas and lexema in self.linguagem.palavras_reservadas:
            tipo = self.linguagem.palavras_reservadas[lexema]

        return Token(
            tipo=tipo,
            lexema=lexema,
            valor=_converter(lexema, automato.converter),
            linha=self.linha,
            coluna=self.coluna,
            automato=automato.nome,
            passos=resultado.passos,
        )

    # ------------------------------------------------------------------
    # Erros
    # ------------------------------------------------------------------

    def _criar_erro(self):
        """
        Registra um erro léxico na posição atual e avança o cursor.
        Dois casos:
          - token incompleto: algum autômato começou a ler mas travou antes de
            chegar num estado final (ex.: string sem fechar aspas);
          - caractere desconhecido: nenhum autômato aceita esse caractere.
            Caracteres desconhecidos seguidos viram um erro só.
        """
        linha, coluna = self.linha, self.coluna
        texto_linha = self.linhas[linha - 1] if linha - 1 < len(self.linhas) else ""

        incompleto = self._maior_tentativa(self.indice)
        if incompleto is not None:
            automato, resultado = incompleto
            lexema = "".join(p.caractere for p in resultado.passos_totais)
            erro = ErroLexico(
                mensagem=(
                    f"token incompleto {lexema!r} ({automato.nome}: "
                    f"o autômato parou no estado {resultado.estado_parada}, que não é final)"
                ),
                lexema=lexema,
                linha=linha,
                coluna=coluna,
                texto_linha=texto_linha,
                arquivo=self.arquivo,
                passos=resultado.passos_totais,
            )
            self._avancar(len(lexema))
            return erro

        # Junta os caracteres desconhecidos seguidos (ex.: "@@@" vira um erro só)
        fim = self.indice + 1
        while (
            fim < len(self.texto)
            and self.texto[fim] not in ESPACOS
            and self._maior_casamento(fim) is None
            and self._maior_tentativa(fim) is None
        ):
            fim += 1
        lexema = self.texto[self.indice : fim]
        descricao = "caractere desconhecido" if len(lexema) == 1 else "caracteres desconhecidos"
        erro = ErroLexico(
            mensagem=f"{descricao} {lexema!r}",
            lexema=lexema,
            linha=linha,
            coluna=coluna,
            texto_linha=texto_linha,
            arquivo=self.arquivo,
        )
        self._avancar(len(lexema))
        return erro

    def _maior_tentativa(self, inicio):
        """Autômato que andou mais caracteres sem aceitar nada (ou None se nenhum andou)."""
        melhor = None
        for automato in self.linguagem.automatos:
            resultado = automato.executar(self.texto, inicio)
            if resultado.passos_totais and (
                melhor is None or len(resultado.passos_totais) > len(melhor[1].passos_totais)
            ):
                melhor = (automato, resultado)
        return melhor

    # ------------------------------------------------------------------
    # Posição
    # ------------------------------------------------------------------

    def _avancar(self, quantidade):
        """Anda 'quantidade' caracteres, atualizando linha e coluna."""
        for _ in range(quantidade):
            if self.texto[self.indice] == "\n":
                self.linha += 1
                self.coluna = 1
            else:
                self.coluna += 1
            self.indice += 1


def _converter(lexema, conversao):
    """Converte o lexema para o valor do token, conforme o campo "converter" do autômato."""
    if conversao == "int":
        return int(lexema)
    if conversao == "float":
        return float(lexema)
    if conversao == "string":
        return lexema[1:-1]  # tira os delimitadores (aspas)
    return lexema


def tokenizar(linguagem, texto, arquivo="<stdin>"):
    """Atalho: cria o Lexer e já devolve (tokens, erros)."""
    return Lexer(linguagem, texto, arquivo).tokenizar()
