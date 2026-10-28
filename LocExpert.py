# -*- coding: utf-8 -*-
import streamlit as st
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import folium_static
import uuid
import requests
import datetime
import base64
import os
import io
import json
import urllib.parse
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from streamlit_js_eval import get_geolocation

# Configuração da página
st.set_page_config(
    page_title="Localizador Expert 🛰️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- BASE DE DADOS EM ARQUIVO JSON PERSISTENTE ---
DB_FILE = os.path.join(os.path.dirname(__file__), "clientes_monitorados.json")

def carregar_base():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return [
        {
            "nome": "Empresa Alfa Logística",
            "documento": "12.345.678/0001-90",
            "cep": "01310-100",
            "tipo": "CLIENTE",
            "cliente_adm": "ADM Master",
            "aprovado": True,
            "ip": "189.40.12.85",
            "mac": "B4:2E:99:A1:4F:22",
            "lat": -23.564886,
            "lon": -46.651918,
            "endereco": "Avenida Paulista, 1000, Bela Vista, São Paulo - SP",
            "status": "ONLINE",
            "foto_b64": "",
            "hora": "18:30:15"
        },
        {
            "nome": "Marcelo Silva (Motorista 01)",
            "documento": "120.729.477-23",
            "cep": "88501-001",
            "tipo": "MONITORADO",
            "cliente_adm": "Empresa Alfa Logística",
            "aprovado": True,
            "ip": "201.88.45.10",
            "mac": "88:6F:D4:FC:9E:5E",
            "lat": -27.81744,
            "lon": -50.33684,
            "endereco": "Rua São Joaquim, Centro, Lages, SC",
            "status": "ONLINE",
            "foto_b64": "",
            "hora": "18:53:42"
        }
    ]

def salvar_usuario(usuario):
    base = carregar_base()
    base = [u for u in base if u["documento"] != usuario["documento"]]
    base.append(usuario)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=4)

def atualizar_usuario_dados(doc_antigo, usuario_atualizado):
    base = carregar_base()
    for i, u in enumerate(base):
        if u["documento"] == doc_antigo:
            base[i] = usuario_atualizado
            break
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=4)

def excluir_usuario(documento):
    base = carregar_base()
    base = [u for u in base if u["documento"] != documento]
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=4)

def atualizar_status_aprovacao(doc, status_aprovado):
    base = carregar_base()
    for u in base:
        if u["documento"] == doc:
            u["aprovado"] = status_aprovado
            u["status"] = "ONLINE" if status_aprovado else "REJEITADO"
            break
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=4)

# --- IMAGEM DE FUNDO EM BASE64 ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

caminho_fundo = os.path.join(os.path.dirname(__file__), "FundoTela.jpg")
b64_fundo = get_base64_image(caminho_fundo)

css_bg = f"""
    .stApp {{
        background: linear-gradient(rgba(5, 8, 17, 0.72), rgba(5, 8, 17, 0.88)),
                    url("data:image/jpeg;base64,{b64_fundo}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Share Tech Mono', monospace;
        color: #00ffcc;
    }}
""" if b64_fundo else """
    .stApp {
        background-color: #050811;
        font-family: 'Share Tech Mono', monospace;
        color: #00ffcc;
    }
"""

