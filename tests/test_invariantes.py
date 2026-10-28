"""Testes = as mesmas portas do pipeline + idempotência da carga.

    python -m unittest -v
Pressupõe o pipeline já executado (`python -m src.pipeline`).
"""
import sqlite3
import unittest

from src import carregar_sor, config as C, portas


class Invariantes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con = sqlite3.connect(C.BANCO)

    def test_stage_igual_sor(self):
        self.assertTrue(portas.stage_igual_sor(self.con))

    def test_nenhum_titulo_cancelado_no_sot(self):
        self.assertGreater(portas.nenhum_titulo_cancelado_no_sot(self.con), 0)

    def test_fluxo_da_base_fecha(self):
        self.assertGreater(portas.fluxo_da_base_fecha(self.con), 0)

    def test_faixas_somam_o_total(self):
        self.assertGreater(portas.faixas_somam_o_total(self.con), 0)

    def test_churn_total_e_soma_das_filiais(self):
        self.assertGreater(portas.churn_total_e_soma_das_filiais(self.con), 0)

    def test_ativacoes_batem_com_a_base(self):
        self.assertGreater(portas.ativacoes_batem_com_a_base(self.con), 0)

    def test_faturas_canceladas_existem_no_sor_e_algumas_sao_negativas(self):
        """A armadilha está na base: se alguém somar sem filtrar status, o número sai errado."""
        q, neg = self.con.execute("SELECT count(*), SUM(valor < 0) FROM sor_fatura WHERE status = 'C'").fetchone()
        self.assertGreater(q, 0)
        self.assertGreater(neg, 0)

    def test_titularidade_nao_e_perda(self):
        q = self.con.execute("SELECT count(*) FROM sot_contrato WHERE motivo_cancelamento = 'TROCA DE TITULARIDADE' AND perda_cliente = 1").fetchone()[0]
        self.assertEqual(q, 0)


class Idempotencia(unittest.TestCase):
    def test_carregar_duas_vezes_da_o_mesmo(self):
        con = sqlite3.connect(C.BANCO)
        foto = lambda: con.execute("SELECT count(*), ROUND(SUM(valor), 2), MAX(id_fatura) FROM sor_fatura").fetchone()  # noqa: E731
        antes = foto()
        carregar_sor.carregar(con)
        self.assertEqual(antes, foto())
        carregar_sor.carregar(con)
        self.assertEqual(antes, foto())


if __name__ == "__main__":
    unittest.main()
