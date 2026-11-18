from decimal import Decimal

class SaldoContratualInsuficienteException(Exception):
    def __init__(self, saldo_disponivel: Decimal, valor_fatura: Decimal):
        self.saldo_disponivel = saldo_disponivel
        self.valor_fatura = valor_fatura
        self.excedente = valor_fatura - saldo_disponivel
        super().__init__(
            f"Operação Bloqueada: Valor da fatura (R$ {valor_fatura:,.2f}) excede o saldo remanescente disponível (R$ {saldo_disponivel:,.3f}). Excedente: R$ {self.excedente:,.2f}."
        )

class ChecklistInvalidoException(Exception):
    pass
