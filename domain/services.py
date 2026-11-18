from decimal import Decimal
from typing import List, Optional
from domain.models import ContratoModel, NotaFiscalModel
from domain.exceptions import SaldoContratualInsuficienteException, ChecklistInvalidoException

class GestaoContratosService:
    def __init__(self, repository):
        self.repo = repository

    def listar_contratos(self) -> List[ContratoModel]:
        return self.repo.listar_contratos()

    def obter_contrato(self, id_contrato: int) -> Optional[ContratoModel]:
        return self.repo.obter_contrato_por_id(id_contrato)

    def lancar_e_atestar_fatura(self, fatura: NotaFiscalModel) -> ContratoModel:
        if not fatura.checklist_conformidade:
            raise ChecklistInvalidoException("Atesto negado: relatório de medição e certidões negativas são obrigatórios.")

        contrato = self.repo.obter_contrato_por_id(fatura.id_contrato)
        if not contrato:
            raise ValueError("Contrato não encontrado.")

        if contrato.status != 'Ativo':
            raise ValueError("Não é permitido lançar notas para contratos que não estejam ativos.")

        # Trava impeditiva de saldo disponivel
        if fatura.valor_bruto > contrato.saldo_remanescente_atual:
            raise SaldoContratualInsuficienteException(
                saldo_disponivel=contrato.saldo_remanescente_atual,
                valor_fatura=fatura.valor_bruto
            )

        # Atualização atômica
        novo_saldo = contrato.saldo_remanescente_atual - fatura.valor_bruto
        self.repo.salvar_fatura_e_atualizar_saldo(fatura, novo_saldo)
        
        contrato.saldo_remanescente_atual = novo_saldo
        return contrato
