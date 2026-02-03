import streamlit as st
import os
import pandas as pd
from docx import Document
import qrcode
from io import BytesIO

# --- RAIZ DO SERVIDOR ---
CAMINHO_BASE = "Processos_Licitatorios"
if not os.path.exists(CAMINHO_BASE):
    os.makedirs(CAMINHO_BASE)

def gerador_ia_completo(tipo_doc, nome_obra, descricao):
    estruturas = {
        "ETP": f"1. NECESSIDADE: {descricao}\n2. REQUISITOS: Normas ABNT.\n3. ESTIMATIVA: Tabelas oficiais.",
        "PLANO_TRABALHO": f"1. METAS: Execução de {nome_obra}.\n2. ETAPAS: Conforme cronograma.",
        "MEMORIAL": f"1. ESPECIFICAÇÕES: Materiais classe A.\n2. EXECUÇÃO: Conforme NBRs."
    }
    return f"[MINUTA LICITFLOW GOV]\nDOC: {tipo_doc}\nOBRA: {nome_obra}\n\n{estruturas.get(tipo_doc, 'Diretrizes gerais.')}"

def criar_estrutura_obra(caminho_pref, nome_obra):
    nome_limpo = nome_obra.replace(" ", "_").upper()
    caminho_obra = os.path.join(caminho_pref, nome_limpo)
    for sub in ["01_Planejamento", "02_Projetos", "03_Orcamento", "04_Fiscalizacao"]:
        os.makedirs(os.path.join(caminho_obra, sub), exist_ok=True)
    return caminho_obra

