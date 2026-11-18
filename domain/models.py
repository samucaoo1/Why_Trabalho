from decimal import Decimal
from datetime import date
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

class ContratoModel(BaseModel):
    id_contrato: Optional[int] = None
    numero_processo: str = Field(..., min_length=1)
    objeto: str = Field(..., min_length=1)
    razao_social_fornecedor: str = Field(..., min_length=1)
    cnpj_fornecedor: str = Field(..., min_length=14)
    data_inicio_vigencia: date
    data_fim_vigencia: date
    valor_global_inicial: Decimal = Field(..., gt=0)
    saldo_remanescente_atual: Decimal = Field(..., ge=0)
    status: Literal['Ativo', 'Encerrado', 'Suspenso'] = 'Ativo'

    @field_validator('data_fim_vigencia')
    @classmethod
    def validar_datas(cls, v: date, info):
        inicio = info.data.get('data_inicio_vigencia')
        if inicio and v < inicio:
            raise ValueError('A data de fim de vigência deve ser posterior à data de início.')
        return v

class NotaFiscalModel(BaseModel):
    id_nota: Optional[int] = None
    id_contrato: int
    numero_nf: str = Field(..., min_length=1)
    data_emissao: date
    data_recebimento: date
    valor_bruto: Decimal = Field(..., gt=0)
    valor_retencoes: Decimal = Field(default=Decimal('0.00'), ge=0)
    status_operacional: Literal['Recebida', 'Em Análise', 'Atestada', 'Glosada', 'Liberada para Pagamento'] = 'Atestada'
    checklist_conformidade: bool = Field(...)

    @field_validator('checklist_conformidade')
    @classmethod
    def validar_checklist(cls, v: bool):
        if not v:
            raise ValueError('O checklist de conformidade documental (medição e certidões) é obrigatório.')
        return v
