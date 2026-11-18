import pytest
from decimal import Decimal
from datetime import date
from domain.models import ContratoModel, NotaFiscalModel
from domain.exceptions import SaldoContratualInsuficienteException, ChecklistInvalidoException
from domain.services import GestaoContratosService

class MockRepository:
    def __init__(self):
        self.contrato = ContratoModel(
            id_contrato=3,
            numero_processo="2026/042",
            objeto="Serviços de Limpeza",
            razao_social_fornecedor="LimpServ",
            cnpj_fornecedor="12.345.678/0001-90",
            data_inicio_vigencia=date(2026, 1, 1),
            data_fim_vigencia=date(2026, 12, 31),
            valor_global_inicial=Decimal("120000.00"),
            saldo_remanescente_atual=Decimal("15000.00"),
            status="Ativo"
        )
        self.faturas_salvas = []

    def obter_contrato_por_id(self, id_contrato: int):
        return self.contrato if id_contrato == 1 else None

    def salvar_fatura_e_atualizar_saldo(self, fatura: NotaFiscalModel, novo_saldo: Decimal):
        self.faturas_salvas.append(fatura)
        self.contrato.saldo_remanescente_atual = novo_saldo

def test_bloqueio_saldo_insuficiente():
    repo = MockRepository()
    service = GestaoContratosService(repo)

    fatura = NotaFiscalModel(
        id_contrato=1,
        numero_nf="000.142",
        data_emissao=date(2026, 11, 10),
        data_recebimento=date(2026, 11, 14),
        valor_bruto=Decimal("18500.00"),
        checklist_conformidade=True
    )

    with pytest.raises(SaldoContratualInsuficienteException) as exc:
        service.lancar_e_atestar_fatura(fatura)

    assert exc.value.saldo_disponivel == Decimal("15000.00")
    assert exc.value.valor_fatura == Decimal("18500.00")
    assert exc.value.excedente == Decimal("3500.00")
    assert repo.contrato.saldo_remanescente_atual == Decimal("15000.00")

def test_atesto_sucesso_com_amortizacao_saldo():
    repo = MockRepository()
    service = GestaoContratosService(repo)

    fatura = NotaFiscalModel(
        id_contrato=1,
        numero_nf="000.143",
        data_emissao=date(2026, 11, 10),
        data_recebimento=date(2026, 11, 14),
        valor_bruto=Decimal("8000.00"),
        checklist_conformidade=True
    )

    contrato_pos = service.lancar_e_atestar_fatura(fatura)
    assert contrato_pos.saldo_remanescente_atual == Decimal("7000.00")
    assert len(repo.faturas_salvas) == 1