def main():
    st.set_page_config(page_title="LicitFlow Gov AI", layout="wide", page_icon="🏛️")
    
    # --- SISTEMA DE LOGIN POR CHAVE ---
    if 'autenticado' not in st.session_state:
        st.session_state['autenticado'] = False

    if not st.session_state['autenticado']:
        st.header("🔐 Acesso Restrito - LicitFlow Gov")
        chave = st.text_input("Digite a Chave de Acesso da Prefeitura (ex: ATIBAIA):", type="password")
        if st.button("Entrar"):
            if chave.strip() != "":
                st.session_state['chave_prefeitura'] = chave.upper().strip()
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("Chave inválida.")
        return 

    # --- DEFINIÇÃO DA PASTA DA PREFEITURA LOGADA ---
    CAMINHO_PREF = os.path.join(CAMINHO_BASE, st.session_state['chave_prefeitura'])
    if not os.path.exists(CAMINHO_PREF):
        os.makedirs(CAMINHO_PREF)

    # --- SIDEBAR PERSONALIZADA ---
    with st.sidebar:
        st.subheader("⚙️ Configurações")
        nome_orgao = st.text_input("Nome do Órgão:", f"Prefeitura de {st.session_state['chave_prefeitura']}")
        sub_orgao = st.text_input("Secretaria:", "Secretaria de Infraestrutura")
        logo_upload = st.file_uploader("Trocar Brasão:", type=["png", "jpg"])
        
        st.markdown("---")
        if logo_upload: st.image(logo_upload, width=100)
        else: st.title("🏛️")
        st.title(nome_orgao)
        st.caption(sub_orgao)
        
        if st.button("🚪 Sair do Sistema"):
            st.session_state['autenticado'] = False
            st.rerun()
        st.markdown("---")

    # --- SELEÇÃO DE OBRA DENTRO DA PREFEITURA ---
    obras = [f for f in os.listdir(CAMINHO_PREF) if os.path.isdir(os.path.join(CAMINHO_PREF, f))]
    sel = st.sidebar.selectbox("Trabalhar na Obra:", ["-- Selecione ou Crie Nova --"] + obras)
    if sel != "-- Selecione ou Crie Nova --":
        st.session_state['pasta_ativa'] = os.path.join(CAMINHO_PREF, sel)

    menu = st.sidebar.radio("Navegação:", ["Nova Demanda (DFD/ETP/TR)", "Projetos e Planos", "Orçamento/Cronograma", "Acompanhamento"])

    # --- MÓDULO 1: PLANEJAMENTO ---
    if menu == "Nova Demanda (DFD/ETP/TR)":
        st.header("📘 Planejamento e Instrução Processual")
        with st.form("form_fase1"):
            nome_obra = st.text_input("Nome da Obra/Serviço:")
            problema = st.text_area("Justificativa:")
            if st.form_submit_button("🤖 Gerar Minutas (IA)"):
                st.session_state['dfd_ia'] = f"DFD - {nome_obra}\nNecessidade: {problema}"
                st.session_state['etp_ia'] = gerador_ia_completo("ETP", nome_obra, problema)
                st.session_state['tr_ia'] = f"TR - {nome_obra}\nFiscalização: Conforme Medição."
            
            t_dfd = st.text_area("Edição DFD:", value=st.session_state.get('dfd_ia', ""), height=100)
            t_etp = st.text_area("Edição ETP:", value=st.session_state.get('etp_ia', ""), height=100)
            t_tr = st.text_area("Edição TR:", value=st.session_state.get('tr_ia', ""), height=100)
            
            if st.form_submit_button("🔨 Salvar e Liberar Downloads"):
                p = criar_estrutura_obra(CAMINHO_PREF, nome_obra)
                st.session_state['pasta_ativa'] = p
                for txt, nome_f in [(t_dfd, "01_DFD.docx"), (t_etp, "02_ETP.docx"), (t_tr, "03_TR.docx")]:
                    doc = Document(); doc.add_paragraph(txt)
                    doc.save(os.path.join(p, "01_Planejamento", nome_f))
                st.success("Salvo com sucesso!")
                st.rerun()

        if 'pasta_ativa' in st.session_state:
            p_plan = os.path.join(st.session_state['pasta_ativa'], "01_Planejamento")
            if os.path.exists(os.path.join(p_plan, "01_DFD.docx")):
                c1, c2, c3 = st.columns(3)
                with open(os.path.join(p_plan, "01_DFD.docx"), "rb") as f: c1.download_button("📥 Baixar DFD", f, "01_DFD.docx")
                with open(os.path.join(p_plan, "02_ETP.docx"), "rb") as f: c2.download_button("📥 Baixar ETP", f, "02_ETP.docx")
                with open(os.path.join(p_plan, "03_TR.docx"), "rb") as f: c3.download_button("📥 Baixar TR", f, "03_TR.docx")

    # --- MÓDULO 2: PROJETOS ---
    elif menu == "Projetos e Planos":
        if 'pasta_ativa' not in st.session_state: st.warning("Selecione uma obra.")
        else:
            p_ativa = st.session_state['pasta_ativa']
            st.header(f"📂 Gestão Técnica: {os.path.basename(p_ativa)}")
            tab1, tab2 = st.tabs(["🏗️ Engenharia", "📋 Plano de Trabalho"])
            with tab1:
                tipo = st.radio("Documento:", ["Projeto Básico", "Projeto Executivo", "Memorial Descritivo"], horizontal=True)
                if st.button(f"🤖 Gerar {tipo}"):
                    st.session_state['minuta_tec'] = gerador_ia_completo("MEMORIAL" if "Memorial" in tipo else "PROJETO", os.path.basename(p_ativa), "")
                txt_t = st.text_area("Conteúdo:", value=st.session_state.get('minuta_tec', ""), height=250)
                if st.button("💾 Salvar Documento"):
                    nome_f = f"{tipo.replace(' ','_')}.docx"
                    path_f = os.path.join(p_ativa, "02_Projetos", nome_f)
                    d = Document(); d.add_paragraph(txt_t); d.save(path_f)
                    with open(path_f, "rb") as f: st.download_button(f"📥 Baixar {tipo}", f, nome_f)

            with tab2:
                if st.button("🤖 Rascunho PT"): st.session_state['pt_ia'] = gerador_ia_completo("PLANO_TRABALHO", os.path.basename(p_ativa), "")
                txt_p = st.text_area("Edição PT:", value=st.session_state.get('pt_ia', ""), height=250)
                if st.button("💾 Salvar PT"):
                    path_pt = os.path.join(p_ativa, "02_Projetos", "PLANO_TRABALHO.docx")
                    d = Document(); d.add_paragraph(txt_p); d.save(path_pt)
                    with open(path_pt, "rb") as f: st.download_button("📥 Baixar Plano", f, "PLANO_TRABALHO.docx")

    # --- MÓDULO 3: ORÇAMENTO ---
    elif menu == "Orçamento/Cronograma":
        if 'pasta_ativa' not in st.session_state: st.warning("Selecione uma obra.")
        else:
            p_ativa = st.session_state['pasta_ativa']
            t_plan, t_cron = st.tabs(["📝 Planilha", "📅 Cronograma"])
            with t_plan:
                if 'df_orc' not in st.session_state:
                    st.session_state['df_orc'] = pd.DataFrame([{"Item": "1.1", "Descrição": "Serviço", "Unidade": "un", "Quantidade": 1.0, "V. Unitário (R$)": 0.0}])
                df_e = st.data_editor(st.session_state['df_orc'], num_rows="dynamic")
                if st.button("💾 Salvar Orçamento"):
                    path_o = os.path.join(p_ativa, "03_Orcamento", "ORCAMENTO.xlsx")
                    df_e.to_excel(path_o, index=False)
                    with open(path_o, "rb") as f: st.download_button("📥 Baixar Planilha", f, "ORCAMENTO.xlsx")
            with t_cron:
                meses = st.number_input("Meses:", 1, 48, 6)
                if st.button("📊 Gerar Cronograma"):
                    path_c = os.path.join(p_ativa, "03_Orcamento", "CRONOGRAMA.xlsx")
                    st.session_state['df_orc'].to_excel(path_c, index=False) # Simplificado para o teste
                    with open(path_c, "rb") as f: st.download_button("📥 Baixar Cronograma", f, "CRONOGRAMA.xlsx")

    # --- MÓDULO 4: ACOMPANHAMENTO ---
    elif menu == "Acompanhamento":
        if 'pasta_ativa' not in st.session_state: st.warning("Selecione uma obra.")
        else:
            p_ativa = st.session_state['pasta_ativa']
            p_fisc = os.path.join(p_ativa, "04_Fiscalizacao")
            qr = qrcode.make(f"https://transparencia.gov.br/{st.session_state['chave_prefeitura']}/{os.path.basename(p_ativa)}")
            buf = BytesIO(); qr.save(buf, format="PNG")
            st.sidebar.image(buf.getvalue(), caption="QR Code da Obra")
            t_med, t_dia, t_fot = st.tabs(["📏 Medições", "📝 Diário", "📸 Fotos"])
            with t_dia:
                relato = st.text_area("Novo Relato do Fiscal:")
                if st.button("Assinar"):
                    with open(os.path.join(p_fisc, "DIARIO.txt"), "a") as f: f.write(f"\n- {relato}")
                    st.success("Registrado!")
            with t_fot:
                ups = st.file_uploader("Upload de Fotos:", accept_multiple_files=True)
                if st.button("💾 Salvar no Servidor"):
                    for u in ups:
                        with open(os.path.join(p_fisc, u.name), "wb") as f: f.write(u.getbuffer())
                    st.success("Fotos arquivadas!")

if __name__ == "__main__":
    main()
