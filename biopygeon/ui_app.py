import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import re
import time
import datetime
from PIL import Image
import traceback

# Configure Streamlit page
st.set_page_config(
    page_title="Biopygeon Web Assistant",
    page_icon=":material/biotech:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Claude-like Styles
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #fcfbf9 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: #1a1a1a !important;
}

/* Hide Streamlit Toolbar (Deploy button, menu) */
[data-testid="stToolbarActions"], [data-testid="stActionElements"], [data-testid="stHeaderActionElements"], .stAppHeaderActionButton, .stToolbarActions {
    visibility: hidden !important;
    display: none !important;
}

/* =========================================================
   SIDEBAR LAYOUT
   ========================================================= */

[data-testid="stSidebar"] {
    background-color: #f7f5ef !important;
    border-right: 1px solid #e5e2d9 !important;
}

/* Container 1: Top Section (Sticky) */
[data-testid="stSidebarUserContent"] > div[data-testid="stVerticalBlock"] > div.stElementContainer:nth-child(1) {
    position: sticky !important;
    top: -15px !important;
    z-index: 999 !important;
    background-color: #f7f5ef !important;
    padding-top: 15px !important;
    padding-bottom: 10px !important;
    margin-bottom: 10px !important;
    border-bottom: 1px solid #e5e2d9 !important;
}

/* ========================================================= */

/* Ensure sidebar toggle button is always visible */
[data-testid="collapsedControl"], [data-testid="baseButton-headerNoPadding"] {
    display: flex !important;
    z-index: 999999 !important;
    visibility: visible !important;
    opacity: 1 !important;
}

[data-testid="collapsedControl"] svg, [data-testid="baseButton-headerNoPadding"] svg {
    fill: #3a2e2b !important;
    color: #3a2e2b !important;
}

/* Fixed App Header mimicking ChatGPT */
header[data-testid="stHeader"] {
    background-color: rgba(247, 245, 239, 0.95) !important;
    backdrop-filter: blur(10px) !important;
    border-bottom: 1px solid #e5e2d9 !important;
    height: 3.5rem !important;
}

header[data-testid="stHeader"]::after {
    content: "Biopygeon AI Assistant";
    position: absolute;
    left: 3.5rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 1.1rem;
    font-weight: 700;
    color: #3a2e2b;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Truncate text on history button */
[data-testid="stSidebar"] .stButton>button p {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    margin: 0 !important;
}

/* Fix Streamlit's inner margins inside sidebar to reduce gaps */
[data-testid="stSidebar"] .stElementContainer {
    margin-bottom: 0 !important;
}

[data-testid="stSidebar"] .stMarkdown h1, 
[data-testid="stSidebar"] .stMarkdown h2, 
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #3a2e2b !important;
    font-weight: 700 !important;
}

