# Testes do parser e do interpretador (cálculos, variáveis, se/senao),
# usando a linguagem definitiva em config/.
# Rodar da raiz do projeto: python3 -m unittest discover tests

import unittest
from pathlib import Path

from interpretador import ErroExecucao, ErroSintatico, Interpretador, rodar
from lexer import Linguagem, tokenizar

CONFIG = Path(__file__).parent.parent / "config" / "linguagem.json"


class TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.linguagem = Linguagem.de_arquivo(CONFIG)

    def rodar(self, codigo, interp=None):
        """Executa o código e devolve (interpretador, saidas do mostrar, ecos, erros)."""
        saidas, ecos = [], []
        interp = interp or Interpretador(saida=saidas.append)
        interp.saida = saidas.append
        erros = rodar(self.linguagem, codigo, interp, eco=ecos.append)
        return interp, saidas, ecos, erros

    def ok(self, codigo):
        interp, saidas, ecos, erros = self.rodar(codigo)
        self.assertEqual(erros, [], [e.como_texto() for e in erros])
        return interp, saidas, ecos

    def erro(self, codigo, classe):
        _, _, _, erros = self.rodar(codigo)
        self.assertEqual(len(erros), 1)
        self.assertIsInstance(erros[0], classe)
        return erros[0]


class TestLinguagemCompleta(TestBase):
    def test_tokens_novos(self):
        tokens, erros = tokenizar(self.linguagem, "a = b == (c - 1) * 2 / 3 >= 4 != 5; { }")
        self.assertEqual(erros, [])
        self.assertEqual(
            [(t.tipo, t.lexema) for t in tokens][1:3], [("TT_ATRIB", "="), ("TT_IDENT", "b")]
        )
        self.assertIn(("TT_OP", "=="), [(t.tipo, t.lexema) for t in tokens])
        self.assertIn(("TT_OP", ">="), [(t.tipo, t.lexema) for t in tokens])
        self.assertIn(("TT_OP", "!="), [(t.tipo, t.lexema) for t in tokens])

    def test_palavras_reservadas(self):
        tokens, _ = tokenizar(self.linguagem, "se senao mostrar sex")
        self.assertEqual(
            [t.tipo for t in tokens], ["TT_SE", "TT_SENAO", "TT_MOSTRAR", "TT_IDENT"]
        )


class TestCalculos(TestBase):
    def valor(self, codigo):
        _, _, ecos = self.ok(codigo)
        return ecos[-1]

    def test_precedencia(self):
        self.assertEqual(self.valor("2 + 3 * 4"), 14)
        self.assertEqual(self.valor("(2 + 3) * 4"), 20)
        self.assertEqual(self.valor("2 * 3 + 4 * 5"), 26)

    def test_associatividade_a_esquerda(self):
        self.assertEqual(self.valor("7 - 2 - 1"), 4)
        self.assertEqual(self.valor("100 / 10 / 5"), 2)

    def test_unario(self):
        self.assertEqual(self.valor("-3 + 5"), 2)
        self.assertEqual(self.valor("2 * -3"), -6)
        self.assertEqual(self.valor("--4"), 4)

    def test_decimais(self):
        self.assertEqual(self.valor("0.5 + 1"), 1.5)
        self.assertIsInstance(self.valor("1.0 * 2"), float)

    def test_divisao(self):
        self.assertEqual(self.valor("10 / 2"), 5)
        self.assertIsInstance(self.valor("10 / 2"), int)
        self.assertEqual(self.valor("10 / 4"), 2.5)

    def test_divisao_por_zero(self):
        erro = self.erro("1 / 0", ErroExecucao)
        self.assertIn("divisão por zero", erro.mensagem)
        self.assertEqual((erro.linha, erro.coluna), (1, 3))

    def test_concatenacao_de_texto(self):
        self.assertEqual(self.valor('"ola, " + "mundo"'), "ola, mundo")

    def test_erro_de_tipos(self):
        self.assertIn("inteiro e texto", self.erro('1 + "a"', ErroExecucao).mensagem)
        self.assertIn("só funciona com números", self.erro('-"a"', ErroExecucao).mensagem)

    def test_comparacoes(self):
        self.assertIs(self.valor("3 < 5"), True)
        self.assertIs(self.valor("3 >= 5"), False)
        self.assertIs(self.valor("2 == 2.0"), True)
        self.assertIs(self.valor("2 != 3"), True)
        self.assertIs(self.valor('"a" < "b"'), True)
        self.assertIs(self.valor('1 == "1"'), False)
        self.assertIs(self.valor("(1 < 2) == (3 < 4)"), True)

    def test_comparacao_de_tipos_diferentes(self):
        self.assertIn("comparar", self.erro('1 < "a"', ErroExecucao).mensagem)

    def test_comparacao_nao_encadeia(self):
        self.erro("1 < 2 < 3", ErroSintatico)


class TestVariaveis(TestBase):
    def test_atribuicao_e_uso(self):
        interp, _, ecos = self.ok("x = 5\ny = x * 2 + 1\ny")
        self.assertEqual(interp.variaveis, {"x": 5, "y": 11})
        self.assertEqual(ecos, [11])

    def test_reatribuicao(self):
        interp, _, _ = self.ok("x = 1\nx = x + 1\nx = x * 10")
        self.assertEqual(interp.variaveis["x"], 20)

    def test_variavel_inexistente(self):
        erro = self.erro("x + 1", ErroExecucao)
        self.assertIn("'x' não foi definida", erro.mensagem)

    def test_variaveis_persistem_entre_execucoes(self):
        interp, _, _, _ = self.rodar("x = 7")
        _, _, ecos, erros = self.rodar("x * 2", interp)
        self.assertEqual(erros, [])
        self.assertEqual(ecos, [14])

    def test_variavel_de_texto(self):
        interp, saidas, _ = self.ok('nome = "Ana"\nmostrar "oi, " + nome')
        self.assertEqual(saidas, ["oi, Ana"])

    def test_nao_executa_nada_se_houver_erro_de_sintaxe(self):
        interp, _, _, erros = self.rodar("x = 1\ny = ")
        self.assertEqual(len(erros), 1)
        self.assertEqual(interp.variaveis, {})


