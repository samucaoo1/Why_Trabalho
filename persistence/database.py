import sqlite3
from decimal import Decimal
from typing import List, Optional
from datetime import date
from domain.models import ContratoModel, NotaFiscalModel

sqlite3.register_adapter(Decimal, lambda d: str(d))
sqlite3.register_converter("DECIMAL", lambda s: Decimal(s.decode('utf-8')))

class SQLiteRepository:
    def __init__(self, db_path: str = "why_database.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            timeout=5.0
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contrato (
                    id_contrato INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_processo TEXT NOT NULL UNIQUE,
                    objeto TEXT NOT NULL,
                    razao_social_fornecedor TEXT NOT NULL,
                    cnpj_fornecedor TEXT NOT NULL,
                    data_inicio_vigencia DATE NOT NULL,
                    data_fim_vigencia DATE NOT NULL,
                    valor_global_inicial DECIMAL NOT NULL,
                    saldo_remanescente_atual DECIMAL NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('Ativo', 'Encerrado', 'Suspenso'))
                );
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nota_fiscal (
                    id_nota INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_contrato INTEGER NOT NULL,
                    numero_nf TEXT NOT NULL,
                    data_emissao DATE NOT NULL,
                    data_recebimento DATE NOT NULL,
                    valor_bruto DECIMAL NOT NULL,
                    valor_retencoes DECIMAL NOT NULL DEFAULT 0.0,
                    status_operacional TEXT NOT NULL,
                    checklist_conformidade INTEGER NOT NULL,
                    FOREIGN KEY (id_contrato) REFERENCES contrato(id_contrato) ON DELETE RESTRICT,
                    UNIQUE(id_contrato, numero_nf)
                );
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_nf_contrato ON nota_fiscal(id_contrato);
            ''')
            conn.commit()

    def seed_initial_data(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM contrato;")
            if cursor.fetchone()['count'] == 0:
                mock_contratos = [
                    ('2025/115', 'Serviços de Manutenção e TI', 'TecnoInfor LTDA', '11.222.333/0001-44', '2025-01-01', '2026-12-31', '100000.00', '15000.00', 'Ativo'),
                    ('2026/042', 'Serviços de Limpeza e Conservação', 'LimpServ Serviços Gerais Ltda', '12.345.678/0001-90', '2026-01-01', '2026-12-31', '120000.00', '15000.00', 'Ativo'),
                    ('2026/008', 'Serviços de Segurança Patrimonial', 'Segur Segurança LTDA', '99.888.777/0001-11', '2026-02-01', '2027-01-31', '35000.00', '10000.00', 'Ativo'),
                    ('2026/017', 'Consultoria e Apoio Técnico', 'Tecno Serviços LTDA', '44.555.666/0001-22', '2026-03-01', '2026-09-30', '13000.00', '35000.00', 'Encerrado'),
                    ('2026/034', 'Serviços de Manutenção Predial', 'Segur Manutenções', '33.222.111/0001-88', '2026-04-01', '2026-10-31', '13000.00', '10000.00', 'Encerrado')
                ]
                cursor.executemany('''
                    INSERT INTO contrato (
                        numero_processo, objeto, razao_social_fornecedor, cnpj_fornecedor,
                        data_inicio_vigencia, data_fim_vigencia, valor_global_inicial,
                        saldo_remanescente_atual, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                ''', mock_contratos)
                conn.commit()

    def listar_contratos(self) -> List[ContratoModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contrato ORDER BY id_contrato ASC;")
            rows = cursor.fetchall()
            return [
                ContratoModel(
                    id_contrato=r['id_contrato'],
                    numero_processo=r['numero_processo'],
                    objeto=r['objeto'],
                    razao_social_fornecedor=r['razao_social_fornecedor'],
                    cnpj_fornecedor=r['cnpj_fornecedor'],
                    data_inicio_vigencia=date.fromisoformat(r['data_inicio_vigencia']) if isinstance(r['data_inicio_vigencia'], str) else r['data_inicio_vigencia'],
                    data_fim_vigencia=date.fromisoformat(r['data_fim_vigencia']) if isinstance(r['data_fim_vigencia'], str) else r['data_fim_vigencia'],
                    valor_global_inicial=Decimal(str(r['valor_global_inicial'])),
                    saldo_remanescente_atual=Decimal(str(r['saldo_remanescente_atual'])),
                    status=r['status']
                )
                for r in rows
            ]

    def obter_contrato_por_id(self, id_contrato: int) -> Optional[ContratoModel]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contrato WHERE id_contrato = ?;", (id_contrato,))
            r = cursor.fetchone()
            if not r:
                return None
            return ContratoModel(
                id_contrato=r['id_contrato'],
                numero_processo=r['numero_processo'],
                objeto=r['objeto'],
                razao_social_fornecedor=r['razao_social_fornecedor'],
                cnpj_fornecedor=r['cnpj_fornecedor'],
                data_inicio_vigencia=date.fromisoformat(r['data_inicio_vigencia']) if isinstance(r['data_inicio_vigencia'], str) else r['data_inicio_vigencia'],
                data_fim_vigencia=date.fromisoformat(r['data_fim_vigencia']) if isinstance(r['data_fim_vigencia'], str) else r['data_fim_vigencia'],
                valor_global_inicial=Decimal(str(r['valor_global_inicial'])),
                saldo_remanescente_atual=Decimal(str(r['saldo_remanescente_atual'])),
                status=r['status']
            )

    def salvar_fatura_e_atualizar_saldo(self, fatura: NotaFiscalModel, novo_saldo: Decimal):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Inserir fatura
            cursor.execute('''
                INSERT INTO nota_fiscal (
                    id_contrato, numero_nf, data_emissao, data_recebimento,
                    valor_bruto, valor_retencoes, status_operacional, checklist_conformidade
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            ''', (
                fatura.id_contrato,
                fatura.numero_nf,
                fatura.data_emissao.isoformat(),
                fatura.data_recebimento.isoformat(),
                str(fatura.valor_bruto),
                str(fatura.valor_retencoes),
                fatura.status_operacional,
                1 if fatura.checklist_conformidade else 0
            ))
            # 2. Atualizar saldo do contrato
            cursor.execute('''
                UPDATE contrato
                SET saldo_remanescente_atual = ?
                WHERE id_contrato = ?;
            ''', (str(novo_saldo), fatura.id_contrato))
            conn.commit()
