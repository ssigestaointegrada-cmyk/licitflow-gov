import streamlit as st
import os
import pandas as pd
from docx import Document
import qrcode
from io import BytesIO

# --- CONFIGURAÇÃO DE CAMINHOS (AJUSTADO PARA NUVEM) ---
# Usando caminho relativo para funcionar no Streamlit Cloud
CAMINHO_BASE = "Processos_Licitatorios"
if not os.path.exists(CAMINHO_BASE):
    os.makedirs(CAMINHO_BASE)

# --- MOTOR DE IA PARA MINUTAS ---
def gerador_ia_completo(tipo_doc, nome_obra, descricao):
    estruturas = {
        "ETP": f"1. NECESSIDADE: {descricao}\n2. REQUISITOS: Normas ABNT aplicáveis.\n3. ESTIMATIVA: Baseada em tabelas oficiais.\n4. VIABILIDADE: Técnica e econômica comprovada.",
        "PLANO_TRABALHO": f"1. METAS: Execução total de {nome_obra}.\n2. ETAPAS: Conforme cronograma físico-financeiro.\n3. DESEMBOLSO: Mensal via medição de serviços executados.",
        "MEMORIAL": f"1. ESPECIFICAÇÕES: Materiais de primeira linha.\n2. EXECUÇÃO: Seguindo rigorosamente os projetos técnicos.\n3. LIMPEZA: Entrega da obra limpa e habitável."
    }
    corpo = estruturas.get(tipo_doc, "Diretrizes gerais conforme Lei 14.133/21.")
    return f"[MINUTA TÉCNICA - LICITFLOW GOV]\nDOC: {tipo_doc}\nOBRA: {nome_obra}\n\n{corpo}"

def criar_estrutura_obra(nome_obra):
    nome_limpo = nome_obra.replace(" ", "_").upper()
    caminho_obra = os.path.join(CAMINHO_BASE, nome_limpo)
    subpastas = ["01_Planejamento", "02_Projetos", "03_Orcamento", "04_Fiscalizacao"]
    for sub in subpastas:
        os.makedirs(os.path.join(caminho_obra, sub), exist_ok=True)
    return caminho_obra

