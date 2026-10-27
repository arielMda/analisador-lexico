# Testes do motor do autômato (lexer/automato.py).
# Rodar da raiz do projeto: python3 -m unittest discover tests

import json
import tempfile
import unittest
from pathlib import Path

from lexer import Automato, ErroAutomato, formatar_caminho

FIXTURES = Path(__file__).parent / "fixtures" / "automatos"


def automato_valido(**alteracoes):
    """AFD mínimo que reconhece números inteiros; 'alteracoes' sobrescreve campos."""
    dados = {
        "nome": "inteiro",
        "token": "TT_INT",
        "estados": ["q0", "q1"],
        "alfabeto": {"digito": "0123456789"},
        "transicoes": {"q0": {"digito": "q1"}, "q1": {"digito": "q1"}},
        "inicial": "q0",
        "finais": ["q1"],
    }
    dados.update(alteracoes)
    return dados


class TestSimulacao(unittest.TestCase):
    def setUp(self):
        self.ident = Automato.de_arquivo(FIXTURES / "identificador.json")
        self.float = Automato.de_arquivo(FIXTURES / "float.json")
        self.string = Automato.de_arquivo(FIXTURES / "string.json")

    def test_reconhecer_aceita(self):
        aceita, passos = self.ident.reconhecer("x1")
        self.assertTrue(aceita)
        self.assertEqual(formatar_caminho(passos), "q0 --'x'--> q1 --'1'--> q1")

    def test_reconhecer_rejeita_simbolo_fora_do_alfabeto(self):
        aceita, passos = self.ident.reconhecer("x@")
        self.assertFalse(aceita)
        self.assertEqual(len(passos), 1)  # travou no '@'

    def test_reconhecer_rejeita_estado_nao_final(self):
        aceita, _ = self.float.reconhecer("3.")
        self.assertFalse(aceita)

    def test_reconhecer_palavra_vazia(self):
        aceita, passos = self.ident.reconhecer("")
        self.assertFalse(aceita)
        self.assertEqual(passos, [])

    def test_executar_pega_maior_prefixo(self):
        resultado = self.ident.executar("abc+1")
        self.assertEqual(resultado.lexema, "abc")

    def test_executar_a_partir_de_posicao(self):
        resultado = self.ident.executar("12 xy", inicio=3)
        self.assertEqual(resultado.lexema, "xy")

    def test_executar_volta_ao_ultimo_estado_final(self):
        # "3.x": o float lê "3." e trava; nenhum prefixo terminou em estado final
        resultado = self.float.executar("3.x")
        self.assertFalse(resultado.aceito)
        self.assertEqual(len(resultado.passos_totais), 2)
        self.assertEqual(resultado.estado_parada, "q2")

    def test_classe_complementar(self):
        self.assertTrue(self.string.reconhecer('"olá, mundo!"')[0])
        self.assertFalse(self.string.reconhecer('"quebra\nlinha"')[0])


class TestValidacao(unittest.TestCase):
    def assertInvalido(self, dados, trecho):
        with self.assertRaises(ErroAutomato) as contexto:
            Automato(dados)
        self.assertIn(trecho, str(contexto.exception))

    def test_valido(self):
        Automato(automato_valido())

    def test_nao_e_objeto(self):
        self.assertInvalido([1, 2], "objeto JSON")

    def test_campo_faltando(self):
        dados = automato_valido()
        del dados["finais"]
        self.assertInvalido(dados, '"finais"')

    def test_inicial_inexistente(self):
        self.assertInvalido(automato_valido(inicial="q9"), "q9")

    def test_final_inexistente(self):
        self.assertInvalido(automato_valido(finais=["q9"]), "q9")

    def test_destino_inexistente(self):
        self.assertInvalido(automato_valido(transicoes={"q0": {"digito": "q9"}}), "q9")

    def test_classe_inexistente(self):
        self.assertInvalido(automato_valido(transicoes={"q0": {"letra": "q1"}}), "letra")

    def test_estados_repetidos(self):
        self.assertInvalido(automato_valido(estados=["q0", "q0", "q1"]), "repetidos")

    def test_caractere_em_duas_classes(self):
        alfabeto = {"digito": "0123456789", "zero": "0"}
        self.assertInvalido(automato_valido(alfabeto=alfabeto), "não determinístico")

    def test_duas_classes_complementares(self):
        alfabeto = {"a": {"exceto": ""}, "b": {"exceto": "x"}}
        self.assertInvalido(automato_valido(alfabeto=alfabeto), "exceto")

    def test_converter_invalido(self):
        self.assertInvalido(automato_valido(converter="bool"), "converter")


class TestArquivo(unittest.TestCase):
    def escrever(self, conteudo):
        pasta = tempfile.mkdtemp()
        caminho = Path(pasta) / "automato.json"
        caminho.write_text(conteudo, encoding="utf-8")
        return caminho

    def test_arquivo_inexistente(self):
        with self.assertRaisesRegex(ErroAutomato, "não encontrado"):
            Automato.de_arquivo("nao_existe.json")

    def test_arquivo_vazio(self):
        with self.assertRaisesRegex(ErroAutomato, "vazio"):
            Automato.de_arquivo(self.escrever("   \n"))

    def test_json_malformado(self):
        with self.assertRaisesRegex(ErroAutomato, "JSON malformado na linha 1"):
            Automato.de_arquivo(self.escrever('{"nome": "x",}'))

    def test_arquivo_valido(self):
        automato = Automato.de_arquivo(self.escrever(json.dumps(automato_valido())))
        self.assertTrue(automato.reconhecer("42")[0])


if __name__ == "__main__":
    unittest.main()
