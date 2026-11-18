# why — Gestão e Trava Orçamentária de Contratos

Aplicação desktop nativa desenvolvida para a fiscalização físico-financeira de contratos de serviços continuados da **Câmara Municipal de Barão de Cocais (MG)**, garantindo conformidade com a **Lei nº 14.133/2021** e as diretrizes do Tribunal de Contas (TCE-MG).

## Arquitetura e Tecnologias
- **Arquitetura:** Monólito em 3 Camadas (Apresentação, Regras de Negócio, Persistência Local).
- **Linguagem & Runtime:** Python 3.12 (CPython).
- **Interface Gráfica (GUI):** CustomTkinter (tema escuro de alto contraste, foco em produtividade via teclado numérico e atalhos).
- **Validação de Domínio:** Pydantic 2.x com tipagem estática e exceções semânticas.
- **Banco de Dados:** SQLite 3 nativo embarcado via C-API (`sqlite3`), integridade referencial mandatória e WAL habilitado.
- **Testes Automatizados:** pytest.

## 🛠 Instalação e Execução

```bash
# 1. Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # No Windows: .venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar suíte de testes unitários
pytest tests/

# 4. Iniciar a aplicação desktop
python app.py
```