[data-testid="stSidebar"] .stButton>button {
    border: 1px solid #e5e2d9 !important;
    background-color: #ffffff !important;
    color: #3a2e2b !important;
    justify-content: flex-start !important;
    padding: 0.4rem 0.8rem !important;
    text-align: left !important;
    font-size: 13.5px !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stButton>button:hover {
    background-color: #f8f7f4 !important;
    border-color: #d97736 !important;
    color: #d97736 !important;
}

/* Typography styles */
h1, h2, h3, h4, h5, h6 {
    color: #3a2e2b !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
}

/* Input and Buttons styling */
.stButton>button {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    border: 1px solid #e5e2d9 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
    font-weight: 500 !important;
    font-size: 14px !important;
}

.stButton>button:hover {
    background-color: #f8f7f4 !important;
    border-color: #d97736 !important;
    color: #d97736 !important;
}

/* Primary buttons (accent colored) */
.stButton>button[kind="primary"] {
    background-color: #d97736 !important;
    color: #ffffff !important;
    border: none !important;
}

/* Success & Info boxes overrides */
.stAlert {
    border-radius: 10px !important;
    background-color: #f7f5ef !important;
    border: 1px solid #edebe4 !important;
}

.stAlert [data-testid="stNotificationContent"] {
    color: #3a2e2b !important;
}

/* Tabs UI overrides */
.stTabs [data-baseweb="tab-list"] {
    background-color: #f3f1eb !important;
    border-radius: 8px !important;
    padding: 4px !important;
    gap: 4px !important;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 6px !important;
    background-color: transparent !important;
    color: #6a5e5a !important;
    border: none !important;
    padding: 8px 16px !important;
    transition: all 0.2s ease !important;
}

.stTabs [aria-selected="true"] {
    background-color: #ffffff !important;
    color: #d97736 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
    font-weight: 600 !important;
}

/* Inline dataframes */
.stDataFrame {
    border: 1px solid #edebe4 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
</style>
""", unsafe_allow_html=True)

# Imports from biopygeon config and engines
from biopygeon.config import get_groq_key, set_groq_key, get_user_email, set_user_email, get_s2_key, set_s2_key
from biopygeon.engines.assistant import agent_router, ask_groq, generate_report, generate_generic_interpretation, GROQ_MODELS
from biopygeon.engines.cache_manager import enforce_cache_limits
import uuid

# Run cache limits check on startup
enforce_cache_limits()

# Helper to load existing keys
initial_groq_key = get_groq_key()
initial_email = get_user_email()
initial_s2_key = get_s2_key()

# --- CHAT HISTORY STORAGE ---
import os
BIOPYGEON_DIR = os.path.expanduser("~/.biopygeon")
os.makedirs(BIOPYGEON_DIR, exist_ok=True)
HISTORY_FILE = os.path.join(BIOPYGEON_DIR, "chat_history.json")

def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_chat_history(history_dict):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_dict, f, ensure_ascii=False, indent=2)

def save_current_chat(messages, session_id):
    if not messages: return
    history = load_chat_history()
    text_msgs = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] in ["user", "assistant"]]
    title = "Sesi Baru"
    for m in text_msgs:
        if m["role"] == "user":
            title = m["content"][:25] + "..." if len(m["content"]) > 25 else m["content"]
            break
    history[session_id] = {
        "title": title,
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "messages": text_msgs
    }
    save_chat_history(history)

# --- SETTINGS MODAL ---
@st.dialog("Pengaturan Biopygeon")
def settings_modal():
    st.markdown("### Konfigurasi API & Email")
    groq_key = st.text_input("Groq API Key", value=initial_groq_key, type="password", help="Kunci API untuk asisten pintar Groq.")
    if groq_key != initial_groq_key:
        set_groq_key(groq_key)
        st.toast("Kunci API Groq berhasil diperbarui!", icon=":material/key:")

    user_email = st.text_input("Email Akademik", value=initial_email, placeholder="contoh@universitas.edu", help="Email diperlukan untuk mengakses Polite Pool di NCBI & OpenAlex.")
    if user_email != initial_email:
        set_user_email(user_email)
        st.toast("Email pengguna berhasil diperbarui!", icon=":material/mail:")

    s2_key = st.text_input("Semantic Scholar API Key (Opsional)", value=initial_s2_key, type="password", help="Kunci API untuk batas rate limit yang lebih tinggi di Semantic Scholar.")
    if s2_key != initial_s2_key:
        set_s2_key(s2_key)
        st.toast("Kunci API Semantic Scholar berhasil diperbarui!", icon=":material/key:")

    st.markdown("### Asisten AI")
    selected_model = st.selectbox("Pilih Model AI", GROQ_MODELS, index=0)
    
    # Reorder GROQ_MODELS in biopygeon assistant module to prioritize selection
    try:
        from biopygeon.engines import assistant
        if selected_model in assistant.GROQ_MODELS:
            assistant.GROQ_MODELS.remove(selected_model)
            assistant.GROQ_MODELS.insert(0, selected_model)
    except Exception as e:
        pass

# --- MANAGE CHATS MODAL ---
@st.dialog("Kelola Riwayat Obrolan")
def manage_chats_modal():
    import uuid
    history_dict = load_chat_history()
    if not history_dict:
        st.info("Tidak ada riwayat obrolan.")
        return
        
    st.markdown("Pilih riwayat obrolan yang ingin dihapus:")
    
    # Sort history
    sorted_history = sorted(history_dict.items(), key=lambda x: x[1]['updated_at'], reverse=True)
    options = {sid: f"{sdata['updated_at']} - {sdata['title']}" for sid, sdata in sorted_history}
    
    selected_sids = st.multiselect("Pilih Obrolan", options=list(options.keys()), format_func=lambda x: options[x], label_visibility="collapsed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Hapus Terpilih", use_container_width=True, type="primary"):
            if selected_sids:
                for sid in selected_sids:
                    del history_dict[sid]
                    if sid == st.session_state.current_session_id:
                        st.session_state.current_session_id = str(uuid.uuid4())
                        st.session_state.messages = []
                save_chat_history(history_dict)
                st.rerun()
            else:
                st.warning("Pilih minimal satu obrolan.")
    with col2:
        if st.button("Hapus Semua", use_container_width=True):
            save_chat_history({})
            st.session_state.current_session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()

# --- INITIALIZE STATE VARIABLES ---
if "current_session_id" not in st.session_state:
    import uuid
    st.session_state.current_session_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history()

if "messages" not in st.session_state:
    if st.session_state.current_session_id in st.session_state.chat_history:
        st.session_state.messages = st.session_state.chat_history[st.session_state.current_session_id].get("messages", [])
    else:
        st.session_state.messages = []

# --- SIDEBAR: Chat History & Options ---
with st.sidebar:
    history_dict = load_chat_history()

    # 1. Top Section (Fixed)
    with st.container():
        st.markdown("<div style='margin-bottom:20px; padding:0 5px;'><span style='font-size:26px; font-weight:600; color:#1a1a1a; font-family: Georgia, serif;'>Biopygeon</span></div>", unsafe_allow_html=True)
        
        if st.button("New chat", icon=":material/add:", use_container_width=True):
            import uuid
            st.session_state.current_session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.uploaded_files = {}
            if "gen_suggestions" in st.session_state:
                del st.session_state.gen_suggestions
            st.rerun()
                
        st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #e5e2d9;'>", unsafe_allow_html=True)
        if st.button("Pengaturan / Profil", icon=":material/settings:", use_container_width=True):
            settings_modal()
            
        if history_dict:
            if st.button("Kelola Riwayat", icon=":material/delete:", use_container_width=True):
                manage_chats_modal()
                
        st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px dashed #e5e2d9;'>", unsafe_allow_html=True)
        st.markdown("<div style='margin: 5px 0 10px 0;'><span style='font-size: 13px; font-weight: 600; color: #8a7e7a;'>Riwayat Chat</span></div>", unsafe_allow_html=True)
        
    # 2. History Section (Scrollable via Flexbox)
    with st.container():
        if not history_dict:
            st.markdown("<p style='font-size: 13px; color: #8a7e7a;'>Belum ada riwayat.</p>", unsafe_allow_html=True)
        else:
            if "history_limit" not in st.session_state:
                st.session_state.history_limit = 15
            
            sorted_history = sorted(history_dict.items(), key=lambda x: x[1]['updated_at'], reverse=True)
            
            for sid, sdata in sorted_history[:st.session_state.history_limit]:
                is_active = (sid == st.session_state.current_session_id)
                btn_icon = ":material/arrow_forward:" if is_active else ":material/chat:"
                btn_label = f"{sdata['title']}"
                if st.button(btn_label, key=f"load_{sid}", icon=btn_icon, use_container_width=True):
                    st.session_state.current_session_id = sid
                    st.session_state.messages = sdata['messages']
                    st.session_state.uploaded_files = {}
                    st.rerun()
            
            if len(sorted_history) > st.session_state.history_limit:
                if st.button("Muat Lebih Banyak", icon=":material/keyboard_arrow_down:", use_container_width=True):
                    st.session_state.history_limit += 15
                    st.rerun()

    # Manage uploaded files state
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = {}

if "last_action_type" not in st.session_state:
    st.session_state.last_action_type = None
if "last_df" not in st.session_state:
    st.session_state.last_df = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "last_primer_data" not in st.session_state:
    st.session_state.last_primer_data = None
if "last_primer_seq" not in st.session_state:
    st.session_state.last_primer_seq = ""
if "last_primer_params" not in st.session_state:
    st.session_state.last_primer_params = {}
if "last_pdb_data" not in st.session_state:
    st.session_state.last_pdb_data = None
if "last_fasta_data" not in st.session_state:
    st.session_state.last_fasta_data = None
if "last_ai_interpretation" not in st.session_state:
    st.session_state.last_ai_interpretation = None
if "last_blast_rid" not in st.session_state:
    st.session_state.last_blast_rid = None

# --- MAIN UI AREA ---

# Suggestions Center: Show beautiful quick prompts if chat is empty
if len(st.session_state.messages) == 0:
    # Header Section
    st.markdown("# :material/biotech: Biopygeon AI Assistant", unsafe_allow_html=True)
    st.markdown("<p style='color: #6a5e5a; font-size: 15px; margin-bottom: 25px;'>Asisten bioinformatika dan penulisan sains publikasi ilmiah berwawasan AI</p>", unsafe_allow_html=True)

    st.markdown("""
    <div class="custom-card" style="background-color: #f7f5ef; border-color: #e5e2d9; margin-bottom: 25px;">
        <div class="custom-card-header" style="border-bottom: 1px solid #e5e2d9;">Selamat datang di Biopygeon Web UI!</div>
        <p style="font-size: 14px; line-height: 1.5; color: #3a2e2b;">
            Ini adalah antarmuka web interaktif asisten <b>Biopygeon</b>. Anda bisa berkomunikasi langsung menggunakan bahasa alami untuk melakukan analisis bioinformatika, mencari referensi jurnal, mendesain primer PCR, menyinkronkan format manuskrip Word, dan merender grafik visualisasi data premium.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Show suggestion buttons based on uploaded files
    st.markdown("##### :material/lightbulb: Mulai dengan salah satu saran berikut:")
    
    # Generic suggestions
    import random
    all_gen_suggestions = [
        "Cari 5 literatur tentang terapi mRNA terbaru untuk kanker",
        "Tolong carikan struktur kristal untuk protein insulin",
        "Buat rancangan primer PCR standar untuk sekuens DNA target",
        "Jelaskan mekanisme kerja obat metformin menggunakan analisis literatur",
        "Berikan saya perbandingan struktur 3D dari hemoglobin dan mioglobin",
        "Buatkan format manuskrip publikasi IEEE dari dokumen draf saya",
        "Analisis sifat fisikokimia protein p53",
    ]
    if "gen_suggestions" not in st.session_state:
        st.session_state.gen_suggestions = random.sample(all_gen_suggestions, min(3, len(all_gen_suggestions)))
    gen_suggestions = st.session_state.gen_suggestions

    # File-specific suggestions
    file_suggestions = []
    if st.session_state.uploaded_files:
        for fname, fmeta in st.session_state.uploaded_files.items():
            if fmeta["type"] == "csv":
                file_suggestions.append(f"Buat heatmap ekspresi dari file '{fname}'")
                file_suggestions.append(f"Harmonisasikan data '{fname}' dan simpan hasilnya")
                file_suggestions.append(f"Buat volcano plot dari '{fname}' dengan kolom pvalue dan log2fc")
            elif fmeta["type"] in ["fasta", "fa"]:
                file_suggestions.append(f"Jalankan analisis ProtParam untuk sekuens dari '{fname}'")
                file_suggestions.append(f"Jalankan pencarian BLAST dari sekuens '{fname}'")
            elif fmeta["type"] == "docx":
                docx_files = [n for n, m in st.session_state.uploaded_files.items() if m["type"] == "docx"]
                if len(docx_files) >= 2:
                    file_suggestions.append(f"Format manuskrip '{docx_files[0]}' menggunakan template '{docx_files[1]}'")
                else:
                    file_suggestions.append(f"Format manuskrip '{fname}' menggunakan template Word")

    all_suggestions = file_suggestions + gen_suggestions
    cols = st.columns(2)
    for idx, sug in enumerate(all_suggestions[:4]):
        col_idx = idx % 2
        with cols[col_idx]:
            if st.button(sug, key=f"sug_{idx}", use_container_width=True):
                st.session_state.trigger_prompt = sug
                st.rerun()
                
    # Feature Catalog Expander
    with st.expander("Lihat Katalog Kemampuan Biopygeon", icon=":material/auto_awesome:"):
        features_html = '''
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; padding: 10px 0;">
           <!-- Card 1 -->
           <div style="border: 1px solid #e5e2d9; border-radius: 8px; padding: 12px; display: flex; gap: 12px; align-items: center; background: white;">
              <div style="color: #d97736; display: flex;">
                 <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
              </div>
              <div>
                 <div style="font-size: 14px; font-weight: 600; color: #1a1a1a;">Pencarian Literatur</div>
                 <div style="font-size: 12px; color: #6a5e5a;">Semantic Scholar API terintegrasi</div>
              </div>
           </div>
           
           <!-- Card 2 -->
           <div style="border: 1px solid #e5e2d9; border-radius: 8px; padding: 12px; display: flex; gap: 12px; align-items: center; background: white;">
              <div style="color: #d97736; display: flex;">
                 <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/></svg>
              </div>
              <div>
                 <div style="font-size: 14px; font-weight: 600; color: #1a1a1a;">Desain Primer PCR</div>
                 <div style="font-size: 12px; color: #6a5e5a;">Kalkulasi parameter PCR otomatis</div>
              </div>
           </div>

           <!-- Card 3 -->
           <div style="border: 1px solid #e5e2d9; border-radius: 8px; padding: 12px; display: flex; gap: 12px; align-items: center; background: white;">
              <div style="color: #d97736; display: flex;">
                 <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>
              </div>
              <div>
                 <div style="font-size: 14px; font-weight: 600; color: #1a1a1a;">Struktur PDB 3D</div>
                 <div style="font-size: 12px; color: #6a5e5a;">Analisis makromolekul & rendering</div>
              </div>
           </div>

           <!-- Card 4 -->
           <div style="border: 1px solid #e5e2d9; border-radius: 8px; padding: 12px; display: flex; gap: 12px; align-items: center; background: white;">
              <div style="color: #d97736; display: flex;">
                 <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
              </div>
              <div>
                 <div style="font-size: 14px; font-weight: 600; color: #1a1a1a;">Analisis ProtParam</div>
                 <div style="font-size: 12px; color: #6a5e5a;">Sifat fisikokimia sekuens FASTA</div>
              </div>
           </div>

           <!-- Card 5 -->
           <div style="border: 1px solid #e5e2d9; border-radius: 8px; padding: 12px; display: flex; gap: 12px; align-items: center; background: white;">
              <div style="color: #d97736; display: flex;">
                 <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/></svg>
              </div>
              <div>
                 <div style="font-size: 14px; font-weight: 600; color: #1a1a1a;">Visualisasi Omics</div>
                 <div style="font-size: 12px; color: #6a5e5a;">Heatmap & Volcano Plot Interaktif</div>
              </div>
           </div>

           <!-- Card 6 -->
           <div style="border: 1px solid #e5e2d9; border-radius: 8px; padding: 12px; display: flex; gap: 12px; align-items: center; background: white;">
              <div style="color: #d97736; display: flex;">
                 <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" x2="8" y1="13" y2="13"/><line x1="16" x2="8" y1="17" y2="17"/><line x1="10" x2="8" y1="9" y2="9"/></svg>
              </div>
              <div>
                 <div style="font-size: 14px; font-weight: 600; color: #1a1a1a;">Format Manuskrip</div>
                 <div style="font-size: 12px; color: #6a5e5a;">Templating Word (.docx) otomatis</div>
              </div>
           </div>

           <!-- Card 7 -->
           <div style="border: 1px solid #e5e2d9; border-radius: 8px; padding: 12px; display: flex; gap: 12px; align-items: center; background: white;">
              <div style="color: #d97736; display: flex;">
                 <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z"/><path d="M7 7h.01"/></svg>
              </div>
              <div>
                 <div style="font-size: 14px; font-weight: 600; color: #1a1a1a;">Eksekusi Otonom (ReAct)</div>
                 <div style="font-size: 12px; color: #6a5e5a;">Siklus agen AI independen</div>
              </div>
           </div>

           <!-- Card 8 -->
           <div style="border: 1px solid #e5e2d9; border-radius: 8px; padding: 12px; display: flex; gap: 12px; align-items: center; background: white;">
              <div style="color: #d97736; display: flex;">
                 <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
              </div>
              <div>
                 <div style="font-size: 14px; font-weight: 600; color: #1a1a1a;">Python Code Interpreter</div>
                 <div style="font-size: 12px; color: #6a5e5a;">Pemrosesan data dinamis</div>
              </div>
           </div>
        </div>
        '''
        st.markdown(features_html, unsafe_allow_html=True)

# --- DISPLAY CHAT HISTORY ---
for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        # Text Content
        st.markdown(message["content"])
        
        # Interactive Renderers (if attached to message)
        if "dataframe" in message and message["dataframe"] is not None:
            st.dataframe(message["dataframe"], use_container_width=True)
            
        if "html_content" in message and message["html_content"]:
            st.components.v1.html(message["html_content"], height=550, scrolling=True)
            
        if "image_path" in message and message["image_path"]:
            st.image(message["image_path"], caption="Visualisasi Jaringan / Pohon Filogenetik", use_container_width=True)
            
        if "pdb_content" in message and message["pdb_content"]:
            try:
                import py3Dmol
                from stmol import showmol
                with open(message["pdb_content"], 'r') as f:
                    pdb_data = f.read()
                
                view = py3Dmol.view(width=800, height=400)
                view.addModel(pdb_data, "pdb")
                view.setStyle({'cartoon': {'color': 'spectrum'}})
                view.setBackgroundColor('#f7f5ef')
                view.zoomTo()
                showmol(view, height=400, width=800)
            except ImportError:
                st.error("Pustaka 3D Viewer belum terinstal. Jalankan: `pip install stmol py3Dmol`")
            except Exception as e:
                st.error(f"Gagal memuat visualisasi 3D: {e}")
            
        # Download buttons
        if "download_buttons" in message and message["download_buttons"]:
            download_cols = st.columns(len(message["download_buttons"]))
            for btn_idx, dbtn in enumerate(message["download_buttons"]):
                with download_cols[btn_idx]:
                    st.download_button(
                        label=dbtn["label"],
                        data=dbtn["data"],
                        file_name=dbtn["file_name"],
                        mime=dbtn.get("mime", "application/octet-stream"),
                        key=f"dl_{msg_idx}_{btn_idx}",
                        icon=dbtn.get("icon", None)
                    )

# --- CHAT INPUT & EXECUTION LOOP ---

# 1. Display horizontal file chips
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}

if st.session_state.uploaded_files:
    chips_html = '<div class="file-chips-container">'
    for fname, fmeta in st.session_state.uploaded_files.items():
        chips_html += f"""
        <div style="background-color: #ffffff; border: 1px solid #edebe4; border-radius: 8px; padding: 4px 10px; display: flex; align-items: center; gap: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.01);">
            <span style="font-size: 12px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg></span>
            <span style="font-size: 12px; color: #1a1a1a; font-weight: 500;">{fname}</span>
            <span style="font-size: 10px; color: #8a7e7a;">({fmeta['size']/1024:.1f} KB)</span>
        </div>
        """
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

# 2. Chat input rendered at root (natively sticky at the bottom)
chat_submission = st.chat_input(
    "Tanyakan sesuatu ke asisten Biopygeon atau berikan file untuk dianalisis...",
    accept_file=True,
    file_type=["csv", "fasta", "fa", "pdb", "docx"]
)

user_prompt = ""
if "trigger_prompt" in st.session_state:
    user_prompt = st.session_state.trigger_prompt
    del st.session_state.trigger_prompt

if chat_submission:
    # If the user typed manually, it takes precedence
    user_prompt = chat_submission.text
    uploaded_files = chat_submission.files if hasattr(chat_submission, "files") and chat_submission.files else []
    
    # Process uploaded files
    if uploaded_files:
        for uf in uploaded_files:
            from biopygeon.engines.cache_manager import get_cache_dir
            file_path = os.path.join(get_cache_dir(), uf.name)
            # Write bytes to disk
            with open(file_path, "wb") as f:
                f.write(uf.getbuffer())
            # Save metadata
            if uf.name not in st.session_state.uploaded_files:
                st.session_state.uploaded_files[uf.name] = {
                    "path": os.path.abspath(file_path),
                    "size": uf.size,
                    "type": uf.name.split(".")[-1].lower()
                }
                st.toast(f"Berhasil mengunggah: {uf.name}", icon=":material/folder:")
        
        # If there's no prompt, we just rerun to show the files
        if not user_prompt:
            time.sleep(0.5)
            st.rerun()

if user_prompt:
    # Check API Key
    groq_key = get_groq_key()
    if not groq_key:
        st.error("🔑 Harap masukkan Kunci API Groq Anda di panel kiri terlebih dahulu (ikon roda gigi).")
        st.stop()

    # Append User prompt to chat
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Generate Response
    with st.chat_message("assistant"):
        # Setup run message components
        message_placeholder = st.empty()
        status_box = st.status("Asisten sedang memikirkan prompt Anda...", state="running")
        
        # Prepare context of uploaded files
        system_context = ""
        if st.session_state.uploaded_files:
            files_info = []
            for fname, fmeta in st.session_state.uploaded_files.items():
                files_info.append(f"- '{fname}' (lokasi absolut: '{fmeta['path']}')")
            files_list_str = "\n".join(files_info)
            system_context = f"\n\n[INFO SISTEM: File-file berikut diunggah dan tersedia di direktori kerja:\n{files_list_str}\nHarap prioritaskan nama-nama file ini saat mengisi parameter input (seperti input_csv, draft_docx, template_docx, input_fasta, dll).]"
        
        # Enriched prompt
        enriched_prompt = user_prompt + system_context
        
        # Create chat history compatible with groq router
        api_history = []
        for msg in st.session_state.messages[:-1]: # exclude latest prompt which we will send enriched
            api_history.append({"role": msg["role"], "content": msg["content"]})
            
        # Call agent_router
        try:
            status_box.update(label="Memetakan aksi dengan AI Router...", state="running")
            response = agent_router(enriched_prompt, history=api_history)
        except Exception as e:
            status_box.update(label="Gagal menghubungi AI Router", state="error")
            st.error(f"Error AI: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Maaf, gagal berinteraksi dengan AI: {e}"})
            st.stop()
            
        from biopygeon.engines.audit_logger import log_action
        action = response.get('action', 'chat')
        params = response.get('params', {})
        log_action("ZeroShot_Router", action, params)
        
        reply = response.get('reply', '')
        
        # Render the AI reply
        message_placeholder.markdown(reply)
        
        # Keep track of message outputs
        msg_df = None
        msg_html = None
        msg_img = None
        msg_pdb = None
        msg_downloads = []
        
        # Progress callback for engines
        def ui_progress_callback(msg, advance=0):
            status_box.update(label=f"Eksekusi: {msg}", state="running")

        # Execute actions
        try:
            # 1. CHAT ACTION
            if action == "chat":
                status_box.update(label="Aksi selesai", state="complete")
                
            # X. AUTONOMOUS REACT PIPELINE
            elif action == "run_autonomous_pipeline":
                status_box.update(label="Memulai proses berpikir otonom...", state="running")
                from biopygeon.engines.agent_loop import run_autonomous_loop
                from biopygeon.engines.tool_registry import FULL_TOOLS_SCHEMA, FULL_FUNCTIONS
                
                final_answer, loop_messages = run_autonomous_loop(
                    user_prompt=enriched_prompt,
                    tools_schema=FULL_TOOLS_SCHEMA,
                    function_registry=FULL_FUNCTIONS,
                    max_steps=5,
                    progress_callback=lambda m: status_box.update(label=f"Agent: {m}", state="running")
                )
                
                # Extract any 3D rendering or downloads from tool responses
                import ast
                for msg in loop_messages:
                    if msg.get("role") == "tool":
                        if msg["name"] == "render_3d_structure":
                            try:
                                res_dict = ast.literal_eval(msg["content"])
                                if "pdb_content" in res_dict and res_dict["pdb_content"]:
                                    msg_pdb = res_dict["pdb_content"]
                            except:
                                pass
                        elif msg["name"] in ["fetch_alphafold_structure", "download_protein_data"]:
                            if "downloaded to:" in msg["content"]:
                                path = msg["content"].split("downloaded to:")[-1].strip()
                                if path.endswith(".pdb") or path.endswith(".cif"):
                                    msg_pdb = path
                
                reply = f"{reply}\n\n**Hasil Eksekusi Otonom:**\n{final_answer}"
                message_placeholder.markdown(reply)
                status_box.update(label="Siklus otonom selesai!", state="complete")
                
            # 2. SEMANTIC SEARCH & LITERATURE REVIEW
            elif action == "lit_search":
                status_box.update(label="Mencari literatur sains...", state="running")
                from biopygeon.engines.literature import search_literature_with_fallback
                query = params.get("query", "science")
                limit = params.get("limit", 5)
                year_filter = params.get("year_filter")
                
                results = search_literature_with_fallback(
                    query, 
                    max_results=limit, 
                    year_filter=year_filter, 
                    progress_callback=ui_progress_callback
                )
                
                if not results:
                    status_box.update(label="Pencarian selesai (Kosong)", state="complete")
                    reply = f"{reply}\n\n*Tidak ada paper yang cocok untuk pencarian ini.*"
                    message_placeholder.markdown(reply)
                else:
                    df = pd.DataFrame(results)
                    # Save states
                    st.session_state.last_df = df
                    st.session_state.last_query = query
                    st.session_state.last_action_type = "lit_search"
                    
                    status_box.update(label="Menganalisis paper dengan AI...", state="running")
                    ai_response_text = generate_report(df, user_prompt)
                    
                    # Markdown synthesis output
                    reply = f"{reply}\n\n{ai_response_text}"
                    message_placeholder.markdown(reply)
                    st.session_state.last_ai_interpretation = ai_response_text
                    
                    # Output dataframe
                    msg_df = df
                    
                    # Generate report exports immediately for user downloads
                    status_box.update(label="Menyiapkan format dokumen ekspor...", state="running")
                    from biopygeon.engines.report_generator import save_pdf_report, save_html_dashboard
                    
                    # Export CSV bytes
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    msg_downloads.append({
                        "label": "Unduh Hasil CSV",
                        "icon": ":material/bar_chart:",
                        "data": csv_data,
                        "file_name": "hasil_riset.csv",
                        "mime": "text/csv"
                    })
                    
                    # Export HTML Dashboard
                    try:
                        html_path = save_html_dashboard(f"Literature Review: {query}", "Biopygeon Autonomous Literature Mining", ai_response_text, os.getcwd(), dataframe=df, progress_callback=lambda m, a=0: None)
                        if os.path.exists(html_path):
                            with open(html_path, "r", encoding="utf-8") as hf:
                                h_data = hf.read()
                            msg_downloads.append({
                                "label": "Unduh Dasbor HTML",
                        "icon": ":material/language:",
                                "data": h_data,
                                "file_name": "Bibliometric_Dashboard.html",
                                "mime": "text/html"
                            })
                    except Exception as he:
                        pass
                        
                    # Export PDF Report
                    try:
                        pdf_path = save_pdf_report(query, df, ai_response_text, os.getcwd(), progress_callback=lambda m, a=0: None)
                        if os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pf:
                                p_data = pf.read()
                            msg_downloads.append({
                                "label": "Unduh Laporan PDF",
                        "icon": ":material/description:",
                                "data": p_data,
                                "file_name": "Laporan_Riset.pdf",
                                "mime": "application/pdf"
                            })
                    except Exception as pe:
                        pass
                    
                    status_box.update(label="Pencarian & Laporan AI Selesai!", state="complete")
                    
            # 3. BIBLIOMETRICS MAPPING
            elif action == "lit_search_bibliometrics":
                status_box.update(label="Memulai ekstraksi data massal (Bibliometrik)...", state="running")
                from biopygeon.engines.literature import search_literature_with_fallback
                from biopygeon.engines.bibliometrics import render_bibliometric_dashboard
                query = params.get("query", "science")
                limit = params.get("limit", 100)
                
                results, query_meta = search_literature_with_fallback(
                    query, 
                    max_results=limit, 
                    sort_by="1", 
                    progress_callback=ui_progress_callback, 
                    skip_ranking=True, 
                    return_metadata=True
                )
                
                if not results:
                    status_box.update(label="Gagal mengekstrak data bibliometrik", state="error")
                    st.error("Tidak ada literatur yang ditemukan.")
                else:
                    df = pd.DataFrame(results)
                    st.session_state.last_df = df
                    st.session_state.last_query = query
                    st.session_state.last_action_type = "lit_search"
                    
                    html_path = os.path.join(os.getcwd(), "Bibliometric_Dashboard.html")
                    render_bibliometric_dashboard(df, output_path=html_path, query=query, limit=limit, metadata=query_meta)
                    
                    if os.path.exists(html_path):
                        with open(html_path, "r", encoding="utf-8") as f:
                            msg_html = f.read()
                            
                        msg_downloads.append({
                            "label": "Unduh Dashboard Bibliometrik",
                        "icon": ":material/language:",
                            "data": msg_html,
                            "file_name": "Bibliometric_Dashboard.html",
                            "mime": "text/html"
                        })
                        
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        msg_downloads.append({
                            "label": "Unduh Metadata CSV",
                        "icon": ":material/bar_chart:",
                            "data": csv_data,
                            "file_name": "bibliometrik_data.csv",
                            "mime": "text/csv"
                        })
                        
                    status_box.update(label="Visualisasi peta bibliometrik selesai!", state="complete")
                    
            # 4. FIND PROTEIN STRUCTURE
            elif action == "find_protein":
                status_box.update(label="Mencari protein di database PDB...", state="running")
                from biopygeon.engines.biology import search_protein_structure
                protein_name = params.get("protein_name", "")
                limit = params.get("limit", 5)
                
                results = search_protein_structure(protein_name, max_results=limit, progress_callback=ui_progress_callback)
                if not results:
                    status_box.update(label="Struktur tidak ditemukan", state="complete")
                    message_placeholder.markdown(f"{reply}\n\n*Tidak ada koordinat PDB yang cocok.*")
                else:
                    df = pd.DataFrame(results)
                    st.session_state.last_pdb_data = results
                    st.session_state.last_action_type = "find_protein"
                    
                    msg_df = df
                    
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    msg_downloads.append({
                        "label": "Unduh Hasil CSV",
                        "icon": ":material/bar_chart:",
                        "data": csv_data,
                        "file_name": "pdb_search_results.csv",
                        "mime": "text/csv"
                    })
                    
                    status_box.update(label="Hasil pencarian PDB siap!", state="complete")
                    
            # 5. FETCH FASTA SEQUENCE
            elif action == "fetch_sequence":
                status_box.update(label="Mengambil sekuens FASTA...", state="running")
                from biopygeon.engines.biology import fetch_fasta_sequence
                accession = params.get("accession", "")
                
                fasta_data = fetch_fasta_sequence(accession, progress_callback=ui_progress_callback)
                if not fasta_data:
                    status_box.update(label="Gagal memuat FASTA", state="error")
                    st.error(f"Sekuens untuk '{accession}' tidak ditemukan.")
                else:
                    st.session_state.last_fasta_data = fasta_data
                    st.session_state.last_action_type = "fetch_sequence"
                    
                    message_placeholder.markdown(f"{reply}\n\n```fasta\n{fasta_data[:1500]}\n...\n```")
                    
                    msg_downloads.append({
                        "label": "Unduh FASTA",
                        "icon": ":material/subject:",
                        "data": fasta_data,
                        "file_name": f"{accession}.fasta",
                        "mime": "text/plain"
                    })
                    
                    status_box.update(label="FASTA berhasil diambil!", state="complete")
                    
            # 6. DOWNLOAD PROTEIN FILES
            elif action == "download_protein_data":
                status_box.update(label="Mengunduh file struktur...", state="running")
                from biopygeon.engines.biology import download_protein_files
                pdb_id = params.get("pdb_id", "")
                file_type = params.get("file_type", "both")
                
                from biopygeon.engines.cache_manager import get_cache_dir
                downloads_path = get_cache_dir()
                
                downloaded = download_protein_files(pdb_id, file_type, downloads_path, progress_callback=ui_progress_callback)
                if not downloaded:
                    status_box.update(label="Gagal mengunduh struktur", state="error")
                else:
                    msg_text = f"{reply}\n\n**Struktur berhasil diproses dan siap diunduh:**\n"
                    for f in downloaded:
                        msg_text += f"- Struktur {os.path.basename(f)}\n"
                        with open(f, "rb") as fd:
                            fdata = fd.read()
                        
                        f_ext = f.split(".")[-1].lower()
                        mime_type = "text/plain" if f_ext != "pdb" else "chemical/x-pdb"
                        msg_downloads.append({
                            "label": f"💾 Unduh {os.path.basename(f)}",
                            "data": fdata,
                            "file_name": os.path.basename(f),
                            "mime": mime_type
                        })
                        if f_ext == "pdb":
                            msg_pdb = f
                    message_placeholder.markdown(msg_text)
                    status_box.update(label="Unduhan selesai!", state="complete")
                    
            # 7. EXTRACT GENETIC DOMAIN
            elif action == "extract_domain":
                status_box.update(label="Mengekstrak domain...", state="running")
                from biopygeon.engines.biology import extract_domain
                seq = params.get("sequence", "")
                motif = params.get("motif", "WFQNHR")
                before_aa = params.get("before_aa", 30)
                after_aa = params.get("after_aa", 25)
                
                res = extract_domain(seq, motif, before_aa, after_aa)
                msg_text = f"{reply}\n\n" \
                           f"**Hasil Ekstraksi Domain:**\n" \
                           f"- **Panjang Sekuens Penuh**: {res['full_protein_length']} aa\n" \
                           f"- **Koordinat Domain**: Asam amino {res['domain_start_aa']} s.d {res['domain_end_aa']}\n" \
                           f"- **Panjang Domain**: {res['domain_nt_length']} bp\n" \
                           f"\n**Sekuens Domain DNA:**\n`{res['domain_nucleotide_seq']}`"
                message_placeholder.markdown(msg_text)
                
                msg_downloads.append({
                    "label": "Ekspor Data JSON",
                        "icon": ":material/save:",
                    "data": json.dumps(res, indent=4),
                    "file_name": "domain_results.json",
                    "mime": "application/json"
                })
                
                status_box.update(label="Ekstraksi domain selesai!", state="complete")
                
            # 8. CALCULATE RECOMBINANT PARAMS
            elif action == "calculate_protein_params":
                status_box.update(label="Menghitung sifat fisikokimia kloning...", state="running")
                from biopygeon.engines.biology import calculate_protein_params
                seq = params.get("sequence", "")
                tag = params.get("fusion_tag", "LEHHHHHH")
                
                res = calculate_protein_params(seq, tag)
                msg_text = f"{reply}\n\n" \
                           f"| Parameter | Nilai | Keterangan |\n" \
                           f"| --- | --- | --- |\n" \
                           f"| **Panjang Asam Amino** | {res['length_aa']} aa | Panjang rantai protein rekombinan |\n" \
                           f"| **Berat Molekul** | {res['molecular_weight_kDa']} kDa | Berat molekul total |\n" \
                           f"| **Titik Isoelektrik (pI)** | {res['isoelectric_point']} | pH tanpa muatan bersih |\n" \
                           f"| **Muatan Bersih pH 7.0** | {res['charge_at_ph7']} | Muatan bersih fisiologis |"
                message_placeholder.markdown(msg_text)
                status_box.update(label="Kalkulasi sifat fisikokimia selesai!", state="complete")
                
            # 9. PROTPARAM PHYSICAL CHEMISTRY
            elif action == "analyze_protparam":
                status_box.update(label="Menganalisis sifat fisikokimia protein...", state="running")
                from biopygeon.engines.biology import calculate_protparam
                seq = params.get("sequence", "")
                
                res_str, data_dict = calculate_protparam(seq)
                
                status_box.update(label="Menyusun interpretasi AI...", state="running")
                ai_text = ask_groq("Interpretasikan hasil ProtParam berikut:\n" + res_str)
                
                reply = f"{reply}\n\n**Hasil Analisis ProtParam:**\n\n```\n{res_str}\n```\n\n**Interpretasi AI:**\n{ai_text}"
                message_placeholder.markdown(reply)
                
                txt_data = f"=== HASIL PROTPARAM ===\n{res_str}\n\n=== INTERPRETASI AI ===\n{ai_text}"
                msg_downloads.append({
                    "label": "Unduh Laporan TXT",
                        "icon": ":material/subject:",
                    "data": txt_data,
                    "file_name": "laporan_protparam.txt",
                    "mime": "text/plain"
                })
                
                status_box.update(label="Analisis ProtParam Selesai!", state="complete")
                
            # 10. RUN BLAST SEARCH
            elif action == "run_blast":
                status_box.update(label="Menjalankan pencarian BLAST di NCBI...", state="running")
                from biopygeon.engines.biology import run_ncbi_blast
                seq = params.get("sequence", "")
                prog = params.get("program", "blastp")
                default_db = "nr_cluster_seq" if prog == "blastp" else "nt"
                db = params.get("database", default_db) or default_db
                limit = params.get("limit", 5)
                
                results, blast_rid = run_ncbi_blast(
                    seq, 
                    program=prog, 
                    database=db, 
                    max_results=limit, 
                    progress_callback=ui_progress_callback
                )
                
                st.session_state.last_blast_rid = blast_rid
                st.session_state.last_action_type = "run_blast"
                
                if not results:
                    status_box.update(label="Tidak ada homologi ditemukan", state="complete")
                    reply = f"{reply}\n\n*Pencarian BLAST tidak menghasilkan hit.*"
                    message_placeholder.markdown(reply)
                else:
                    df = pd.DataFrame(results)
                    display_df = df.drop(columns=["alignment_text"], errors="ignore")
                    msg_df = display_df
                    
                    align_md = "\n\n### 🧬 Detail Alignment\n"
                    for idx, row in enumerate(results):
                        align_md += f"**Hit {idx+1}: {row['accession']}** - {row['description']}\n```text\n{row.get('alignment_text', '')}\n```\n"
                    
                    status_box.update(label="Menulis interpretasi hasil BLAST...", state="running")
                    data_str = display_df.to_string()
                    ai_text = ask_groq("Interpretasikan hasil BLAST (homologi) ini secara singkat:\n" + data_str)
                    
                    reply = f"{reply}\n\n**Interpretasi AI:**\n{ai_text}{align_md}"
                    message_placeholder.markdown(reply)
                    
                    # Export CSV
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    msg_downloads.append({
                        "label": "Unduh Hasil CSV",
                        "icon": ":material/bar_chart:",
                        "data": csv_data,
                        "file_name": "blast_results.csv",
                        "mime": "text/csv"
                    })
                    
                    # Ask NCBI for formats (TXT)
                    try:
                        status_box.update(label="Mengunduh laporan BLAST text...", state="running")
                        r = requests.get("https://blast.ncbi.nlm.nih.gov/Blast.cgi", params={"CMD": "Get", "FORMAT_TYPE": "Text", "RID": blast_rid})
                        if r.ok:
                            msg_downloads.append({
                                "label": "Unduh Laporan NCBI Text",
                        "icon": ":material/description:",
                                "data": r.text,
                                "file_name": f"blast_{blast_rid}.txt",
                                "mime": "text/plain"
                            })
                    except:
                        pass
                        
                    # Export PDF Report
                    try:
                        status_box.update(label="Merender PDF Laporan BLAST...", state="running")
                        from biopygeon.engines.report_generator import save_generic_pdf_report
                        pdf_path = save_generic_pdf_report("BLAST Homology Report", f"Program: {prog} | Database: {db}", ai_text, os.getcwd(), raw_data=df, full_sequence=seq)
                        if os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as pf:
                                p_data = pf.read()
                            msg_downloads.append({
                                "label": "Unduh PDF Laporan Cerdas",
                        "icon": ":material/description:",
                                "data": p_data,
                                "file_name": "Laporan_BLAST.pdf",
                                "mime": "application/pdf"
                            })
                    except:
                        pass
                        
                    status_box.update(label="BLAST berhasil selesai!", state="complete")
                    
            # 11. PREPARE STRUCTURE FOR DOCKING
            elif action == "prepare_docking":
                status_box.update(label="Mempersiapkan struktur untuk docking...", state="running")
                from biopygeon.engines.biology import prepare_structure_for_vina
                in_path = params.get("input_path", "")
                out_path = params.get("output_path", "cleaned_docking.pdbqt")
                p_type = params.get("prep_type", "target")
                
                res_path = prepare_structure_for_vina(
                    in_path, 
                    out_path, 
                    prep_type=p_type.lower(), 
                    progress_callback=ui_progress_callback
                )
                
                if os.path.exists(res_path):
                    with open(res_path, "rb") as f:
                        f_data = f.read()
                    msg_downloads.append({
                        "label": f"💾 Unduh {os.path.basename(res_path)}",
                        "data": f_data,
                        "file_name": os.path.basename(res_path),
                        "mime": "application/octet-stream"
                    })
                    reply = f"{reply}\n\n**Struktur berhasil dibersihkan dan siap digunakan.** File disimpan sebagai `{os.path.basename(res_path)}`."
                    message_placeholder.markdown(reply)
                status_box.update(label="Persiapan docking selesai!", state="complete")
                
            # 12. RUN MULTIPLE SEQUENCE ALIGNMENT (MSA)
            elif action == "run_msa":
                status_box.update(label="Mengirim pekerjaan MSA ke EBI Clustal Omega...", state="running")
                from biopygeon.engines.biology import run_ebi_clustalo
                in_path = params.get("input_fasta", "")
                out_path = params.get("output_fasta", "alignment.fasta")
                
                res_path = run_ebi_clustalo(in_path, out_path, progress_callback=ui_progress_callback)
                if os.path.exists(res_path):
                    with open(res_path, "r", encoding="utf-8") as f:
                        f_data = f.read()
                    msg_downloads.append({
                        "label": "Unduh Alignment FASTA",
                        "icon": ":material/subject:",
                        "data": f_data,
                        "file_name": os.path.basename(res_path),
                        "mime": "text/plain"
                    })
                    
                    display_align = "\n".join(f_data.split("\n")[:25]) + "\n..."
                    reply = f"{reply}\n\n**Hasil MSA berhasil disimpan ke `{os.path.basename(res_path)}`:**\n```\n{display_align}\n```"
                    message_placeholder.markdown(reply)
                status_box.update(label="MSA selesai!", state="complete")
                
            # 13. PLOT PHYLOGENETIC TREE
            elif action == "plot_phylo":
                status_box.update(label="Membangun visualisasi Pohon Filogenetik...", state="running")
                from biopygeon.engines.biology import render_phylogenetic_tree
                aln_file = params.get("alignment_file", "")
                out_file = params.get("output_tiff", "phylo_tree.tiff")
                
                res_path = render_phylogenetic_tree(aln_file, out_file, progress_callback=ui_progress_callback)
                if os.path.exists(res_path):
                    # Convert TIFF to PNG for inline rendering
                    png_path = os.path.join(os.getcwd(), "phylo_tree.png")
                    try:
                        with Image.open(res_path) as img:
                            img.save(png_path, "PNG")
                        msg_img = png_path
                    except Exception as img_err:
                        pass
                    
                    with open(res_path, "rb") as f:
                        f_data = f.read()
                        
                    msg_downloads.append({
                        "label": "Unduh Publikasi TIFF (300 DPI)",
                        "icon": ":material/image:",
                        "data": f_data,
                        "file_name": os.path.basename(res_path),
                        "mime": "image/tiff"
                    })
                    
                status_box.update(label="Pohon Filogenetik siap!", state="complete")
                
            # 14. PCR PRIMER DESIGN
            elif action == "design_primer":
                status_box.update(label="Mendesain PCR primer...", state="running")
                from biopygeon.engines.biology import design_pcr_primers
                seq = params.get("sequence", "")
                
                prod_min = params.get("prod_size_min", 150)
                prod_max = params.get("prod_size_max", 500)
                tm_opt = params.get("tm_opt", 60.0)
                tm_min = params.get("tm_min", 57.0)
                tm_max = params.get("tm_max", 63.0)
                fwd_enzyme = params.get("fwd_enzyme", "")
                fwd_enzyme_seq = params.get("fwd_enzyme_seq", "")
                rev_enzyme = params.get("rev_enzyme", "")
                rev_enzyme_seq = params.get("rev_enzyme_seq", "")
                fwd_overhang = params.get("fwd_overhang", "")
                rev_overhang = params.get("rev_overhang", "")
                drop_stop_codon = params.get("drop_stop_codon", False)
                
                res = design_pcr_primers(
                    seq, 
                    prod_size_min=prod_min, 
                    prod_size_max=prod_max,
                    tm_opt=tm_opt,
                    tm_min=tm_min,
                    tm_max=tm_max,
                    fwd_enzyme=fwd_enzyme,
                    fwd_enzyme_seq=fwd_enzyme_seq,
                    rev_enzyme=rev_enzyme,
                    rev_enzyme_seq=rev_enzyme_seq,
                    fwd_overhang=fwd_overhang,
                    rev_overhang=rev_overhang,
                    drop_stop_codon=drop_stop_codon
                )
                
                if not res:
                    status_box.update(label="Gagal merancang primer", state="complete")
                    reply = f"{reply}\n\n*Tidak ada pasangan primer yang memenuhi syarat desain.*"
                    message_placeholder.markdown(reply)
                else:
                    st.session_state.last_primer_data = res
                    st.session_state.last_primer_seq = seq
                    st.session_state.last_primer_params = params
                    st.session_state.last_action_type = "primer"
                    
                    # Construct markdown list of primers
                    p_md = f"{reply}\n\n**Daftar Pasangan Primer Potensial:**\n\n"
                    table_rows = []
                    for idx, p in enumerate(res):
                        p_md += f"**Primer #{p['rank']} (Ukuran Produk: {p['product_size']} bp)**\n"
                        if p.get('cloning_mode'):
                            p_md += f"- **Forward Primer**: `{p['forward']['sequence']}` (Tm-bind: {p['forward']['tm_bind']}°C, GC: {p['forward']['gc']}%, Panjang: {p['forward']['length']} bp)\n"
                            p_md += f"- **Reverse Primer**: `{p['reverse']['sequence']}` (Tm-bind: {p['reverse']['tm_bind']}°C, GC: {p['reverse']['gc']}%, Panjang: {p['reverse']['length']} bp)\n"
                        else:
                            p_md += f"- **Forward Primer**: `{p['forward']['sequence']}` (Tm: {p['forward']['tm']}°C, GC: {p['forward']['gc']}%)\n"
                            p_md += f"- **Reverse Primer**: `{p['reverse']['sequence']}` (Tm: {p['reverse']['tm']}°C, GC: {p['reverse']['gc']}%)\n"
                        
                        table_rows.append({
                            "Rank": p['rank'],
                            "Product Size": p['product_size'],
                            "Fwd Sequence": p['forward']['sequence'],
                            "Fwd Tm": p['forward'].get('tm', p['forward'].get('tm_bind')),
                            "Rev Sequence": p['reverse']['sequence'],
                            "Rev Tm": p['reverse'].get('tm', p['reverse'].get('tm_bind'))
                        })
                    
                    message_placeholder.markdown(p_md)
                    msg_df = pd.DataFrame(table_rows)
                    
                    # Generate PDF report
                    status_box.update(label="Merender laporan PDF Primer...", state="running")
                    from biopygeon.engines.report_generator import save_primer_pdf_report
                    pdf_path = save_primer_pdf_report(
                        res, 
                        os.getcwd(), 
                        sequence=seq, 
                        params_used=params, 
                        progress_callback=lambda m, a=0: None
                    )
                    
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as pf:
                            p_data = pf.read()
                        msg_downloads.append({
                            "label": "Unduh Laporan Primer PDF",
                        "icon": ":material/description:",
                            "data": p_data,
                            "file_name": "Laporan_Desain_Primer.pdf",
                            "mime": "application/pdf"
                        })
                    status_box.update(label="Desain primer selesai!", state="complete")
                    
            # 15. HARMONIZE DATA (ALS/Missing Value)
            elif action == "harmonize_data":
                status_box.update(label="Mengharmonisasi data...", state="running")
                from biopygeon.engines.q1_pipeline import harmonize_data
                in_csv = params.get("input_csv")
                out_csv = params.get("output_csv", "harmonized_data.csv")
                strategy = params.get("strategy", "mean")
                base_method = params.get("baseline_method", "als")
                
                res_msg = harmonize_data(in_csv, out_csv, strategy=strategy, baseline_method=base_method)
                reply = f"{reply}\n\n**{res_msg}**"
                message_placeholder.markdown(reply)
                
                if os.path.exists(out_csv):
                    df_clean = pd.read_csv(out_csv)
                    msg_df = df_clean.head(20)
                    
                    csv_data = df_clean.to_csv(index=False).encode('utf-8')
                    msg_downloads.append({
                        "label": "Unduh CSV Bersih",
                        "icon": ":material/bar_chart:",
                        "data": csv_data,
                        "file_name": os.path.basename(out_csv),
                        "mime": "text/csv"
                    })
                status_box.update(label="Harmonisasi selesai!", state="complete")
                
            # 16. RENDER SSN NETWORK
            elif action == "render_network":
                status_box.update(label="Membuat visualisasi Jaringan (SSN)...", state="running")
                from biopygeon.engines.q1_pipeline import render_network
                in_csv = params.get("input_csv")
                out_tiff = params.get("output_tiff", "network.tiff")
                out_html = params.get("output_html", "network.html")
                src_col = params.get("source_col")
                tgt_col = params.get("target_col")
                nodes_csv = params.get("nodes_csv")
                
                res_msg = render_network(in_csv, out_tiff, out_html, src_col, tgt_col, nodes_csv=nodes_csv)
                
                if os.path.exists(out_html):
                    with open(out_html, "r", encoding="utf-8") as f:
                        msg_html = f.read()
                    
                    msg_downloads.append({
                        "label": "Unduh Peta Jaringan HTML",
                        "icon": ":material/language:",
                        "data": msg_html,
                        "file_name": os.path.basename(out_html),
                        "mime": "text/html"
                    })
                    
                if os.path.exists(out_tiff):
                    png_path = os.path.join(os.getcwd(), "network.png")
                    try:
                        with Image.open(out_tiff) as img:
                            img.save(png_path, "PNG")
                        msg_img = png_path
                    except:
                        pass
                        
                    with open(out_tiff, "rb") as f:
                        t_data = f.read()
                    msg_downloads.append({
                        "label": "Unduh Jaringan TIFF (300 DPI)",
                        "icon": ":material/image:",
                        "data": t_data,
                        "file_name": os.path.basename(out_tiff),
                        "mime": "image/tiff"
                    })
                    
                status_box.update(label="Render jaringan selesai!", state="complete")
                
            # 17. STATISTICAL PLOT Q1 FIGURE
            elif action == "plot_q1_figure":
                status_box.update(label="Membuat plot statistik...", state="running")
                from biopygeon.engines.q1_pipeline import plot_q1_figure
                in_csv = params.get("input_csv")
                out_html = params.get("output_html", "q1_plot.html")
                ptype = params.get("plot_type")
                x_col = params.get("x_col")
                y_col = params.get("y_col")
                
                res_msg = plot_q1_figure(in_csv, out_html, ptype, x_col, y_col)
                reply = f"{reply}\n\n**{res_msg}**"
                message_placeholder.markdown(reply)
                
                if os.path.exists(out_html):
                    with open(out_html, "r", encoding="utf-8") as f:
                        msg_html = f.read()
                    msg_downloads.append({
                        "label": "Unduh Plot HTML",
                        "icon": ":material/language:",
                        "data": msg_html,
                        "file_name": os.path.basename(out_html),
                        "mime": "text/html"
                    })
                status_box.update(label="Plot statistik siap!", state="complete")
                
            # 18. GENERATE METHODOLOGY DRAFT
            elif action == "generate_methodology":
                status_box.update(label="Menulis draf metodologi...", state="running")
                from biopygeon.engines.q1_pipeline import generate_methodology
                output_txt = params.get("output_txt", "methodology.txt")
                baseline_method = params.get("baseline_method", "als")
                plot_type = params.get("plot_type", "boxplot")
                journal = params.get("journal", "nature")
                
                res_msg = generate_methodology(output_txt, baseline_method, plot_type, journal)
                if os.path.exists(output_txt):
                    with open(output_txt, "r", encoding="utf-8") as f:
                        m_txt = f.read()
                    message_placeholder.markdown(f"{reply}\n\n**Draf Metodologi Penelitian:**\n\n```\n{m_txt}\n```")
                    
                    msg_downloads.append({
                        "label": "Unduh Draf Metodologi TXT",
                        "icon": ":material/subject:",
                        "data": m_txt,
                        "file_name": os.path.basename(output_txt),
                        "mime": "text/plain"
                    })
                status_box.update(label="Metodologi berhasil disusun!", state="complete")
                
            # 19. NATIVE WORD MANUSCRIPT FORMATTING
            elif action == "format_manuscript":
                status_box.update(label="Membuka MS Word via COM Automation...", state="running")
                from biopygeon.engines.formatter import format_manuscript_engine
                draft_docx = params.get("draft_docx")
                template_docx = params.get("template_docx")
                output_docx = params.get("output_docx", "formatted_manuscript.docx")
                
                res_msg = format_manuscript_engine(draft_docx, template_docx, output_docx)
                reply = f"{reply}\n\n**{res_msg}**"
                message_placeholder.markdown(reply)
                
                if os.path.exists(output_docx):
                    with open(output_docx, "rb") as f:
                        d_data = f.read()
                    msg_downloads.append({
                        "label": "Unduh Dokumen Terformat (DOCX)",
                        "icon": ":material/save:",
                        "data": d_data,
                        "file_name": os.path.basename(output_docx),
                        "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    })
                status_box.update(label="Sinkronisasi format naskah selesai!", state="complete")
                
            # 20. OMICS HEATMAP EXPRESSION
            elif action == "plot_heatmap":
                status_box.update(label="Membuat Heatmap ekspresi genetik...", state="running")
                from biopygeon.engines.omics import plot_heatmap
                in_csv = params.get("input_csv")
                out_html = params.get("output_html", "heatmap.html")
                
                res_msg = plot_heatmap(in_csv, out_html)
                reply = f"{reply}\n\n**{res_msg}**"
                message_placeholder.markdown(reply)
                
                if os.path.exists(out_html):
                    with open(out_html, "r", encoding="utf-8") as f:
                        msg_html = f.read()
                    msg_downloads.append({
                        "label": "Unduh Heatmap HTML",
                        "icon": ":material/language:",
                        "data": msg_html,
                        "file_name": os.path.basename(out_html),
                        "mime": "text/html"
                    })
                status_box.update(label="Heatmap siap!", state="complete")
                
            # 21. OMICS ENRICHMENT SCATTER
            elif action == "plot_enrichment":
                status_box.update(label="Membuat plot pengayaan...", state="running")
                from biopygeon.engines.omics import plot_enrichment
                in_csv = params.get("input_csv")
                out_html = params.get("output_html", "enrichment.html")
                
                res_msg = plot_enrichment(in_csv, out_html)
                reply = f"{reply}\n\n**{res_msg}**"
                message_placeholder.markdown(reply)
                
                if os.path.exists(out_html):
                    with open(out_html, "r", encoding="utf-8") as f:
                        msg_html = f.read()
                    msg_downloads.append({
                        "label": "Unduh Plot Pengayaan HTML",
                        "icon": ":material/language:",
                        "data": msg_html,
                        "file_name": os.path.basename(out_html),
                        "mime": "text/html"
                    })
                status_box.update(label="Plot pengayaan siap!", state="complete")
                
            # 22. OMICS VOLCANO SCATTER
            elif action == "plot_volcano":
                status_box.update(label="Membuat Volcano Plot...", state="running")
                from biopygeon.engines.omics import plot_volcano
                in_csv = params.get("input_csv")
                out_html = params.get("output_html", "volcano.html")
                pval_col = params.get("pvalue_col")
                fc_col = params.get("fc_col")
                pval_th = params.get("pval_threshold", 0.05)
                fc_th = params.get("log2fc_threshold", 1.0)
                gene_col = params.get("gene_col")
                
                res_msg = plot_volcano(
                    in_csv, 
                    out_html, 
                    pval_col, 
                    fc_col, 
                    pval_th, 
                    fc_th, 
                    gene_col
                )
                reply = f"{reply}\n\n**{res_msg}**"
                message_placeholder.markdown(reply)
                
                if os.path.exists(out_html):
                    with open(out_html, "r", encoding="utf-8") as f:
                        msg_html = f.read()
                    msg_downloads.append({
                        "label": "Unduh Volcano Plot HTML",
                        "icon": ":material/language:",
                        "data": msg_html,
                        "file_name": os.path.basename(out_html),
                        "mime": "text/html"
                    })
                status_box.update(label="Volcano Plot siap!", state="complete")
                
            # 23. ALPHAFOLD STRUCTURE
            elif action == "fetch_alphafold_structure":
                status_box.update(label="Mengunduh model AlphaFold...", state="running")
                from biopygeon.engines.biology import fetch_alphafold_structure
                uid = params.get("uniprot_id")
                try:
                    res_files = fetch_alphafold_structure(uid, progress_callback=lambda p: status_box.update(label=p, state="running"))
                    reply = f"{reply}\n\n**Struktur AlphaFold siap divisualisasikan.**"
                    with open(res_files[0], "rb") as f:
                        pdb_data = f.read()
                    msg_downloads.append({
                        "label": f"Unduh AF-{uid}.pdb",
                        "data": pdb_data,
                        "file_name": os.path.basename(res_files[0]),
                        "mime": "chemical/x-pdb"
                    })
                    msg_pdb = res_files[0]
                    status_box.update(label="Model AlphaFold siap!", state="complete")
                except Exception as e:
                    reply = f"{reply}\n\n**Galat:** {e}"
                    status_box.update(label="Gagal mengunduh AlphaFold", state="error")
                    
            # 24. RENDER 3D STRUCTURE
            elif action == "render_3d_structure":
                status_box.update(label="Menyiapkan Viewer 3D Interaktif...", state="running")
                pdb_path = params.get("pdb_path")
                if pdb_path and os.path.exists(pdb_path):
                    msg_pdb = pdb_path
                    reply = f"{reply}\n\n*Menampilkan struktur 3D dari {pdb_path}*"
                    status_box.update(label="Visualisasi 3D berhasil", state="complete")
                else:
                    reply = f"{reply}\n\n**Galat:** File PDB tidak ditemukan di path: `{pdb_path}`"
                    status_box.update(label="File PDB tidak ditemukan", state="error")
                
            else:
                status_box.update(label="Perintah tidak dikenali", state="error")
                st.warning(f"Aksi AI '{action}' belum didukung oleh antarmuka Web UI ini.")
                
        except Exception as e:
            status_box.update(label="Eksekusi Terhenti (Error)", state="error")
            tb = traceback.format_exc()
            st.error(f"Terjadi kesalahan saat mengeksekusi modul:\n`{e}`")
            with st.expander("Detail Stacktrace"):
                st.code(tb)
            # Store fallback reply
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Terjadi kegagalan pemrosesan:\n`{e}`"
            })
            st.stop()

        # Build final message dict to save to history
        new_assistant_message = {
            "role": "assistant",
            "content": reply,
            "dataframe": msg_df,
            "html_content": msg_html,
            "image_path": msg_img,
            "pdb_content": msg_pdb,
            "download_buttons": msg_downloads
        }
        
        # Save to chat history
        st.session_state.messages.append(new_assistant_message)
        save_current_chat(st.session_state.messages, st.session_state.current_session_id)
        
        # Force a rerun to show download buttons and tables neatly in historical order
        st.rerun()