# --- ESTILIZAÇÃO VISUAL HUD COMPLETA ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@600;700&display=swap');

    html {{
        scroll-behavior: smooth;
    }}

    header[data-testid="stHeader"] {{
        background: transparent !important;
        background-color: transparent !important;
    }}
    div[data-testid="stToolbar"] {{
        visibility: hidden !important;
        display: none !important;
    }}
    div[data-testid="stDecoration"] {{
        display: none !important;
    }}
    .block-container {{
        padding-top: 1.5rem !important;
    }}

    {css_bg}

    .title-hud-box {{
        position: relative;
        background: rgba(4, 25, 38, 0.85);
        border: 1.5px solid #00ff88;
        border-radius: 12px;
        padding: 14px 24px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.25), inset 0 0 12px rgba(0, 255, 136, 0.08);
        display: flex;
        align-items: center;
    }}

    .title-corner-tl {{
        position: absolute;
        top: -4px; left: -4px;
        width: 18px; height: 18px;
        border-top: 3.5px solid #00ff88;
        border-left: 3.5px solid #00ff88;
    }}
    .title-corner-br {{
        position: absolute;
        bottom: -4px; right: -4px;
        width: 18px; height: 18px;
        border-bottom: 3.5px solid #ff9900;
        border-right: 3.5px solid #ff9900;
    }}

    .title-text {{
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.9rem;
        font-weight: 700;
        color: #00ff88;
        text-shadow: 0 0 12px rgba(0, 255, 136, 0.6);
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 0;
    }}

    .continuous-radar-loader {{
        position: relative;
        width: 100%;
        height: 38px;
        background: rgba(4, 25, 38, 0.85);
        border: 1.5px solid #00ff88;
        border-radius: 20px;
        overflow: hidden;
        margin-bottom: 16px;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.25);
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .continuous-radar-loader::before {{
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(
            90deg, 
            transparent 0%, 
            rgba(0, 255, 204, 0.25) 35%, 
            rgba(0, 255, 136, 0.75) 50%, 
            rgba(255, 170, 0, 0.85) 65%, 
            transparent 100%
        );
        box-shadow: 0 0 25px rgba(0, 255, 136, 0.8);
        animation: radar-sweep 2.2s infinite ease-in-out;
    }}

    @keyframes radar-sweep {{
        0% {{ left: -100%; }}
        100% {{ left: 100%; }}
    }}

    .radar-loader-text {{
        position: relative;
        z-index: 2;
        font-family: 'Rajdhani', sans-serif;
        font-weight: 700;
        font-size: 1.15rem;
        letter-spacing: 4px;
        color: #00ff88;
        text-shadow: 0 0 12px rgba(0, 255, 136, 0.9);
        display: flex;
        align-items: center;
        gap: 10px;
    }}

    label[data-testid="stWidgetLabel"] p {{
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 0.88rem !important;
        color: #00ffcc !important;
        margin-bottom: 4px !important;
    }}

    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
    div[data-baseweb="select"] > div {{
        background-color: rgba(4, 25, 38, 0.85) !important;
        border: 1.5px solid #00ff88 !important;
        border-radius: 18px !important;
        backdrop-filter: blur(10px) !important;
        box-shadow: 0 0 12px rgba(0, 255, 136, 0.25) !important;
    }}

    div[data-testid="stTextInput"] input {{
        background: transparent !important;
        color: #00ffcc !important;
        font-family: 'Share Tech Mono', monospace !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        padding: 8px 18px !important;
    }}

    /* Estilo de tag de código IP escura e responsiva */
    code {{
        background: rgba(4, 25, 38, 0.9) !important;
        color: #00ffcc !important;
        border: 1px solid rgba(0, 255, 136, 0.3) !important;
        padding: 2px 6px !important;
        border-radius: 6px !important;
        word-break: break-all !important;
        font-size: 0.75rem !important;
    }}

    .stButton > button, .stLinkButton > a, .stDownloadButton > button, .hud-anchor-btn {{
        background: rgba(4, 30, 45, 0.75) !important;
        color: #00ff88 !important;
        font-family: 'Rajdhani', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border: 1.5px solid #00ff88 !important;
        border-radius: 24px !important;
        padding: 8px 24px !important;
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.25) !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        box-sizing: border-box !important;
        cursor: pointer !important;
        transition: all 0.25s ease-in-out !important;
    }}

    .stButton > button:hover, .stLinkButton > a:hover, .stDownloadButton > button:hover, .hud-anchor-btn:hover {{
        background: rgba(0, 255, 136, 0.25) !important;
        color: #ffffff !important;
        border-color: #00ffcc !important;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.6) !important;
    }}

    .status-badge {{
        background: rgba(0, 255, 136, 0.2);
        color: #00ff88;
        border: 1px solid #00ff88;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-weight: bold;
    }}

    .status-pending {{
        background: rgba(255, 170, 0, 0.2);
        color: #ffaa00;
        border: 1px solid #ffaa00;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 0.75rem;
        font-weight: bold;
    }}

    .profile-card {{
        background: rgba(6, 26, 42, 0.95);
        border: 2px solid #00ffcc;
        border-radius: 16px;
        padding: 20px;
        margin-top: 15px;
        margin-bottom: 20px;
        box-shadow: 0 0 30px rgba(0, 255, 204, 0.35);
        display: flex;
        gap: 25px;
        align-items: center;
    }}

    .profile-pic {{
        width: 110px;
        height: 110px;
        border-radius: 50%;
        border: 2px solid #00ff88;
        box-shadow: 0 0 15px #00ff88;
        object-fit: cover;
        background: #0f172a;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
    }}

    iframe {{
        border: 1.5px solid #00ff88 !important;
        border-radius: 12px !important;
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.25) !important;
        filter: invert(100%) hue-rotate(180deg) brightness(85%) contrast(120%) !important;
    }}

    .glass-panel {{
        background: rgba(4, 25, 38, 0.75);
        border: 1.5px solid #00ff88;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 0 15px rgba(0, 255, 136, 0.2);
    }}

    .panel-header {{
        font-family: 'Rajdhani', sans-serif;
        font-size: 1.15rem;
        font-weight: 700;
        color: #00ff88;
        border-bottom: 1px solid rgba(0, 255, 136, 0.3);
        padding-bottom: 4px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}

    .live-pulse {{
        display: inline-block;
        width: 10px; height: 10px;
        background: #00ff88;
        border-radius: 50%;
        margin-right: 8px;
        box-shadow: 0 0 10px #00ff88;
        animation: pulse 1.5s infinite;
    }}
    @keyframes pulse {{
        0% {{ transform: scale(0.9); opacity: 0.6; }}
        50% {{ transform: scale(1.3); opacity: 1; }}
        100% {{ transform: scale(0.9); opacity: 0.6; }}
    }}
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE HARDWARE E TELEMETRIA ---
def obter_mac_address():
    mac_num = uuid.getnode()
    mac_hex = f"{mac_num:012x}"
    return ":".join(mac_hex[i:i+2] for i in range(0, 12, 2)).upper()

def obter_ip_publico():
    try:
        r = requests.get("https://api64.ipify.org?format=json", timeout=3)
        return r.json().get("ip", "192.168.1.10")
    except Exception:
        return "192.168.1.10"

# --- FUNÇÕES DE EXPORTAÇÃO PERSONALIZADA ---
def exportar_clientes_txt(clientes, periodo, intervalo, cli_especifico=None):
    nome_alvo = cli_especifico['nome'] if cli_especifico else "TODOS OS REGISTROS"
    linhas = [
        "===========================================================",
        "   LOCALIZADOR EXPERT // RELATORIO DE MONITORAMENTO       ",
        "===========================================================",
        f"Data Emissao: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"Perfil Extraido: {nome_alvo}",
        f"Filtro Aplicado: Periodo: {periodo} | Amostragem: {intervalo}",
        f"Total de Registros: {len(clientes)}",
        "-----------------------------------------------------------",
        "NOME | DOCUMENTO | TIPO | VINCULO ADM | IP | MAC | LAT | LON | ENDERECO | STATUS"
    ]
    for c in clientes:
        linhas.append(f"{c['nome']} | {c.get('documento', 'N/A')} | {c.get('tipo', 'N/A')} | {c.get('cliente_adm', 'N/A')} | {c['ip']} | {c['mac']} | {c['lat']:.5f} | {c['lon']:.5f} | {c['endereco']} | {c['status']}")
    return "\n".join(linhas)

def exportar_clientes_excel(clientes, periodo, intervalo, cli_especifico=None):
    df = pd.DataFrame(clientes)
    if "foto_b64" in df.columns:
        df = df.drop(columns=["foto_b64"])
    df["Perfil_Extraido"] = cli_especifico['nome'] if cli_especifico else "Todos"
    df["Filtro_Periodo"] = periodo
    df["Intervalo_Amostragem"] = intervalo
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Monitoramento")
    return output.getvalue()

def exportar_clientes_pdf(clientes, periodo, intervalo, cli_especifico=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8
    )
    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=4
    )

    nome_alvo = cli_especifico['nome'] if cli_especifico else "Relatório Consolidado"
    elements = [
        Paragraph("LOCALIZADOR EXPERT // RELATORIO OPERACIONAL", title_style),
        Paragraph(f"<b>Data de Emissão:</b> {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", meta_style),
        Paragraph(f"<b>Perfil:</b> <font color='#0066cc'><b>{nome_alvo}</b></font>", meta_style),
        Paragraph(f"<b>Filtro:</b> Período: <b>{periodo}</b> | Intervalo: <b>{intervalo}</b>", meta_style),
        Spacer(1, 10)
    ]
    
    table_data = [["NOME", "TIPO", "VÍNCULO ADM", "IP", "MAC", "STATUS"]]
    for c in clientes:
        table_data.append([
            c["nome"][:20],
            c.get("tipo", "N/A"),
            c.get("cliente_adm", "N/A")[:18],
            c["ip"],
            c["mac"],
            c["status"]
        ])
        
    t = Table(table_data, colWidths=[110, 80, 100, 100, 100, 60])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('FONTSIZE', (0,1), (-1,-1), 8),
    ]))
    
    elements.append(t)
    doc.build(elements)
    return buffer.getvalue()

