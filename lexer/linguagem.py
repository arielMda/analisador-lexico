# Qual é a função deste arquivo?
# Ele carrega a definição da linguagem (config/linguagem.json): o nome dela,
# a lista de autômatos que reconhecem os tokens e as palavras reservadas.

import json
from pathlib import Path

from .automato import Automato, ErroAutomato


class Linguagem:
    def __init__(self, nome, automatos, palavras_reservadas):
        self.nome = nome
        self.automatos = automatos  # lista de Automato, na ordem do arquivo
        self.palavras_reservadas = palavras_reservadas  # lexema -> tipo do token

    @classmethod
    def de_arquivo(cls, caminho):
        """Lê o linguagem.json e todos os autômatos que ele referencia."""
        caminho = Path(caminho)
        try:
            conteudo = caminho.read_text(encoding="utf-8")
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

        if not isinstance(dados, dict):
            raise ErroAutomato(f"{caminho}: a linguagem deve ser um objeto JSON {{ ... }}")

        nome = dados.get("nome")
        if not isinstance(nome, str) or not nome:
            raise ErroAutomato(f'{caminho}: "nome" deve ser um texto não vazio')

        arquivos = dados.get("automatos")
        if not isinstance(arquivos, list) or not arquivos:
            raise ErroAutomato(f'{caminho}: "automatos" deve ser uma lista não vazia de arquivos')

        reservadas = dados.get("palavras_reservadas", {})
        if not isinstance(reservadas, dict) or not all(
            isinstance(k, str) and isinstance(v, str) and k and v for k, v in reservadas.items()
        ):
            raise ErroAutomato(
                f'{caminho}: "palavras_reservadas" deve ser um objeto {{ "palavra": "TIPO" }}'
            )

        # Os caminhos dos autômatos são relativos à pasta do linguagem.json
        automatos = []
        for arquivo in arquivos:
            if not isinstance(arquivo, str):
                raise ErroAutomato(f'{caminho}: os itens de "automatos" devem ser caminhos de arquivo')
            automatos.append(Automato.de_arquivo(caminho.parent / arquivo))

        nomes = [a.nome for a in automatos]
        repetidos = {n for n in nomes if nomes.count(n) > 1}
        if repetidos:
            raise ErroAutomato(f"{caminho}: autômatos com nome repetido: {', '.join(sorted(repetidos))}")

        return cls(nome, automatos, reservadas)
