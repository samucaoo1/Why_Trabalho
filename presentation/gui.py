import customtkinter as ctk
from decimal import Decimal, InvalidOperation
from datetime import date
from typing import Optional

from domain.models import ContratoModel, NotaFiscalModel
from domain.exceptions import SaldoContratualInsuficienteException, ChecklistInvalidoException
from domain.services import GestaoContratosService

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self, service: GestaoContratosService):
        super().__init__()
        self.service = service
        self.title("why - Gestão de Contratos e Faturas")
        self.geometry("1100x680")
        self.minsize(980, 600)
        self.configure(fg_color="#1E1E2E")

        self.contratos_cache = []
        self.selected_contract: Optional[ContratoModel] = None
        self.auto_contrast = False

        self._setup_topbar()
        self._setup_main_container()
        self.mostrar_dashboard()

        # Atalhos globais
        self.bind("<Alt-s>", lambda e: self.quit())
        self.bind("<Alt-S>", lambda e: self.quit())

    def _setup_topbar(self):
        topbar = ctk.CTkFrame(self, height=56, fg_color="#181825", corner_radius=0)
        topbar.pack(fill="x", side="top")

        title_lbl = ctk.CTkLabel(
            topbar,
            text="why   |   Gestão de Contratos e Faturas",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#FFFFFF"
        )
        title_lbl.pack(side="left", padx=24)

        self.btn_contraste = ctk.CTkButton(
            topbar,
            text="Alto contraste: desligado",
            height=36,
            fg_color="#313244",
            hover_color="#45475A",
            text_color="#CDD6F4",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._toggle_auto_contrast
        )
        self.btn_contraste.pack(side="right", padx=8)

        btn_sair = ctk.CTkButton(
            topbar,
            text="Sair [Alt+S]",
            height=36,
            fg_color="#313244",
            hover_color="#45475A",
            text_color="#CDD6F4",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self.quit
        )
        btn_sair.pack(side="right", padx=16)

        user_badge = ctk.CTkLabel(
            topbar,
            text="👤 Operador: Fiscal Administrativo",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#BAC2DE"
        )
        user_badge.pack(side="right", padx=12)

    def _toggle_auto_contrast(self):
        self.auto_contrast = not self.auto_contrast
        self.btn_contraste.configure(
            text="Alto contraste: ligado" if self.auto_contrast else "Alto contraste: desligado"
        )
        self._apply_auto_contrast(self)

    def _apply_auto_contrast(self, parent):
        # Reaplica uma paleta de alto contraste sem alterar os dados ou a lógica.
        palette = {
            "#1E1E2E": "#000000",
            "#181825": "#080808",
            "#2A2A3C": "#181818",
            "#313244": "#252525",
            "#45475A": "#777777",
            "#3B3B52": "#555555",
            "#144A75": "#003B70",
            "#1F6AA5": "#005FCC",
            "#89DCEB": "#00FFFF",
            "#A6ADC8": "#E8E8E8",
            "#BAC2DE": "#FFFFFF",
            "#CDD6F4": "#FFFFFF",
            "#FFFFFF": "#FFFFFF",
            "#A6E3A1": "#00FF66",
            "#F38BA8": "#FF6666",
            "#F9E2AF": "#FFFF00",
        }
        normalized_palette = {key.lower(): value for key, value in palette.items()}
        for widget in parent.winfo_children():
            try:
                for option in ("fg_color", "text_color", "border_color", "hover_color",
                               "placeholder_text_color", "button_color", "button_hover_color"):
                    current = widget.cget(option)
                    if isinstance(current, str) and current.lower() in normalized_palette:
                        widget.configure(**{option: normalized_palette[current.lower()]})
            except (KeyError, TypeError, ValueError):
                pass
            self._apply_auto_contrast(widget)

    def _setup_main_container(self):
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=24, pady=16)

    def limpar_conteudo(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # ==================== TELA 1: DASHBOARD ====================
    def mostrar_dashboard(self):
        self.limpar_conteudo()
        self.selected_contract = None

        # Filtro de busca
        filter_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 12))

        lbl_busca = ctk.CTkLabel(filter_frame, text="Buscar Processo/Fornecedor:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#A6ADC8")
        lbl_busca.pack(side="left", padx=(0, 8))

        self.entry_busca = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Digite o processo administrativo ou razão social...",
            width=360,
            height=38,
            fg_color="#313244",
            border_color="#45475A"
        )
        self.entry_busca.pack(side="left")
        self.entry_busca.bind("<KeyRelease>", self._filtrar_tabela)

        # Tabela / Grid
        self.table_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="#181825", corner_radius=8, border_width=1, border_color="#313244")
        self.table_frame.pack(fill="both", expand=True, pady=(0, 16))

        # Cabeçalho da tabela
        headers = ["Processo", "Fornecedor", "Objeto", "Valor Global", "Saldo Remanescente", "Status"]
        header_frame = ctk.CTkFrame(self.table_frame, fg_color="#2A2A3C", height=38, corner_radius=4)
        header_frame.pack(fill="x", padx=4, pady=4)

        weights = [120, 220, 200, 140, 140, 100]
        for idx, (title, w) in enumerate(zip(headers, weights)):
            lbl = ctk.CTkLabel(header_frame, text=title, width=w, anchor="w" if idx < 3 else "e", font=ctk.CTkFont(size=12, weight="bold"), text_color="#89DCEB")
            lbl.pack(side="left", padx=8, pady=6)

        self.rows_container = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        self.rows_container.pack(fill="both", expand=True)

        self.contratos_cache = self.service.listar_contratos()
        self._render_rows(self.contratos_cache)

        # Barra inferior com ação principal
        bottom_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", side="bottom")

        self.btn_lancar = ctk.CTkButton(
            bottom_frame,
            text="Lançar / Atestar Fatura [Enter]",
            height=46,
            fg_color="#1F6AA5",
            hover_color="#144A75",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self._acao_lancar_fatura
        )
        self.btn_lancar.pack(side="right")

        self.bind("<Return>", lambda e: self._acao_lancar_fatura())
        if self.auto_contrast:
            self._apply_auto_contrast(self)

    def _render_rows(self, contratos):
        for w in self.rows_container.winfo_children():
            w.destroy()

        self.row_widgets = []
        for c in contratos:
            row = ctk.CTkFrame(
                self.rows_container,
                height=48,
                fg_color="#313244" if (self.selected_contract and self.selected_contract.id_contrato == c.id_contrato) else "#2A2A3C",
                border_width=2 if (self.selected_contract and self.selected_contract.id_contrato == c.id_contrato) else 0,
                border_color="#1F6AA5",
                corner_radius=6
            )
            row.pack(fill="x", padx=4, pady=4)
            row.pack_propagate(False)

            # Conteúdo da linha; o frame permite organizar os campos sem
            # conflitar com o gerenciador interno de geometria do CTkButton.
            lbl_proc = ctk.CTkLabel(row, text=c.numero_processo, width=120, anchor="w", font=ctk.CTkFont(weight="bold"))
            lbl_proc.pack(side="left", padx=8)

            lbl_forn = ctk.CTkLabel(row, text=c.razao_social_fornecedor, width=220, anchor="w")
            lbl_forn.pack(side="left", padx=8)

            lbl_obj = ctk.CTkLabel(row, text=c.objeto[:24] + "...", width=200, anchor="w", text_color="#A6ADC8")
            lbl_obj.pack(side="left", padx=8)

            lbl_global = ctk.CTkLabel(row, text=f"R$ {c.valor_global_inicial:,.2f}", width=140, anchor="e")
            lbl_global.pack(side="left", padx=8)

            lbl_saldo = ctk.CTkLabel(row, text=f"R$ {c.saldo_remanescente_atual:,.2f}", width=140, anchor="e", font=ctk.CTkFont(weight="bold"), text_color="#A6E3A1")
            lbl_saldo.pack(side="left", padx=8)

            status_color = "#A6E3A1" if c.status == "Ativo" else "#F38BA8"
            lbl_status = ctk.CTkLabel(row, text=c.status, width=100, anchor="e", text_color=status_color)
            lbl_status.pack(side="left", padx=8)

            # Mantém a seleção acessível clicando em qualquer ponto da linha.
            selecionar = lambda event, item=c: self._selecionar_contrato(item)
            row.bind("<Button-1>", selecionar)
            for label in (lbl_proc, lbl_forn, lbl_obj, lbl_global, lbl_saldo, lbl_status):
                label.bind("<Button-1>", selecionar)

            self.row_widgets.append((c, row))

        # Selecionar o contrato 2026/042 por padrão se disponível
        if not self.selected_contract and contratos:
            p42 = next((c for c in contratos if c.numero_processo == '2026/042'), contratos[0])
            self._selecionar_contrato(p42)

        if self.auto_contrast:
            self._apply_auto_contrast(self.rows_container)

    def _selecionar_contrato(self, contrato: ContratoModel):
        self.selected_contract = contrato
        for c, widget in self.row_widgets:
            if c.id_contrato == contrato.id_contrato:
                widget.configure(border_width=2, border_color="#1F6AA5", fg_color="#313244")
            else:
                widget.configure(border_width=0, fg_color="#2A2A3C")

    def _filtrar_tabela(self, event=None):
        termo = self.entry_busca.get().lower()
        filtrados = [
            c for c in self.contratos_cache
            if termo in c.numero_processo.lower() or termo in c.razao_social_fornecedor.lower() or termo in c.objeto.lower()
        ]
        self._render_rows(filtrados)

    def _acao_lancar_fatura(self):
        if not self.selected_contract:
            return
        self.unbind("<Return>")
        self.mostrar_tela_lancamento(self.selected_contract)

    # ==================== TELA 2: LANÇAMENTO ====================
    def mostrar_tela_lancamento(self, contrato: ContratoModel):
        self.limpar_conteudo()

        # Cabeçalho Fixo Resumo
        header_card = ctk.CTkFrame(self.content_frame, fg_color="#2A2A3C", corner_radius=8, height=64)
        header_card.pack(fill="x", pady=(0, 20), padx=8)

        lbl_resumo_p = ctk.CTkLabel(header_card, text=f"Processo: {contrato.numero_processo}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#FFFFFF")
        lbl_resumo_p.pack(side="left", padx=20, pady=16)

        lbl_resumo_f = ctk.CTkLabel(header_card, text=f"|   {contrato.razao_social_fornecedor}", font=ctk.CTkFont(size=14), text_color="#BAC2DE")
        lbl_resumo_f.pack(side="left", padx=10, pady=16)

        lbl_resumo_s = ctk.CTkLabel(
            header_card,
            text=f"Saldo Disponível: R$ {contrato.saldo_remanescente_atual:,.2f}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#89DCEB"
        )
        lbl_resumo_s.pack(side="right", padx=20, pady=16)

        # Formulário Central
        form_card = ctk.CTkFrame(self.content_frame, fg_color="#181825", corner_radius=8, width=540)
        form_card.pack(expand=True, pady=10, padx=8)

        form_inner = ctk.CTkFrame(form_card, fg_color="transparent")
        form_inner.pack(padx=32, pady=24)

        # Campo 1: Número NF
        ctk.CTkLabel(form_inner, text="Número da NF:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#CDD6F4").grid(row=0, column=0, sticky="w", pady=(8, 2))
        self.ent_nf = ctk.CTkEntry(form_inner, width=440, height=38, fg_color="#313244", border_color="#45475A")
        self.ent_nf.insert(0, "000.142")
        self.ent_nf.grid(row=1, column=0, sticky="w", pady=(0, 8))

        # Campo 2 e 3: Datas
        datas_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        datas_frame.grid(row=2, column=0, sticky="w", pady=4)

        ctk.CTkLabel(datas_frame, text="Data de Emissão (AAAA-MM-DD):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CDD6F4").pack(side="left")
        ctk.CTkLabel(datas_frame, text="Data de Recebimento:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#CDD6F4").pack(side="left", padx=(60, 0))

        datas_inputs = ctk.CTkFrame(form_inner, fg_color="transparent")
        datas_inputs.grid(row=3, column=0, sticky="w", pady=(0, 8))

        self.ent_emissao = ctk.CTkEntry(datas_inputs, width=210, height=38, fg_color="#313244", border_color="#45475A")
        self.ent_emissao.insert(0, "2026-11-10")
        self.ent_emissao.pack(side="left", padx=(0, 20))

        self.ent_recebimento = ctk.CTkEntry(datas_inputs, width=210, height=38, fg_color="#313244", border_color="#45475A")
        self.ent_recebimento.insert(0, "2026-11-14")
        self.ent_recebimento.pack(side="left")

        # Campo 4: Valor Bruto
        ctk.CTkLabel(form_inner, text="Valor Bruto (R$):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#CDD6F4").grid(row=4, column=0, sticky="w", pady=(8, 2))
        self.ent_valor = ctk.CTkEntry(form_inner, width=440, height=38, fg_color="#313244", border_color="#45475A")
        self.ent_valor.insert(0, "18500.00")
        self.ent_valor.grid(row=5, column=0, sticky="w", pady=(0, 8))

        # Campo 5: Retenções
        ctk.CTkLabel(form_inner, text="Retenções Legais (R$):", font=ctk.CTkFont(size=13, weight="bold"), text_color="#CDD6F4").grid(row=6, column=0, sticky="w", pady=(8, 2))
        self.ent_retencoes = ctk.CTkEntry(form_inner, width=440, height=38, fg_color="#313244", border_color="#45475A")
        self.ent_retencoes.insert(0, "0.00")
        self.ent_retencoes.grid(row=7, column=0, sticky="w", pady=(0, 12))

        # Checkbox Conformidade
        self.var_checklist = ctk.BooleanVar(value=True)
        self.chk_conf = ctk.CTkCheckBox(
            form_inner,
            text="Atesto relatório de medição aprovado e certidões negativas válidas",
            variable=self.var_checklist,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A6E3A1",
            checkbox_width=24,
            checkbox_height=24
        )
        self.chk_conf.grid(row=8, column=0, sticky="w", pady=(4, 20))

        # Botões de Ação
        actions_frame = ctk.CTkFrame(form_inner, fg_color="transparent")
        actions_frame.grid(row=9, column=0, sticky="ew")

        btn_cancelar = ctk.CTkButton(
            actions_frame,
            text="Cancelar [Esc]",
            width=140,
            height=44,
            fg_color="#313244",
            hover_color="#45475A",
            text_color="#CDD6F4",
            command=self.mostrar_dashboard
        )
        btn_cancelar.pack(side="left")

        btn_processar = ctk.CTkButton(
            actions_frame,
            text="Processar e Atestar [Enter]",
            width=280,
            height=44,
            fg_color="#1F6AA5",
            hover_color="#144A75",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self._submeter_fatura(contrato)
        )
        btn_processar.pack(side="right")

        self.bind("<Return>", lambda e: self._submeter_fatura(contrato))
        self.bind("<Escape>", lambda e: self.mostrar_dashboard())
        if self.auto_contrast:
            self._apply_auto_contrast(self)

    def _submeter_fatura(self, contrato: ContratoModel):
        try:
            val_bruto = Decimal(self.ent_valor.get().replace(",", "."))
            val_ret = Decimal(self.ent_retencoes.get().replace(",", "."))
            fatura = NotaFiscalModel(
                id_contrato=contrato.id_contrato,
                numero_nf=self.ent_nf.get().strip(),
                data_emissao=date.fromisoformat(self.ent_emissao.get().strip()),
                data_recebimento=date.fromisoformat(self.ent_recebimento.get().strip()),
                valor_bruto=val_bruto,
                valor_retencoes=val_ret,
                status_operacional='Atestada',
                checklist_conformidade=self.var_checklist.get()
            )

            # Executa validação de domínio e persistência
            contrato_atualizado = self.service.lancar_e_atestar_fatura(fatura)
            self._mostrar_modal_sucesso(contrato_atualizado, val_bruto)

        except SaldoContratualInsuficienteException as e:
            self._mostrar_modal_bloqueio(e.saldo_disponivel, e.valor_fatura, e.excedente)
        except ChecklistInvalidoException as e:
            self._mostrar_alerta_generico("[!] Atesto Não Permitido", str(e))
        except (InvalidOperation, ValueError) as e:
            self._mostrar_alerta_generico("[!] Erro de Formatação", f"Inconsistência nos dados preenchidos: {str(e)}")

    # ==================== TELA 3: MODAL DE ALERTA / RESULTADO ====================
    def _mostrar_modal_bloqueio(self, saldo: Decimal, valor: Decimal, excedente: Decimal):
        modal = ctk.CTkToplevel(self)
        modal.title("Bloqueio Orçamentário")
        modal.geometry("520x360")
        modal.configure(fg_color="#1E1E2E")
        modal.grab_set()
        modal.resizable(False, False)

        inner = ctk.CTkFrame(modal, fg_color="#2A2A3C", corner_radius=10, border_width=2, border_color="#F38BA8")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        # Header com ícone semântico
        head = ctk.CTkFrame(inner, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(16, 8))

        lbl_ico = ctk.CTkLabel(head, text="[!]", font=ctk.CTkFont(size=24, weight="bold"), text_color="#F38BA8")
        lbl_ico.pack(side="left", padx=(0, 8))

        lbl_tit = ctk.CTkLabel(
            head,
            text="OPERAÇÃO BLOQUEADA — SALDO INSUFICIENTE",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#F38BA8"
        )
        lbl_tit.pack(side="left")

        # Quadro comparativo
        calc_box = ctk.CTkFrame(inner, fg_color="#181825", corner_radius=6)
        calc_box.pack(fill="x", padx=16, pady=12)

        def add_line(t, v, bold=False, color="#CDD6F4"):
            f = ctk.CTkFrame(calc_box, fg_color="transparent")
            f.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(f, text=t, font=ctk.CTkFont(size=13, weight="bold" if bold else "normal"), text_color="#A6ADC8").pack(side="left")
            ctk.CTkLabel(f, text=v, font=ctk.CTkFont(size=13, weight="bold" if bold else "normal"), text_color=color).pack(side="right")

        add_line("Saldo Disponível:", f"R$ {saldo:,.2f}")
        add_line("Valor da Fatura:", f"R$ {valor:,.2f}")
        add_line("Excedente:", f"R$ {excedente:,.2f}", bold=True, color="#F38BA8")

        lbl_desc = ctk.CTkLabel(
            inner,
            text="O valor da nota fiscal excede o saldo contratual disponível.\nOperação cancelada para resguardo do erário público.",
            font=ctk.CTkFont(size=12),
            text_color="#BAC2DE"
        )
        lbl_desc.pack(padx=16, pady=(4, 12))

        btn_retornar = ctk.CTkButton(
            inner,
            text="Compreendido / Retornar [Esc]",
            height=44,
            fg_color="#1F6AA5",
            hover_color="#144A75",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=modal.destroy
        )
        btn_retornar.pack(pady=8)
        btn_retornar.focus_set()

        modal.bind("<Escape>", lambda e: modal.destroy())
        modal.bind("<Return>", lambda e: modal.destroy())
        if self.auto_contrast:
            self._apply_auto_contrast(modal)

    def _mostrar_modal_sucesso(self, contrato: ContratoModel, valor_faturado: Decimal):
        modal = ctk.CTkToplevel(self)
        modal.title("Atesto Efetuado")
        modal.geometry("500x320")
        modal.configure(fg_color="#1E1E2E")
        modal.grab_set()

        inner = ctk.CTkFrame(modal, fg_color="#2A2A3C", corner_radius=10, border_width=2, border_color="#A6E3A1")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        head = ctk.CTkFrame(inner, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(head, text="[OK]", font=ctk.CTkFont(size=24, weight="bold"), text_color="#A6E3A1").pack(side="left", padx=(0, 8))
        ctk.CTkLabel(head, text="ATESTO EFETUADO COM SUCESSO", font=ctk.CTkFont(size=15, weight="bold"), text_color="#A6E3A1").pack(side="left")

        calc_box = ctk.CTkFrame(inner, fg_color="#181825", corner_radius=6)
        calc_box.pack(fill="x", padx=16, pady=12)

        f1 = ctk.CTkFrame(calc_box, fg_color="transparent")
        f1.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(f1, text="Valor Liquidado:", text_color="#A6ADC8").pack(side="left")
        ctk.CTkLabel(f1, text=f"R$ {valor_faturado:,.2f}", font=ctk.CTkFont(weight="bold"), text_color="#CDD6F4").pack(side="right")

        f2 = ctk.CTkFrame(calc_box, fg_color="transparent")
        f2.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(f2, text="Novo Saldo Disponível:", text_color="#A6ADC8").pack(side="left")
        ctk.CTkLabel(f2, text=f"R$ {contrato.saldo_remanescente_atual:,.2f}", font=ctk.CTkFont(weight="bold"), text_color="#A6E3A1").pack(side="right")

        def fechar():
            modal.destroy()
            self.mostrar_dashboard()

        btn_ok = ctk.CTkButton(inner, text="Concluir e Voltar ao Painel [Enter]", height=44, fg_color="#1F6AA5", command=fechar)
        btn_ok.pack(pady=12)
        btn_ok.focus_set()

        modal.bind("<Return>", lambda e: fechar())
        modal.bind("<Escape>", lambda e: fechar())
        if self.auto_contrast:
            self._apply_auto_contrast(modal)

    def _mostrar_alerta_generico(self, titulo: str, msg: str):
        modal = ctk.CTkToplevel(self)
        modal.title(titulo)
        modal.geometry("460x220")
        modal.configure(fg_color="#1E1E2E")
        modal.grab_set()

        inner = ctk.CTkFrame(modal, fg_color="#2A2A3C", corner_radius=8)
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(inner, text=titulo, font=ctk.CTkFont(size=14, weight="bold"), text_color="#F9E2AF").pack(pady=(12, 8))
        ctk.CTkLabel(inner, text=msg, wraplength=400, text_color="#CDD6F4").pack(pady=8)
        ctk.CTkButton(inner, text="OK", width=120, height=36, command=modal.destroy).pack(pady=12)
        if self.auto_contrast:
            self._apply_auto_contrast(modal)