# --- ESTADOS DA SESSÃO ---
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = "adm_master" # Default para acesso direto

if "cliente_selecionado" not in st.session_state:
    st.session_state["cliente_selecionado"] = None

if "modo_edicao" not in st.session_state:
    st.session_state["modo_edicao"] = False

# Roteamento por URL
query_params = st.query_params
eh_cadastro = query_params.get("modo") == "cadastro"

# =========================================================================
# MODO 1: PORTAL DE CADASTRO COM ABA SISTEMA (CLIENTE OU MONITORADO) + LGPD
# =========================================================================
if eh_cadastro:
    st.markdown("""
    <div class="title-hud-box">
        <div class="title-corner-tl"></div>
        <div class="title-corner-br"></div>
        <div class="title-text">
            <span>🛰️</span>
            <span>Localizador Expert // Cadastro & Consentimento LGPD</span>
            <span style="font-size:0.8rem; color:#ffaa00; margin-left:auto; font-family:'Share Tech Mono';">● TERMO LGPD</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    pos_gps = get_geolocation(component_key="gps_cadastro_form")
    lat_cad = -27.81744
    lon_cad = -50.33684
    if pos_gps and "coords" in pos_gps:
        lat_cad = pos_gps["coords"]["latitude"]
        lon_cad = pos_gps["coords"]["longitude"]
        st.success(f"📍 GPS Detectado: {lat_cad:.6f}, {lon_cad:.6f}")
    else:
        st.info("ℹ️ Autorize a localização no aviso do seu navegador para vincular seu GPS.")

    ip_cad = obter_ip_publico()
    mac_cad = obter_mac_address()
    base_atual = carregar_base()
    lista_clientes_adm = [u["nome"] for u in base_atual if u.get("tipo") == "CLIENTE" and u.get("aprovado")]

    with st.container():
        st.markdown("""
        <div class="glass-panel">
            <div class="panel-header">
                <span>Cadastro e Liberação de Rastreamento (LGPD)</span>
                <span style="font-size:0.85rem; color:#ffaa00;">LEI Nº 13.709/2018</span>
            </div>
            <p style="color:#cbd5e1; font-size:0.9rem;">
                Ao preencher os dados abaixo e clicar em confirmar, você autoriza expressamente o <b>Localizador Expert</b> a receber suas coordenadas GPS, endereço IP e identificadores técnicos de rede para fins de monitoramento e segurança. Seu cadastro passará por aprovação do <b>ADM Master</b>.
            </p>
        </div>
        """, unsafe_allow_html=True)

        aba_dados, aba_sistema = st.tabs(["📝 Dados Pessoais / Empresa", "⚙️ Aba Sistema & Vínculo"])

        with aba_dados:
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                nome_cad = st.text_input("Nome Completo / Razão Social:", placeholder="Ex: Marcelo Silva")
                doc_cad = st.text_input("CPF ou CNPJ:", placeholder="000.000.000-00")
            with col_c2:
                cep_cad = st.text_input("CEP:", placeholder="00000-000")
                foto_upload = st.file_uploader("Foto de Perfil / Documento (Opcional):", type=["jpg", "png", "jpeg"])

        with aba_sistema:
            tipo_usuario = st.radio(
                "Escolha o Tipo de Acesso no Sistema:",
                ["Monitorado (Subordinado)", "Cliente (Empresa / Gestor)"],
                help="Clientes gerenciam seus próprios monitorados. Monitorados são rastreados pela sua central e pelo ADM Master."
            )
            tipo_final = "MONITORADO" if "Monitorado" in tipo_usuario else "CLIENTE"

            if tipo_final == "MONITORADO":
                opcoes_vinculo = lista_clientes_adm if lista_clientes_adm else ["ADM Master (Direto)"]
                cliente_adm_escolhido = st.selectbox(
                    "Selecione seu Cliente ADM Gestor:",
                    opcoes_vinculo,
                    help="Indique a qual Cliente/Empresa você pertence."
                )
            else:
                cliente_adm_escolhido = "ADM Master"
                st.info("ℹ️ Clientes respondem e reportam diretamente à governança do **ADM Master**.")

        if st.button("✅ Confirmar Dados e Solicitar Aprovação", use_container_width=True):
            if nome_cad and doc_cad:
                foto_b64 = ""
                if foto_upload:
                    foto_b64 = base64.b64encode(foto_upload.read()).decode()

                end_formatado = f"CEP {cep_cad}" if cep_cad else "Localização via GPS"
                try:
                    geolocator = Nominatim(user_agent="locexpert_cad_save")
                    rev = geolocator.reverse(f"{lat_cad}, {lon_cad}")
                    if rev:
                        end_formatado = rev.address
                except Exception:
                    pass

                novo_cad = {
                    "nome": nome_cad,
                    "documento": doc_cad,
                    "cep": cep_cad,
                    "tipo": tipo_final,
                    "cliente_adm": cliente_adm_escolhido,
                    "aprovado": False,
                    "ip": ip_cad,
                    "mac": mac_cad,
                    "lat": lat_cad,
                    "lon": lon_cad,
                    "endereco": end_formatado,
                    "status": "AGUARDANDO APROVAÇÃO",
                    "foto_b64": foto_b64,
                    "hora": datetime.datetime.now().strftime("%H:%M:%S")
                }
                salvar_usuario(novo_cad)
                st.balloons()
                st.success("🎉 Cadastro enviado com sucesso! Seus dados foram transmitidos ao ADM Master para liberação.")
            else:
                st.error("Por favor, preencha Nome e CPF/CNPJ.")

# =========================================================================
# MODO 2: TELA DE LOGIN (QUANDO NÃO AUTENTICADO)
# =========================================================================
elif not st.session_state["usuario_logado"]:
    st.markdown("""
    <div class="title-hud-box">
        <div class="title-corner-tl"></div>
        <div class="title-corner-br"></div>
        <div class="title-text">
            <span>🛰️</span>
            <span>Localizador Expert // Autenticação de Segurança</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("""
        <div class="glass-panel" style="text-align:center;">
            <div class="panel-header" style="justify-content:center;">
                <span>🔐 ACESSO RESTRITO À CENTRAL TÁTICA</span>
            </div>
            <p style="color:#cbd5e1; font-size:0.9rem;">
                Informe suas credenciais de <b>ADM Master</b> ou selecione seu perfil de <b>Cliente Gestor</b> para acessar o painel de monitoramento.
            </p>
        </div>
        """, unsafe_allow_html=True)

        tipo_login = st.radio("Entrar como:", ["ADM Master (Controle Total)", "Cliente Gestor"], horizontal=True)

        if "ADM Master" in tipo_login:
            user_login = st.text_input("Usuário Master:", value="admin")
            pass_login = st.text_input("Senha Master:", type="password", value="admin123")
            if st.button("🚀 Acessar Central ADM Master", use_container_width=True):
                if user_login == "admin" and pass_login == "admin123":
                    st.session_state["usuario_logado"] = "adm_master"
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        else:
            base_clientes = [u for u in carregar_base() if u.get("tipo") == "CLIENTE" and u.get("aprovado")]
            if base_clientes:
                dict_clientes = {f"{c['nome']} (Doc: {c['documento']})": c for c in base_clientes}
                cliente_escolhido = st.selectbox("Selecione sua Conta de Cliente:", list(dict_clientes.keys()))
                doc_confirm = st.text_input("Confirme seu CPF/CNPJ:")
                if st.button("🚀 Entrar no Painel do Cliente", use_container_width=True):
                    c_obj = dict_clientes[cliente_escolhido]
                    if doc_confirm.strip() == c_obj["documento"].strip():
                        st.session_state["usuario_logado"] = c_obj
                        st.rerun()
                    else:
                        st.error("Documento não confere.")
            else:
                st.warning("Nenhum cliente aprovado disponível no momento.")

# =========================================================================
# MODO 3: PAINEL DE MONITORAMENTO (ADM MASTER OU CLIENTE GESTOR)
# =========================================================================
else:
    eh_master = st.session_state["usuario_logado"] == "adm_master"
    base_geral = carregar_base()

    link_cadastro = "http://localhost:8501/?modo=cadastro"
    texto_disparo = "monitorados" if eh_master else "meus monitorados"
    msg_zap = f"Ola! Por favor, acesse o link para realizar seu cadastro e liberar seu acesso de monitoramento via LGPD: {link_cadastro}"
    link_zap_disparo = f"https://api.whatsapp.com/send?text={urllib.parse.quote(msg_zap)}"

    # Título HUD
    st.markdown(f"""
    <div class="title-hud-box">
        <div class="title-corner-tl"></div>
        <div class="title-corner-br"></div>
        <div class="title-text">
            <span>🛰️</span>
            <span>Localizador Expert</span>
            <span style="font-size:0.8rem; color:#ffaa00; margin-left:auto; font-family:'Share Tech Mono';">
                {'[MODO: ADM MASTER]' if eh_master else f'[CLIENTE: {st.session_state["usuario_logado"]["nome"]}]'}
            </span>
            <span style="font-size:0.95rem; font-weight:900; color:#00ff88; margin-left:14px; font-family:'Share Tech Mono'; letter-spacing:2px; text-shadow:0 0 10px #00ff88;">● ON</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # BARRA CARREGANDO CONTINUAMENTE - DASHBOARD
    st.markdown("""
    <div class="continuous-radar-loader">
        <div class="radar-loader-text">
            <span>DASHBOARD</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # BOTÕES PRINCIPAIS DE COMANDO
    col_act1, col_act2, col_act3, col_act4 = st.columns([2, 3, 2.5, 1.5])
    with col_act1:
        st.markdown("""
        <a href="#painel-clientes" class="hud-anchor-btn">
            👥 Monitoramento
        </a>
        """, unsafe_allow_html=True)
    with col_act2:
        st.link_button(f"📲 Disparar Link para {texto_disparo} (WhatsApp)", link_zap_disparo, use_container_width=True)
    with col_act3:
        st.link_button("🌐 Abrir Formulário Cadastro (LGPD)", link_cadastro, use_container_width=True)
    with col_act4:
        if st.button("🚪 Sair (Logout)", use_container_width=True):
            st.session_state["usuario_logado"] = None
            st.session_state["cliente_selecionado"] = None
            st.session_state["modo_edicao"] = False
            st.rerun()

    # Separação de visibilidade:
    # ADM Master vê todos os cadastrados
    if eh_master:
        lista_visivel = base_geral
        pendentes_aprovacao = [u for u in base_geral if not u.get("aprovado")]
    else:
        cli_nome = st.session_state["usuario_logado"]["nome"]
        lista_visivel = [u for u in base_geral if u.get("aprovado") and (u.get("cliente_adm") == cli_nome or u.get("nome") == cli_nome)]
        pendentes_aprovacao = []

    # =========================================================================
    # ÁREA EXCLUSIVA ADM MASTER: APROVAÇÃO RÁPIDA
    # =========================================================================
    if eh_master and pendentes_aprovacao:
        st.markdown("""
        <div class="glass-panel" style="border-color:#ffaa00; margin-top:10px;">
            <div class="panel-header" style="color:#ffaa00; border-bottom:1px solid rgba(255,170,0,0.3);">
                <span>🔔 SOLICITAÇÕES PENDENTES DE APROVAÇÃO (LGPD RECEBIDA)</span>
                <span class="status-pending">PENDENTES: """ + str(len(pendentes_aprovacao)) + """</span>
            </div>
            <p style="color:#cbd5e1; font-size:0.85rem;">Como ADM Master, aprove ou reprove novos Clientes e Monitorados para liberar o acesso ao sistema:</p>
        </div>
        """, unsafe_allow_html=True)

        for pend in pendentes_aprovacao:
            col_ap1, col_ap2, col_ap3, col_ap4 = st.columns([3, 2, 2, 2])
            with col_ap1:
                st.markdown(f"<b style='color:#38bdf8;'>{pend['nome']}</b> ({pend.get('tipo', 'N/A')})<br><span style='color:#94a3b8; font-size:0.8rem;'>Vínculo ADM: {pend.get('cliente_adm', 'N/A')}</span>", unsafe_allow_html=True)
            with col_ap2:
                st.markdown(f"<span style='color:#cbd5e1; font-size:0.85rem;'>Doc: {pend['documento']} | CEP: {pend.get('cep', 'N/A')}</span>", unsafe_allow_html=True)
            with col_ap3:
                if st.button(f"✅ Aprovar & Liberar", key=f"apr_{pend['documento']}", use_container_width=True):
                    atualizar_status_aprovacao(pend['documento'], True)
                    st.rerun()
            with col_ap4:
                if st.button(f"❌ Rejeitar", key=f"rej_{pend['documento']}", use_container_width=True):
                    excluir_usuario(pend['documento'])
                    st.rerun()

    # Dispositivo focado
    cli_foco = None
    if st.session_state["cliente_selecionado"]:
        for c in lista_visivel:
            if c["documento"] == st.session_state["cliente_selecionado"]:
                cli_foco = c
                break

    centro_mapa = [cli_foco["lat"], cli_foco["lon"]] if cli_foco else [-23.564886, -46.651918]

    # Layout: Mapa (Esquerda) + Painéis (Direita)
    col_mapa, col_info = st.columns([7, 3], gap="medium")

    with col_mapa:
        mapa = folium.Map(location=centro_mapa, zoom_start=14 if cli_foco else 6, tiles="OpenStreetMap")

        for cli in lista_visivel:
            c_lat = cli.get("lat", -23.56488)
            c_lon = cli.get("lon", -46.65191)
            eh_tipo_cliente = cli.get("tipo") == "CLIENTE"
            
            folium.Circle(
                location=[c_lat, c_lon],
                radius=250 if cli == cli_foco else (180 if eh_tipo_cliente else 120),
                color="#ffaa00" if cli == cli_foco else ("#38bdf8" if eh_tipo_cliente else "#00ff88"),
                weight=2 if cli == cli_foco else 1.5,
                fill=False,
                opacity=0.8
            ).add_to(mapa)

            popup_texto = f"<b>{cli['nome']}</b><br>Tipo: {cli.get('tipo', 'N/A')}<br>Vínculo: {cli.get('cliente_adm', 'N/A')}"
            folium.Marker(
                [c_lat, c_lon],
                popup=popup_texto,
                tooltip=f"{cli['nome']} ({cli.get('tipo')})",
                icon=folium.Icon(color="red" if cli == cli_foco else ("blue" if eh_tipo_cliente else "green"), icon="user", prefix="fa")
            ).add_to(mapa)

        folium_static(mapa, width=780, height=450)

    with col_info:
        st.markdown(f"""
        <div class="glass-panel">
            <div class="panel-header">
                <span><span class="live-pulse"></span>Central em Tempo Real</span>
                <span style="font-size: 1.1rem;">🛰️</span>
            </div>
            <div style="font-size:0.88rem; line-height:1.6; color:#bbf7d0;">
                <div><span style="color:#00ffcc; font-weight:bold;">PERFIL ATUAL:</span> {'ADM MASTER' if eh_master else 'CLIENTE GESTOR'}</div>
                <div><span style="color:#00ffcc; font-weight:bold;">DISPOSITIVOS ATIVOS:</span> {len(lista_visivel)} cadastrados</div>
                <div><span style="color:#00ffcc; font-weight:bold;">REDE SERVIDOR:</span> {obter_ip_publico()}</div>
                <div><span style="color:#00ffcc; font-weight:bold;">HARDWARE SERVER:</span> {obter_mac_address()}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # PAINEL DE EXTRAÇÃO DE BASE PERSONALIZADA
        alvo_texto = f"👤 {cli_foco['nome']}" if cli_foco else "🌐 Todos"
        st.markdown(f"""
        <div class="glass-panel">
            <div class="panel-header" style="color:#ffaa00; border-bottom:1px solid rgba(255,170,0,0.3);">
                <span>Extração de Base</span>
                <span style="font-size:0.8rem; color:#00ffcc;">{alvo_texto}</span>
            </div>
        """, unsafe_allow_html=True)

        if cli_foco:
            st.info(f"🎯 Extraindo: **{cli_foco['nome']}** ({cli_foco.get('tipo')})")
        else:
            st.caption("ℹ️ Extraindo a base geral conectada.")

        filtro_dia = st.selectbox(
            "📅 Período de Rastreamento:",
            ["Hoje (Dia Atual)", "Últimas 24 Horas", "Últimos 7 Dias", "Mês Atual", "Histórico Completo"]
        )

        filtro_intervalo = st.selectbox(
            "⏱️ Intervalo de Amostragem:",
            ["A cada 15 minutos", "A cada 30 minutos", "A cada 1 hora", "Tempo Real (Sem Intervalo)"]
        )

        filtro_formato = st.selectbox(
            "📄 Formato da Exportação:",
            ["Documento PDF (.pdf)", "Excel (.xlsx / .xlsm)", "Texto Log (.txt)"]
        )

        st.write("")

        dados_para_extrair = [cli_foco] if cli_foco else lista_visivel
        prefixo_nome = cli_foco['nome'].lower().replace(' ', '_') if cli_foco else "base_monitoramento"
        nome_base_arquivo = f"{prefixo_nome}_{datetime.datetime.now().strftime('%d_%m_%Y')}"

        if "Excel" in filtro_formato:
            dados_excel = exportar_clientes_excel(dados_para_extrair, filtro_dia, filtro_intervalo, cli_especifico=cli_foco)
            st.download_button(
                label=f"📥 Extrair ({'Perfil: ' + cli_foco['nome'][:18] if cli_foco else 'Base Geral'})",
                data=dados_excel,
                file_name=f"{nome_base_arquivo}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        elif "PDF" in filtro_formato:
            dados_pdf = exportar_clientes_pdf(dados_para_extrair, filtro_dia, filtro_intervalo, cli_especifico=cli_foco)
            st.download_button(
                label=f"📥 Extrair ({'Perfil: ' + cli_foco['nome'][:18] if cli_foco else 'Base Geral'})",
                data=dados_pdf,
                file_name=f"{nome_base_arquivo}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            dados_txt = exportar_clientes_txt(dados_para_extrair, filtro_dia, filtro_intervalo, cli_especifico=cli_foco)
            st.download_button(
                label=f"📥 Extrair ({'Perfil: ' + cli_foco['nome'][:18] if cli_foco else 'Base Geral'})",
                data=dados_txt,
                file_name=f"{nome_base_arquivo}.txt",
                mime="text/plain",
                use_container_width=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================================
    # PERFIL DETALHADO DO MONITORADO OU CLIENTE (COM MODO DE EDIÇÃO DO ADM MASTER)
    # =========================================================================
    if cli_foco:
        # SE O ADM MASTER ATIVOU O MODO EDIÇÃO
        if eh_master and st.session_state["modo_edicao"]:
            st.markdown(f"""
            <div class="glass-panel" style="border-color:#38bdf8; margin-top:15px; margin-bottom:15px;">
                <div class="panel-header" style="color:#38bdf8; border-bottom:1px solid rgba(56,189,248,0.3);">
                    <span>✏️ EDITAR PERFIL: {cli_foco['nome']} (ADM MASTER)</span>
                    <span style="font-size:0.8rem; color:#ffaa00;">ACESSO DE CONTROLE TOTAL</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_ed1, col_ed2, col_ed3 = st.columns(3)
            with col_ed1:
                edit_nome = st.text_input("Nome Completo:", value=cli_foco["nome"])
                edit_doc = st.text_input("CPF / CNPJ:", value=cli_foco["documento"])
                edit_cep = st.text_input("CEP:", value=cli_foco.get("cep", ""))
            with col_ed2:
                # Escolha do Tipo
                tipos = ["MONITORADO", "CLIENTE"]
                idx_tipo = tipos.index(cli_foco.get("tipo", "MONITORADO")) if cli_foco.get("tipo") in tipos else 0
                edit_tipo = st.selectbox("Tipo de Conta:", tipos, index=idx_tipo)

                # Escolha do Vínculo
                clientes_para_vinculo = ["ADM Master"] + [c["nome"] for c in base_geral if c.get("tipo") == "CLIENTE" and c["documento"] != cli_foco["documento"]]
                vinculo_atual = cli_foco.get("cliente_adm", "ADM Master")
                idx_vinc = clientes_para_vinculo.index(vinculo_atual) if vinculo_atual in clientes_para_vinculo else 0
                edit_vinculo = st.selectbox("Pertence a (Cliente ADM Gestor):", clientes_para_vinculo, index=idx_vinc)

                status_opcoes = ["ONLINE", "OFFLINE", "AGUARDANDO APROVAÇÃO", "BLOQUEADO"]
                idx_status = status_opcoes.index(cli_foco.get("status", "ONLINE")) if cli_foco.get("status") in status_opcoes else 0
                edit_status = st.selectbox("Status Operacional:", status_opcoes, index=idx_status)

            with col_ed3:
                edit_lat = st.number_input("Latitude:", value=float(cli_foco["lat"]), format="%.6f")
                edit_lon = st.number_input("Longitude:", value=float(cli_foco["lon"]), format="%.6f")
                edit_end = st.text_input("Endereço:", value=cli_foco.get("endereco", ""))

            col_salvar, col_cancelar, col_excluir = st.columns([2, 2, 2])
            with col_salvar:
                if st.button("💾 Salvar Alterações", use_container_width=True):
                    usuario_editado = dict(cli_foco)
                    usuario_editado.update({
                        "nome": edit_nome,
                        "documento": edit_doc,
                        "cep": edit_cep,
                        "tipo": edit_tipo,
                        "cliente_adm": edit_vinculo,
                        "status": edit_status,
                        "aprovado": edit_status != "AGUARDANDO APROVAÇÃO",
                        "lat": edit_lat,
                        "lon": edit_lon,
                        "endereco": edit_end
                    })
                    atualizar_usuario_dados(cli_foco["documento"], usuario_editado)
                    st.session_state["cliente_selecionado"] = edit_doc
                    st.session_state["modo_edicao"] = False
                    st.success("✅ Perfil atualizado com sucesso pelo ADM Master!")
                    st.rerun()
            with col_cancelar:
                if st.button("↩️ Cancelar Edição", use_container_width=True):
                    st.session_state["modo_edicao"] = False
                    st.rerun()
            with col_excluir:
                if st.button("🗑️ Excluir Dispositivo", use_container_width=True):
                    excluir_usuario(cli_foco["documento"])
                    st.session_state["cliente_selecionado"] = None
                    st.session_state["modo_edicao"] = False
                    st.rerun()

        # VISUALIZAÇÃO NORMAL DO PERFIL COM BOTÃO DE EDITAR
        else:
            foto_html = f'<img src="data:image/jpeg;base64,{cli_foco["foto_b64"]}" class="profile-pic">' if cli_foco.get("foto_b64") else '<div class="profile-pic">👤</div>'
            link_maps_cliente = f"https://www.google.com/maps/?q={cli_foco['lat']},{cli_foco['lon']}"
            link_street_cliente = f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={cli_foco['lat']},{cli_foco['lon']}"

            badge_tipo_cor = "#38bdf8" if cli_foco.get("tipo") == "CLIENTE" else "#00ff88"
            st.markdown(f"""
            <div class="profile-card">
                {foto_html}
                <div style="flex-grow:1;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-family:'Rajdhani', sans-serif; font-size:1.8rem; font-weight:700; color:#38bdf8;">
                                {cli_foco['nome']}
                            </span>
                            <span style="background:rgba(56,189,248,0.2); color:{badge_tipo_cor}; border:1px solid {badge_tipo_cor}; border-radius:8px; padding:2px 8px; font-size:0.75rem; margin-left:10px;">
                                {cli_foco.get('tipo', 'MONITORADO')}
                            </span>
                        </div>
                        <span class="status-badge" style="font-size:0.9rem;">● {cli_foco['status']}</span>
                    </div>
                    <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; margin-top:10px; font-size:0.9rem; color:#cbd5e1;">
                        <div><b style="color:#00ff88;">CPF/CNPJ:</b> {cli_foco['documento']}</div>
                        <div><b style="color:#00ff88;">Pertence a (Vínculo):</b> <span style="color:#ffaa00; font-weight:bold;">{cli_foco.get('cliente_adm', 'N/A')}</span></div>
                        <div><b style="color:#00ff88;">Última Transmissão:</b> {cli_foco.get('hora', 'Agora')}</div>
                        <div><b style="color:#00ff88;">Endereço IP:</b> <code>{cli_foco['ip']}</code></div>
                        <div><b style="color:#00ff88;">MAC Address:</b> <code>{cli_foco['mac']}</code></div>
                        <div><b style="color:#00ff88;">Coordenadas:</b> {cli_foco['lat']:.5f}, {cli_foco['lon']:.5f}</div>
                    </div>
                    <div style="margin-top:10px; font-size:0.85rem; color:#94a3b8;">
                        <b style="color:#00ff88;">Endereço Completo:</b> {cli_foco['endereco']}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_p1, col_p2, col_p3, col_p4 = st.columns([1.5, 1.5, 1.5, 1.5])
            with col_p1:
                st.link_button("🚗 Traçar Rota até Dispositivo", link_maps_cliente, use_container_width=True)
            with col_p2:
                st.link_button("📸 Street View / Foto do Local", link_street_cliente, use_container_width=True)
            with col_p3:
                # BOTÃO EXCLUSIVO ADM MASTER: EDITAR DISPOSITIVO
                if eh_master:
                    if st.button("✏️ Editar Perfil & Vínculo", use_container_width=True):
                        st.session_state["modo_edicao"] = True
                        st.rerun()
                else:
                    st.write("")
            with col_p4:
                if st.button("❌ Desmarcar Perfil / Ver Todos", use_container_width=True):
                    st.session_state["cliente_selecionado"] = None
                    st.session_state["modo_edicao"] = False
                    st.rerun()

    # =========================================================================
    # PAINEL DE DISPOSITIVOS CONECTADOS & MONITORADOS (COM IP ESCURO E ALINHADO)
    # =========================================================================
    st.markdown("""
    <div id="painel-clientes" style="background:rgba(4,25,38,0.85); border:1.0px solid #00ff88; border-radius:12px; padding:13px; margin-top:13px; box-shadow:0 0 20px rgba(0,255,136,0.2);">
        <div style="display:flex; justify-content:center; align-items:center; margin: 0 auto;">
            <span style="font-family:'Rajdhani', sans-serif; font-size:1.3rem; font-weight:700; color:#00ff88;">
                👥 PAINEL : Rastreamento Global 👥 
            </span>
            <span style="font-size:0.85rem; color:#ffaa00;"></span>
        </div>
    """, unsafe_allow_html=True)

    c_head1, c_head2, c_head3, c_head4, c_head5, c_head6, c_head7, c_head8, c_head9 = st.columns([2.5, 1.4, 2, 2, 2.2, 1.2, 1.2, 2.5, 1.5])
    with c_head1: st.markdown("<b style='color:#00ff88;'>Nome</b>", unsafe_allow_html=True)
    with c_head2: st.markdown("<b style='color:#00ff88;'>Tipo</b>", unsafe_allow_html=True)
    with c_head3: st.markdown("<b style='color:#00ff88;'>Pertence a</b>", unsafe_allow_html=True)
    with c_head4: st.markdown("<b style='color:#00ff88;'>Documento</b>", unsafe_allow_html=True)
    with c_head5: st.markdown("<b style='color:#00ff88;'>IP</b>", unsafe_allow_html=True)
    with c_head6: st.markdown("<b style='color:#00ff88;'>Latitude</b>", unsafe_allow_html=True)
    with c_head7: st.markdown("<b style='color:#00ff88;'>Longitude</b>", unsafe_allow_html=True)
    with c_head8: st.markdown("<b style='color:#00ff88;'>Endereço</b>", unsafe_allow_html=True)
    with c_head9: st.markdown("<b style='color:#00ff88;'>Status</b>", unsafe_allow_html=True)

    for cli in lista_visivel:
        col_r1, col_r2, col_r3, col_r4, col_r5, col_r6, col_r7, col_r8, col_r9 = st.columns([2.5, 1.4, 2, 2, 2.2, 1.2, 1.2, 2.5, 1.5])
        
        with col_r1:
            if st.button(f"🔍 {cli['nome']}", key=f"btn_cli_{cli['documento']}", use_container_width=True):
                st.session_state["cliente_selecionado"] = cli["documento"]
                st.session_state["modo_edicao"] = False
                st.rerun()
        with col_r2:
            st.markdown(f"<span style='color:#38bdf8; font-size:0.8rem; font-weight:bold;'>{cli.get('tipo', 'MONITORADO')}</span>", unsafe_allow_html=True)
        with col_r3:
            st.markdown(f"<span style='color:#ffaa00; font-size:0.8rem;'>{cli.get('cliente_adm', 'N/A')[:18]}</span>", unsafe_allow_html=True)
        with col_r4:
            st.markdown(f"<span style='color:#cbd5e1; font-size:0.8rem;'>{cli.get('documento', 'N/A')}</span>", unsafe_allow_html=True)
        with col_r5:
            # IP em container escuro translúcido sem estourar o fundo branco
            st.markdown(f"<code>{cli['ip']}</code>", unsafe_allow_html=True)
        with col_r6:
            st.markdown(f"<span style='color:#38bdf8; font-size:0.8rem;'>{cli['lat']:.4f}</span>", unsafe_allow_html=True)
        with col_r7:
            st.markdown(f"<span style='color:#38bdf8; font-size:0.8rem;'>{cli['lon']:.4f}</span>", unsafe_allow_html=True)
        with col_r8:
            st.markdown(f"<span style='color:#cbd5e1; font-size:0.78rem;'>{cli['endereco'][:22]}...</span>", unsafe_allow_html=True)
        with col_r9:
            eh_aprov = cli.get("aprovado", True)
            badge_classe = "status-badge" if eh_aprov else "status-pending"
            status_texto = cli.get('status', 'ONLINE')
            st.markdown(f"<span class='{badge_classe}'>● {status_texto[:14]}</span>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