class TestSe(TestBase):
    def test_se_verdadeiro(self):
        _, saidas, _ = self.ok('se 3 > 2 { mostrar "sim" } senao { mostrar "nao" }')
        self.assertEqual(saidas, ["sim"])

    def test_senao(self):
        _, saidas, _ = self.ok('se 1 > 2 { mostrar "sim" } senao { mostrar "nao" }')
        self.assertEqual(saidas, ["nao"])

    def test_se_sem_senao(self):
        _, saidas, _ = self.ok('se 1 > 2 { mostrar "sim" }\nmostrar "fim"')
        self.assertEqual(saidas, ["fim"])

    def test_senao_se(self):
        codigo = """
        nota = 7
        se nota >= 9 { mostrar "A" }
        senao se nota >= 7 { mostrar "B" }
        senao { mostrar "C" }
        """
        _, saidas, _ = self.ok(codigo)
        self.assertEqual(saidas, ["B"])

    def test_se_aninhado_e_atribuicao_no_bloco(self):
        codigo = """
        x = 10
        se x > 5 {
            se x > 8 { y = 1 } senao { y = 2 }
        } senao {
            y = 3
        }
        """
        interp, _, _ = self.ok(codigo)
        self.assertEqual(interp.variaveis["y"], 1)

    def test_condicao_com_ou_sem_parenteses(self):
        _, saidas, _ = self.ok('x = 4\nse (x == 4) { mostrar "a" }\nse x == 4 { mostrar "b" }')
        self.assertEqual(saidas, ["a", "b"])

    def test_condicao_numerica(self):
        _, saidas, _ = self.ok('se 0 { mostrar "a" } senao { mostrar "b" }\nse 2 { mostrar "c" }')
        self.assertEqual(saidas, ["b", "c"])

    def test_condicao_de_texto_e_erro(self):
        erro = self.erro('se "a" { mostrar 1 }', ErroExecucao)
        self.assertIn("texto", erro.mensagem)

    def test_expressao_solta_dentro_do_bloco_nao_faz_eco(self):
        _, _, ecos = self.ok("se 1 { 2 + 2 }")
        self.assertEqual(ecos, [])

    def test_mostrar_formata_valores(self):
        _, saidas, _ = self.ok('mostrar 1 < 2\nmostrar 2.5\nmostrar "oi"')
        self.assertEqual(saidas, ["verdadeiro", "2.5", "oi"])


class TestFimDeComando(TestBase):
    def test_operador_em_linha_nova_comeca_outro_comando(self):
        interp, _, ecos = self.ok("x = 5\n-3")
        self.assertEqual(interp.variaveis["x"], 5)
        self.assertEqual(ecos, [-3])

    def test_expressao_em_varias_linhas_dentro_de_parenteses(self):
        _, _, ecos = self.ok("(1 +\n 2 +\n 3)")
        self.assertEqual(ecos, [6])

    def test_ponto_e_virgula(self):
        interp, _, ecos = self.ok("x = 5 - 3; y = x; y")
        self.assertEqual(interp.variaveis, {"x": 2, "y": 2})
        self.assertEqual(ecos, [2])

    def test_comentarios_sao_ignorados(self):
        interp, _, _ = self.ok("x = 1 # um\n# dois\ny = 2")
        self.assertEqual(interp.variaveis, {"x": 1, "y": 2})


class TestErrosSintaticos(TestBase):
    def test_bloco_sem_fechar_pede_mais_codigo(self):
        erro = self.erro("se 1 > 0 {", ErroSintatico)
        self.assertTrue(erro.fim_inesperado)

    def test_expressao_incompleta_pede_mais_codigo(self):
        self.assertTrue(self.erro("x = ", ErroSintatico).fim_inesperado)
        self.assertTrue(self.erro("(1 + 2", ErroSintatico).fim_inesperado)

    def test_senao_solto(self):
        erro = self.erro("senao { }", ErroSintatico)
        self.assertFalse(erro.fim_inesperado)
        self.assertIn("sem um 'se'", erro.mensagem)

    def test_chave_sobrando(self):
        self.assertIn("sem um '{'", self.erro("}", ErroSintatico).mensagem)

    def test_se_sem_chave(self):
        erro = self.erro("se 1 > 0 mostrar 1", ErroSintatico)
        self.assertIn("esperava '{'", erro.mensagem)

    def test_token_inesperado(self):
        erro = self.erro("x = * 3", ErroSintatico)
        self.assertEqual((erro.linha, erro.coluna), (1, 5))

    def test_mensagem_com_seta(self):
        _, _, _, erros = self.rodar("x = 1\ny = * 2")
        texto = erros[0].como_texto()
        self.assertIn("linha 2, coluna 5", texto)
        self.assertIn("y = * 2", texto)


class TestErrosLexicosNaExecucao(TestBase):
    def test_erro_lexico_impede_a_execucao(self):
        interp, _, _, erros = self.rodar("x = 5 @")
        self.assertEqual(len(erros), 1)
        self.assertIn("caractere desconhecido", erros[0].mensagem)
        self.assertEqual(interp.variaveis, {})


if __name__ == "__main__":
    unittest.main()
