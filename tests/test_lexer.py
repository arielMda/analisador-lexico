# Testes do núcleo do lexer (lexer/lexer.py), usando a linguagem de teste em tests/fixtures.
# Rodar da raiz do projeto: python3 -m unittest discover tests

import unittest
from pathlib import Path

from lexer import ErroAutomato, Linguagem, tokenizar

FIXTURES = Path(__file__).parent / "fixtures"


class TestLexer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.linguagem = Linguagem.de_arquivo(FIXTURES / "linguagem.json")

    def tipos(self, texto):
        tokens, erros = tokenizar(self.linguagem, texto)
        self.assertEqual(erros, [])
        return [(t.tipo, t.lexema) for t in tokens]

    def test_texto_vazio(self):
        self.assertEqual(tokenizar(self.linguagem, ""), ([], []))
        self.assertEqual(tokenizar(self.linguagem, "  \n\t "), ([], []))

    def test_maior_casamento(self):
        # "<=" é um token só, e "3.14" é float, não inteiro + "." + inteiro
        self.assertEqual(
            self.tipos("a<=3.14"),
            [("TT_IDENT", "a"), ("TT_OP", "<="), ("TT_FLOAT", "3.14")],
        )

    def test_palavras_reservadas(self):
        self.assertEqual(
            self.tipos("se senao sex"),
            [("TT_SE", "se"), ("TT_SENAO", "senao"), ("TT_IDENT", "sex")],
        )

    def test_valores_convertidos(self):
        tokens, _ = tokenizar(self.linguagem, '42 2.5 "oi"')
        self.assertEqual([t.valor for t in tokens], [42, 2.5, "oi"])

    def test_comentario_ignorado(self):
        self.assertEqual(self.tipos("x # isso é ignorado\ny"), [("TT_IDENT", "x"), ("TT_IDENT", "y")])

    def test_linha_e_coluna(self):
        tokens, _ = tokenizar(self.linguagem, "a\n  b")
        self.assertEqual([(t.linha, t.coluna) for t in tokens], [(1, 1), (2, 3)])

    def test_caminho_de_estados(self):
        tokens, _ = tokenizar(self.linguagem, "<=")
        self.assertEqual([p.destino for p in tokens[0].passos], ["menor", "menor_igual"])

    def test_continua_depois_do_erro(self):
        tokens, erros = tokenizar(self.linguagem, "a @@ b $ c")
        self.assertEqual([t.lexema for t in tokens], ["a", "b", "c"])
        self.assertEqual([(e.lexema, e.coluna) for e in erros], [("@@", 3), ("$", 8)])

    def test_token_incompleto(self):
        tokens, erros = tokenizar(self.linguagem, 'x = "sem fim\ny')
        self.assertEqual(len(erros), 2)  # "=" sozinho não existe e a string não fecha
        self.assertIn("incompleto", erros[1].mensagem)
        self.assertEqual(erros[1].lexema, '"sem fim')
        self.assertEqual([t.lexema for t in tokens], ["x", "y"])

    def test_mensagem_de_erro(self):
        _, erros = tokenizar(self.linguagem, "a @ b", arquivo="prog.txt")
        texto = erros[0].como_texto()
        self.assertIn("prog.txt, linha 1, coluna 3", texto)
        self.assertIn("a @ b", texto)


class TestLinguagem(unittest.TestCase):
    def test_linguagem_inexistente(self):
        with self.assertRaisesRegex(ErroAutomato, "não encontrado"):
            Linguagem.de_arquivo(FIXTURES / "nao_existe.json")


if __name__ == "__main__":
    unittest.main()
