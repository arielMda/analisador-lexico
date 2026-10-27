# Qual é a função deste arquivo?
# Ele representa um Autômato Finito Determinístico (AFD) lido de um arquivo JSON
# e simula a execução do autômato passo a passo, guardando o caminho de estados.
#
# Formalmente, um AFD é a 5-upla M = (Q, Σ, δ, q0, F). No JSON:
#   Q  -> "estados"
#   Σ  -> "alfabeto"   (agrupado em classes de caracteres, ex.: "letra", "digito")
#   δ  -> "transicoes" (estado -> classe -> próximo estado)
#   q0 -> "inicial"
#   F  -> "finais"
# O formato completo está documentado em docs/CONTRATO.md.

import json
from dataclasses import dataclass, field

# Conversões de valor que um autômato pode pedir para o lexema reconhecido
CONVERSOES = ("int", "float", "string")


class ErroAutomato(Exception):
    """Especificação de autômato inválida (arquivo malformado, estado inexistente etc.)."""


@dataclass(frozen=True)
class Passo:
    """Uma transição feita durante a simulação: origem --caractere--> destino."""

    origem: str
    caractere: str
    classe: str
    destino: str


@dataclass
class ResultadoExecucao:
    """Resultado de rodar o autômato a partir de uma posição do texto."""

    lexema: str  # maior prefixo aceito ("" se nenhum)
    passos: list = field(default_factory=list)  # passos até o último estado final
    passos_totais: list = field(default_factory=list)  # todos os passos até travar
    estado_parada: str = ""  # estado em que o autômato travou

    @property
    def aceito(self):
        return len(self.lexema) > 0