def main():
    st.set_page_config(page_title="LicitFlow Gov AI", layout="wide", page_icon="🏛️")
    
    st.sidebar.title("🏛️ LicitFlow Gov AI")
    st.sidebar.info("Gestão de Obras Públicas - Lei 14.133/21")
    
    # SELEÇÃO DE OBRA
    obras = [f for f in os.listdir(CAMINHO_BASE) if os.path.isdir(os.path.join(CAMINHO_BASE, f))]
    sel = st.sidebar.selectbox("Trabalhar na Obra:", ["-- Selecione ou Crie Nova --"] + obras)
    if sel != "-- Selecione ou Crie Nova --":
        st.session_state['pasta_ativa'] = os.path.join(CAMINHO_BASE, sel)

    menu = st.sidebar.radio("Navegação:", ["Nova Demanda (DFD/ETP/TR)", "Projetos e Planos", "Orçamento/Cronograma", "Acompanhamento"])

    # --- MÓDULO 1: PLANEJAMENTO ---
    if menu == "Nova Demanda (DFD/ETP/TR)":
        st.header("📘 Planejamento e Instrução Processual")
        with st.form("form_fase1"):
            nome_obra = st.text_input("Nome da Obra/Serviço (Objeto):")
            problema = st.text_area("Justificativa da Necessidade:")
            
            c1, c2, c3 = st.columns(3)
            if c1.form_submit_button("📄 Gerar DFD"):
                st.session_state['dfd_ia'] = f"DFD - {nome_obra}\nJustificativa: {problema}\nResponsável: Secretaria de Obras."
            if c2.form_submit_button("📑 Gerar ETP"):
                st.session_state['etp_ia'] = gerador_ia_completo("ETP", nome_obra, problema)
            if c3.form_submit_button("📜 Gerar TR"):
                st.session_state['tr_ia'] = f"TERMO DE REFERÊNCIA\nObjeto: {nome_obra}\nPagamento: Conforme Cronograma."
            
            t_dfd = st.text_area("Edição DFD:", value=st.session_state.get('dfd_ia', ""), height=100)
            t_etp = st.text_area("Edição ETP:", value=st.session_state.get('etp_ia', ""), height=100)
            t_tr = st.text_area("Edição TR:", value=st.session_state.get('tr_ia', ""), height=100)
            
            if st.form_submit_button("🔨 Consolidar e Salvar Tudo"):
                p = criar_estrutura_obra(nome_obra)
                for txt, nome_f in [(t_dfd, "01_DFD.docx"), (t_etp, "02_ETP.docx"), (t_tr, "03_TR.docx")]:
                    doc = Document(); doc.add_paragraph(txt)
                    doc.save(os.path.join(p, "01_Planejamento", nome_f))
                st.success(f"Arquivos salvos na pasta {nome_obra}!")
                st.rerun()

    # --- MÓDULO 2: PROJETOS ---
    elif menu == "Projetos e Planos":
        if 'pasta_ativa' not in st.session_state: st.warning("Selecione uma obra.")
        else:
            p_ativa = st.session_state['pasta_ativa']
            st.header(f"📂 Gestão Técnica: {os.path.basename(p_ativa)}")
            tab1, tab2 = st.tabs(["🏗️ Engenharia (PB/PE/Memorial)", "📋 Plano de Trabalho"])
            
            with tab1:
                tipo = st.radio("Documento:", ["Projeto Básico", "Projeto Executivo", "Memorial Descritivo"], horizontal=True)
                if st.button(f"🤖 Gerar {tipo}"):
                    st.session_state['minuta_tec'] = gerador_ia_completo("MEMORIAL" if "Memorial" in tipo else "PROJETO", os.path.basename(p_ativa), "")
                txt_t = st.text_area("Conteúdo:", value=st.session_state.get('minuta_tec', ""), height=250)
                if st.button("💾 Salvar Documento Técnico"):
                    d = Document(); d.add_paragraph(txt_t)
                    d.save(os.path.join(p_ativa, "02_Projetos", f"{tipo.replace(' ','_')}.docx"))
                    st.success("Salvo!")

            with tab2:
                if st.button("🤖 Rascunho Plano de Trabalho"):
                    st.session_state['pt_ia'] = gerador_ia_completo("PLANO_TRABALHO", os.path.basename(p_ativa), "")
                txt_p = st.text_area("Edição Plano:", value=st.session_state.get('pt_ia', ""), height=250)
                if st.button("💾 Salvar PT"):
                    d = Document(); d.add_paragraph(txt_p)
                    d.save(os.path.join(p_ativa, "02_Projetos", "PLANO_DE_TRABALHO.docx"))
                    st.success("Plano Salvo!")

    # --- MÓDULO 3: ORÇAMENTO ---
    elif menu == "Orçamento/Cronograma":
        if 'pasta_ativa' not in st.session_state: st.warning("Selecione uma obra.")
        else:
            p_ativa = st.session_state['pasta_ativa']
            t_plan, t_cron = st.tabs(["📝 Planilha Orçamentária", "📅 Cronograma Detalhado"])
            
            with t_plan:
                if 'df_orc' not in st.session_state:
                    st.session_state['df_orc'] = pd.DataFrame([{"Item": "1.1", "Descrição": "Serviço", "Unidade": "un", "Quantidade": 1.0, "V. Unitário (R$)": 0.0}])
                df_e = st.data_editor(st.session_state['df_orc'], num_rows="dynamic")
                if st.button("💾 Salvar Orçamento"):
                    st.session_state['df_orc'] = df_e
                    df_e.to_excel(os.path.join(p_ativa, "03_Orcamento", "ORCAMENTO.xlsx"), index=False)
                    st.success("Orçamento Salvo!")
            
            with t_cron:
                meses = st.number_input("Meses:", 1, 48, 6)
                df_c = st.session_state.get('df_orc', pd.DataFrame()).copy()
                if not df_c.empty:
                    df_c['Total (R$)'] = df_c['Quantidade'] * df_c['V. Unitário (R$)']
                    for m in range(1, meses + 1): df_c[f"Mês {m} (%)"] = 0.0
                    df_ce = st.data_editor(df_c)
                    if st.button("📊 Gerar Cronograma Excel"):
                        df_ce.to_excel(os.path.join(p_ativa, "03_Orcamento", "CRONOGRAMA.xlsx"), index=False)
                        st.success("Cronograma Gerado!")

    # --- MÓDULO 4: ACOMPANHAMENTO ---
    elif menu == "Acompanhamento":
        if 'pasta_ativa' not in st.session_state: st.warning("Selecione uma obra.")
        else:
            p_ativa = st.session_state['pasta_ativa']
            p_fisc = os.path.join(p_ativa, "04_Fiscalizacao")
            
            # QR CODE NA SIDEBAR
            qr = qrcode.make(f"https://transparencia.gov.br/obras/{os.path.basename(p_ativa)}")
            buf = BytesIO(); qr.save(buf, format="PNG")
            st.sidebar.image(buf.getvalue(), caption="QR Code Transparência")
            
            t_med, t_dia, t_fot = st.tabs(["📏 Medições", "📝 Diário", "📸 Fotos"])
            with t_dia:
                relato = st.text_area("Novo Relato:")
                if st.button("Assinar Diário"):
                    with open(os.path.join(p_fisc, "DIARIO.txt"), "a") as f: f.write(f"\n- {relato}")
                    st.success("Relato Salvo!")
            with t_fot:
                ups = st.file_uploader("Subir Fotos:", accept_multiple_files=True)
                if st.button("💾 Salvar Fotos"):
                    for u in ups:
                        with open(os.path.join(p_fisc, u.name), "wb") as f: f.write(u.getbuffer())
                    st.rerun()

if __name__ == "__main__":
    main()