class Automato:
    def __init__(self, dados, origem="<dict>"):
        # "origem" é usada só nas mensagens de erro (normalmente o caminho do arquivo)
        self.origem = origem
        self._validar(dados)

        self.nome = dados["nome"]
        self.token = dados["token"]
        self.prioridade = dados.get("prioridade", 100)
        self.ignorar = dados.get("ignorar", False)
        self.reservadas = dados.get("reservadas", False)
        self.converter = dados.get("converter")
        self.estados = list(dados["estados"])
        self.inicial = dados["inicial"]
        self.finais = set(dados["finais"])
        self.transicoes = {
            estado: dict(saidas) for estado, saidas in dados["transicoes"].items()
        }
        self._montar_alfabeto(dados["alfabeto"])

    # ------------------------------------------------------------------
    # Carregamento
    # ------------------------------------------------------------------

    @classmethod
    def de_arquivo(cls, caminho):
        """Lê e valida um autômato de um arquivo JSON."""
        try:
            with open(caminho, encoding="utf-8") as arquivo:
                conteudo = arquivo.read()
        except FileNotFoundError:
            raise ErroAutomato(f"{caminho}: arquivo não encontrado")
        except UnicodeDecodeError:
            raise ErroAutomato(f"{caminho}: o arquivo não está em UTF-8")
        except OSError as erro:
            raise ErroAutomato(f"{caminho}: não foi possível ler o arquivo ({erro})")

        if not conteudo.strip():
            raise ErroAutomato(f"{caminho}: arquivo vazio")

        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError as erro:
            raise ErroAutomato(
                f"{caminho}: JSON malformado na linha {erro.lineno}, "
                f"coluna {erro.colno} ({erro.msg})"
            )

        return cls(dados, origem=str(caminho))

    def _erro(self, mensagem):
        raise ErroAutomato(f"{self.origem}: {mensagem}")

    def _validar(self, dados):
        """Confere se a especificação é um AFD bem formado."""
        if not isinstance(dados, dict):
            self._erro("o autômato deve ser um objeto JSON { ... }")

        for chave in ("nome", "token", "estados", "alfabeto", "transicoes", "inicial", "finais"):
            if chave not in dados:
                self._erro(f'campo obrigatório "{chave}" não encontrado')

        for chave in ("nome", "token", "inicial"):
            if not isinstance(dados[chave], str) or not dados[chave]:
                self._erro(f'"{chave}" deve ser um texto não vazio')

        # Q: estados
        estados = dados["estados"]
        if not isinstance(estados, list) or not estados:
            self._erro('"estados" deve ser uma lista não vazia')
        if not all(isinstance(e, str) and e for e in estados):
            self._erro('todos os "estados" devem ser textos não vazios')
        if len(set(estados)) != len(estados):
            self._erro('"estados" tem nomes repetidos')

        # q0 e F
        if dados["inicial"] not in estados:
            self._erro(f'estado inicial "{dados["inicial"]}" não está em "estados"')
        finais = dados["finais"]
        if not isinstance(finais, list) or not finais:
            self._erro('"finais" deve ser uma lista não vazia')
        for estado in finais:
            if estado not in estados:
                self._erro(f'estado final "{estado}" não está em "estados"')

        # Σ: classes de caracteres
        alfabeto = dados["alfabeto"]
        if not isinstance(alfabeto, dict) or not alfabeto:
            self._erro('"alfabeto" deve ser um objeto não vazio { "classe": "caracteres" }')
        complementares = 0
        for classe, definicao in alfabeto.items():
            if isinstance(definicao, str):
                if not definicao:
                    self._erro(f'a classe "{classe}" do alfabeto está vazia')
            elif isinstance(definicao, dict) and set(definicao) == {"exceto"}:
                if not isinstance(definicao["exceto"], str):
                    self._erro(f'"exceto" da classe "{classe}" deve ser um texto')
                complementares += 1
            else:
                self._erro(
                    f'a classe "{classe}" deve ser um texto com os caracteres '
                    f'ou {{"exceto": "..."}}'
                )
        if complementares > 1:
            self._erro('só pode existir uma classe do tipo {"exceto": ...} por autômato')

        # δ: função de transição
        transicoes = dados["transicoes"]
        if not isinstance(transicoes, dict):
            self._erro('"transicoes" deve ser um objeto { "estado": { "classe": "destino" } }')
        for origem, saidas in transicoes.items():
            if origem not in estados:
                self._erro(f'transição a partir de "{origem}", que não está em "estados"')
            if not isinstance(saidas, dict):
                self._erro(f'as transições de "{origem}" devem ser um objeto {{ "classe": "destino" }}')
            for classe, destino in saidas.items():
                if classe not in alfabeto:
                    self._erro(f'transição {origem} --{classe}--> usa uma classe que não está no "alfabeto"')
                if destino not in estados:
                    self._erro(f'transição {origem} --{classe}--> "{destino}", que não está em "estados"')

        # Campos opcionais
        prioridade = dados.get("prioridade", 100)
        if not isinstance(prioridade, int) or isinstance(prioridade, bool):
            self._erro('"prioridade" deve ser um número inteiro')
        for chave in ("ignorar", "reservadas"):
            if not isinstance(dados.get(chave, False), bool):
                self._erro(f'"{chave}" deve ser true ou false')
        if dados.get("converter") not in (None, *CONVERSOES):
            self._erro(f'"converter" deve ser um destes: {", ".join(CONVERSOES)}')

    def _montar_alfabeto(self, alfabeto):
        # Mapa caractere -> classe, para as classes explícitas.
        # Cada caractere só pode pertencer a uma classe, senão o autômato
        # deixaria de ser determinístico.
        self._classe_do_caractere = {}
        self._classe_complementar = None
        self._excecoes = ""

        for classe, definicao in alfabeto.items():
            if isinstance(definicao, dict):
                self._classe_complementar = classe
                self._excecoes = definicao["exceto"]
                continue
            for caractere in definicao:
                anterior = self._classe_do_caractere.get(caractere)
                if anterior is not None and anterior != classe:
                    self._erro(
                        f"o caractere {caractere!r} está nas classes "
                        f'"{anterior}" e "{classe}" (o AFD ficaria não determinístico)'
                    )
                self._classe_do_caractere[caractere] = classe

    # ------------------------------------------------------------------
    # Simulação
    # ------------------------------------------------------------------

    def classe_de(self, caractere):
        """Retorna a classe do alfabeto do caractere, ou None se ele não pertence a Σ."""
        classe = self._classe_do_caractere.get(caractere)
        if classe is not None:
            return classe
        # A classe complementar pega tudo que não está nas outras classes nem em "exceto"
        if self._classe_complementar and caractere not in self._excecoes:
            return self._classe_complementar
        return None

    def transicao(self, estado, caractere):
        """δ(estado, caractere). Retorna (classe, destino) ou (classe, None) se não há transição."""
        classe = self.classe_de(caractere)
        if classe is None:
            return None, None
        return classe, self.transicoes.get(estado, {}).get(classe)

    def executar(self, texto, inicio=0):
        """
        Roda o AFD a partir de texto[inicio] até não haver mais transição possível
        e devolve o MAIOR prefixo que terminou em um estado final.
        É o que o lexer usa para encontrar o próximo token.
        """
        estado = self.inicial
        passos = []
        tamanho_aceito = 0

        posicao = inicio
        while posicao < len(texto):
            caractere = texto[posicao]
            classe, destino = self.transicao(estado, caractere)
            if destino is None:
                break
            passos.append(Passo(estado, caractere, classe, destino))
            estado = destino
            posicao += 1
            if estado in self.finais:
                tamanho_aceito = len(passos)

        return ResultadoExecucao(
            lexema=texto[inicio : inicio + tamanho_aceito],
            passos=passos[:tamanho_aceito],
            passos_totais=passos,
            estado_parada=estado,
        )

    def reconhecer(self, palavra):
        """
        Simulação clássica do AFD: a palavra inteira é aceita?
        Retorna (aceita, passos). Se travar no meio, os passos param ali.
        """
        estado = self.inicial
        passos = []
        for caractere in palavra:
            classe, destino = self.transicao(estado, caractere)
            if destino is None:
                return False, passos
            passos.append(Passo(estado, caractere, classe, destino))
            estado = destino
        return estado in self.finais, passos

    def __repr__(self):
        return f"Automato({self.nome!r}, token={self.token!r})"


def formatar_caminho(passos, inicial=None):
    """Monta o texto do caminho percorrido. Ex.: q0 --'a'--> q1 --'1'--> q1"""
    if not passos:
        return inicial or ""
    partes = [passos[0].origem]
    for passo in passos:
        partes.append(f"--{passo.caractere!r}--> {passo.destino}")
    return " ".join(partes)
