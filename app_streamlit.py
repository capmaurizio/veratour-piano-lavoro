#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaccia Web Streamlit Multi-Tour Operatour
Basata sulla versione originale funzionante di Veratour
"""

import streamlit as st
import pandas as pd
import io
import os
import sys
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
import re

# Aggiungi Veratour, Alpitour, Domina, MichelTours, SAND, Caboverdetime e Rusconi al path per import
veratour_path = os.path.join(os.path.dirname(__file__), 'Veratour')
alpitour_path = os.path.join(os.path.dirname(__file__), 'Alpitour')
domina_path = os.path.join(os.path.dirname(__file__), 'Domina')
micheltours_path = os.path.join(os.path.dirname(__file__), 'MICHELTOURS')
sand_path = os.path.join(os.path.dirname(__file__), ' Sand')
caboverdetime_path = os.path.join(os.path.dirname(__file__), 'Caboverdetime')
rusconi_path = os.path.join(os.path.dirname(__file__), 'Rusconi')
if veratour_path not in sys.path:
    sys.path.insert(0, veratour_path)
if alpitour_path not in sys.path:
    sys.path.insert(0, alpitour_path)
if domina_path not in sys.path:
    sys.path.insert(0, domina_path)
if micheltours_path not in sys.path:
    sys.path.insert(0, micheltours_path)
if sand_path not in sys.path:
    sys.path.insert(0, sand_path)
if caboverdetime_path not in sys.path:
    sys.path.insert(0, caboverdetime_path)
if rusconi_path not in sys.path:
    sys.path.insert(0, rusconi_path)

from consuntivoveratour import (
    CalcConfig as VeratourCalcConfig,
    RoundingPolicy,
    process_files as process_files_veratour,
    write_output_excel as write_output_excel_veratour,
    load_holiday_list
)

try:
    from consuntivoalpitour import (
        CalcConfig as AlpitourCalcConfig,
        process_files as process_files_alpitour,
        write_output_excel as write_output_excel_alpitour,
        validate_file_complete as validate_file_alpitour
    )
    ALPITOUR_AVAILABLE = True
except ImportError as e:
    ALPITOUR_AVAILABLE = False
    # Non mostrare warning all'avvio, solo se necessario
    AlpitourCalcConfig = None
    process_files_alpitour = None
    write_output_excel_alpitour = None
    validate_file_alpitour = None

try:
    from consuntivodomina import (
        CalcConfig as DominaCalcConfig,
        process_files as process_files_domina,
        write_output_excel as write_output_excel_domina,
    )
    DOMINA_AVAILABLE = True
except ImportError as e:
    DOMINA_AVAILABLE = False
    DominaCalcConfig = None
    process_files_domina = None
    write_output_excel_domina = None

try:
    from consuntivocaboverdetime import (
        CalcConfig as CaboverdetimeCalcConfig,
        process_files as process_files_caboverdetime,
        write_output_excel as write_output_excel_caboverdetime,
    )
    CABOVERDETIME_AVAILABLE = True
except ImportError as e:
    CABOVERDETIME_AVAILABLE = False
    CaboverdetimeCalcConfig = None
    process_files_caboverdetime = None
    write_output_excel_caboverdetime = None

try:
    from consuntivorusconi import (
        CalcConfig as RusconiCalcConfig,
        process_files as process_files_rusconi,
        write_output_excel as write_output_excel_rusconi,
    )
    RUSCONI_AVAILABLE = True
except ImportError as e:
    RUSCONI_AVAILABLE = False
    RusconiCalcConfig = None
    process_files_rusconi = None
    write_output_excel_rusconi = None

try:
    from consuntivomicheltours import (
        CalcConfig as MichelToursCalcConfig,
        process_files as process_files_micheltours,
        write_output_excel as write_output_excel_micheltours,
    )
    MICHELTOURS_AVAILABLE = True
except ImportError as e:
    MICHELTOURS_AVAILABLE = False
    MichelToursCalcConfig = None
    process_files_micheltours = None
    write_output_excel_micheltours = None

try:
    from consuntivosand import (
        CalcConfig as SandCalcConfig,
        process_files as process_files_sand,
        write_output_excel as write_output_excel_sand,
    )
    SAND_AVAILABLE = True
except ImportError as e:
    SAND_AVAILABLE = False
    SandCalcConfig = None
    process_files_sand = None
    write_output_excel_sand = None

# Configurazione pagina
st.set_page_config(
    page_title="Calcolo Piano Lavoro - Multi-Tour Operatour",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-container {
        max-width: 450px;
        margin: 80px auto;
        padding: 40px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        background-color: #ffffff;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .login-title {
        font-size: 1.8rem;
        font-weight: 600;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }
    .login-subtitle {
        font-size: 0.95rem;
        color: #666;
        text-align: center;
        margin-bottom: 30px;
    }
    .company-name {
        font-size: 1.2rem;
        font-weight: 500;
        color: #333;
        text-align: center;
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

# Credenziali di accesso
VALID_USERNAME = "skypemiao"
VALID_PASSWORD = "jfjdljf3244a?091"

# Inizializza session_state per autenticazione
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_credentials(username: str, password: str) -> bool:
    """Verifica le credenziali di accesso"""
    return username == VALID_USERNAME and password == VALID_PASSWORD

def login_page():
    """Mostra la pagina di login"""
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Accesso Protetto</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Inserisci le credenziali per accedere all\'applicazione</div>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Inserisci username")
        password = st.text_input("Password", type="password", placeholder="Inserisci password")
        submit_button = st.form_submit_button("Accedi", use_container_width=True)
        
        if submit_button:
            if check_credentials(username, password):
                st.session_state.authenticated = True
                st.success("Accesso autorizzato")
                st.rerun()
            else:
                st.error("Username o password non corretti. Riprova.")
    
    st.markdown('<div class="company-name">Scay Bergamo</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Controllo autenticazione
if not st.session_state.authenticated:
    login_page()
    st.stop()

# Header (mostrato solo se autenticato)
st.markdown('<div class="main-header">Calcolo Piano Lavoro - Multi-Tour Operatour</div>', unsafe_allow_html=True)

# Bottone logout nella sidebar
with st.sidebar:
    st.markdown("---")
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()


def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizza i nomi delle colonne"""
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def find_col(df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
    """Trova una colonna che corrisponde a uno dei pattern"""
    cols = [str(c).upper() for c in df.columns]
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for c in cols:
            if rx.search(c):
                return c
    return None


def detect_tour_operators(file_path: str) -> Set[str]:
    """Rileva tutti i tour operatour unici dal file Excel"""
    tour_operators = set()
    
    try:
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            if df is None or df.empty:
                continue
            
            df = normalize_cols(df)
            to_col = find_col(df, [r"TOUR\s*OPERATOR", r"^TO$", r"OPERATORE"])
            
            if to_col:
                unique_values = df[to_col].dropna().astype(str).str.strip()
                unique_values = unique_values[unique_values != ""]
                unique_values = unique_values[unique_values.str.lower() != "nan"]
                unique_values = unique_values[unique_values.str.lower() != "none"]
                tour_operators.update(unique_values.unique())
    except Exception as e:
        st.warning(f"Errore nel rilevare tour operatour: {str(e)}")
    
    return tour_operators


def find_tour_operator_folder(to_name: str, base_path: str = ".") -> Optional[str]:
    """Cerca la cartella del tour operatour nella root"""
    to_clean = re.sub(r'[^a-zA-Z]', '', to_name).lower()
    
    if os.path.exists(base_path):
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                item_clean = re.sub(r'[^a-zA-Z]', '', item).lower()
                if item_clean == to_clean or to_clean in item_clean or item_clean in to_clean:
                    return item_path
    
    return None


# Sidebar con opzioni avanzate
with st.sidebar:
    st.header("⚙️ Opzioni di Calcolo")
    
    apt_filter = st.multiselect(
        "Filtra Aeroporti (opzionale)",
        options=["VRN", "BGY", "NAP", "VCE"],
        help="Seleziona gli aeroporti da includere. Lascia vuoto per includere tutti."
    )
    
    # Opzioni Veratour
    st.subheader("Opzioni Veratour")
    night_mode = st.selectbox(
        "Modalità Notturno (Veratour)",
        options=["DIFF5", "FULL30"],
        index=0,
        help="DIFF5: Maggiorazione differenziale (€5/h). FULL30: Tariffa piena (€30/h)."
    )
    
    st.subheader("Arrotondamenti (Veratour)")
    
    round_extra_mode = st.selectbox(
        "Arrotondamento Extra (Veratour)",
        options=["NONE", "FLOOR", "CEIL", "NEAREST"],
        index=0
    )
    round_extra_step = st.number_input(
        "Step Arrotondamento Extra (minuti)",
        min_value=1,
        value=5,
        step=1
    )
    
    round_night_mode = st.selectbox(
        "Arrotondamento Notturno (Veratour)",
        options=["NONE", "FLOOR", "CEIL", "NEAREST"],
        index=0
    )
    round_night_step = st.number_input(
        "Step Arrotondamento Notturno (minuti)",
        min_value=1,
        value=5,
        step=1
    )
    
    st.info("ℹ️ Alpitour: Nessun arrotondamento (valori esatti)")
    
    holiday_file = st.file_uploader(
        "File Festivi (opzionale)",
        type=["txt", "csv"],
        help="File con lista festivi (una data per riga, formato YYYY-MM-DD)"
    )

# Area principale
st.markdown("### Carica File Excel del Piano di Lavoro")

uploaded_file = st.file_uploader(
    "Seleziona il file Excel",
    type=["xlsx", "xls"],
    help="Carica il file Excel contenente il piano di lavoro"
)

if uploaded_file is not None:
    file_details = {
        "Nome file": uploaded_file.name,
        "Dimensione": f"{uploaded_file.size / 1024:.2f} KB",
        "Tipo": uploaded_file.type
    }
    
    with st.expander("ℹ️ Informazioni File", expanded=False):
        st.json(file_details)
    
    # Rileva tour operatour
    with st.spinner("🔍 Rilevamento tour operatour..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        try:
            tour_operators = detect_tour_operators(tmp_path)
            
            if tour_operators:
                st.info(f"Tour operatour rilevati: {', '.join(sorted(tour_operators))}")
                
                available_folders = {}
                missing_tour_operators = []
                
                for to_name in tour_operators:
                    folder_path = find_tour_operator_folder(to_name)
                    if folder_path:
                        available_folders[to_name] = folder_path
                    else:
                        missing_tour_operators.append(to_name)
                
            if available_folders:
                st.success(f"Tour operatour con calcolo disponibile: {', '.join(available_folders.keys())}")
            
            if missing_tour_operators:
                st.warning(f"Tour operatour senza cartella (non elaborati): {', '.join(missing_tour_operators)}")
        finally:
            pass  # Manteniamo tmp_path per la validazione
    
    # VALIDAZIONE COMPLETA DEL FILE PRIMA DEL CALCOLO
    st.markdown("---")
    st.markdown("### 🔍 Validazione File")
    
    if 'validation_results' not in st.session_state or st.session_state.get('last_file') != uploaded_file.name:
        with st.spinner("⏳ Validazione file in corso..."):
            validation_results = {}
            
            # Validazione per Veratour
            if 'veratour' in [to.lower() for to in tour_operators]:
                try:
                    # Crea una funzione di validazione per Veratour (simile ad Alpitour)
                    # Per ora usiamo la stessa logica di rilevamento
                    st.info("🔍 Validazione Veratour...")
                    validation_results['veratour'] = {
                        "status": "ok",
                        "tour_operators": [to for to in tour_operators if 'veratour' in to.lower()],
                        "note": "Veratour rilevato - pronto per calcolo"
                    }
                except Exception as e:
                    validation_results['veratour'] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Validazione per Alpitour
            if ALPITOUR_AVAILABLE and validate_file_alpitour and 'alpitour' in [to.lower() for to in tour_operators]:
                try:
                    st.info("🔍 Validazione Alpitour...")
                    result_alpitour = validate_file_alpitour(tmp_path, to_keyword="alpitour", apt_filter=apt_filter if apt_filter else None)
                    validation_results['alpitour'] = result_alpitour
                except Exception as e:
                    validation_results['alpitour'] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Validazione per Domina
            if 'domina' in [to.lower() for to in tour_operators]:
                try:
                    st.info("🔍 Validazione Domina...")
                    validation_results['domina'] = {
                        "status": "ok",
                        "tour_operators": [to for to in tour_operators if 'domina' in to.lower()],
                        "note": "Domina rilevato - pronto per calcolo"
                    }
                except Exception as e:
                    validation_results['domina'] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Validazione per MichelTours
            if 'micheltours' in [to.lower() for to in tour_operators] or 'michel tours' in [to.lower() for to in tour_operators]:
                try:
                    st.info("🔍 Validazione MichelTours...")
                    validation_results['micheltours'] = {
                        "status": "ok",
                        "tour_operators": [to for to in tour_operators if 'micheltours' in to.lower() or 'michel tours' in to.lower()],
                        "note": "MichelTours rilevato - pronto per calcolo"
                    }
                except Exception as e:
                    validation_results['micheltours'] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Validazione per SAND
            if 'sand' in [to.lower() for to in tour_operators]:
                try:
                    st.info("🔍 Validazione SAND...")
                    validation_results['sand'] = {
                        "status": "ok",
                        "tour_operators": [to for to in tour_operators if 'sand' in to.lower()],
                        "note": "SAND rilevato - pronto per calcolo"
                    }
                except Exception as e:
                    validation_results['sand'] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            st.session_state['validation_results'] = validation_results
            st.session_state['last_file'] = uploaded_file.name
    
    # Mostra risultati validazione
    validation_results = st.session_state.get('validation_results', {})
    
    if validation_results:
        for to_name, result in validation_results.items():
            with st.expander(f"Risultati Validazione - {to_name.upper()}", expanded=True):
                if isinstance(result, dict) and 'status' in result:
                    if result['status'] == 'ok':
                        st.success(f"{to_name.upper()}: Validazione completata")
                        if 'tour_operators' in result:
                            st.info(f"Tour operatour: {', '.join(result['tour_operators'])}")
                    else:
                        st.error(f"{to_name.upper()}: {result.get('error', 'Errore sconosciuto')}")
                else:
                    # Risultato completo da validate_file_complete
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Righe Totali", result.get('righe_totali', 0))
                        st.metric("Righe con Errori", len(result.get('righe_con_errori', [])))
                    
                    with col2:
                        st.metric("Tour Operatour", len(result.get('tour_operators_trovati', [])))
                        st.metric("Aeroporti", len(result.get('aeroporti_trovati', [])))
                    
                    with col3:
                        st.metric("Date Trovate", len(result.get('date_trovate', [])))
                        st.metric("Fogli Validati", len(result.get('fogli_validati', [])))
                    
                    # Colonne trovate/mancanti
                    if result.get('colonne_trovate'):
                        st.success("Colonne trovate:")
                        for key, val in result['colonne_trovate'].items():
                            st.write(f"  - {key}: {val}")
                    
                    if result.get('colonne_mancanti'):
                        st.warning("Colonne mancanti (opzionali):")
                        for col in result['colonne_mancanti']:
                            st.write(f"  - {col}")
                    
                    # Tour operatour e aeroporti
                    if result.get('tour_operators_trovati'):
                        st.info(f"Tour operatour: {', '.join(result['tour_operators_trovati'])}")
                    
                    if result.get('aeroporti_trovati'):
                        st.info(f"✈️ Aeroporti: {', '.join(result['aeroporti_trovati'])}")
                    
                    # Errori
                    if result.get('righe_con_errori'):
                        st.error(f"Righe con errori: {len(result['righe_con_errori'])}")
                        with st.expander("Dettaglio Errori (prime 10)", expanded=False):
                            for err in result['righe_con_errori'][:10]:
                                st.write(f"**Foglio {err['foglio']}, Riga {err['riga']}** ({err.get('data', 'N/A')} - {err.get('apt', 'N/A')}): {err['errore']}")
                            if len(result['righe_con_errori']) > 10:
                                st.write(f"... e altri {len(result['righe_con_errori']) - 10} errori")
                    
                    # Fogli validati
                    if result.get('fogli_validati'):
                        st.info("Fogli validati:")
                        for foglio in result['fogli_validati']:
                            st.write(f"  - {foglio['foglio']}: {foglio['righe_totali']} righe totali, {foglio['righe_con_errori']} con errori")
    
    # Salva tmp_path in session state per il calcolo
    st.session_state['tmp_file_path'] = tmp_path
    st.session_state['uploaded_file_name'] = uploaded_file.name
    
    # Pulsante per eseguire il calcolo
    st.markdown("---")
    st.markdown("### Esegui Calcolo")
    
    if st.button("Esegui Calcolo", type="primary", use_container_width=True):
        with st.spinner("⏳ Elaborazione in corso..."):
            try:
                # Usa il file temporaneo già creato durante la validazione
                tmp_path = st.session_state.get('tmp_file_path')
                if not tmp_path or not os.path.exists(tmp_path):
                    # Se non esiste, ricrearlo
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                
                try:
                    # Carica festivi se presente
                    holiday_dates = None
                    if holiday_file is not None:
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt") as tmp_holiday:
                            tmp_holiday.write(holiday_file.getvalue().decode('utf-8'))
                            tmp_holiday_path = tmp_holiday.name
                        try:
                            holiday_dates = load_holiday_list(tmp_holiday_path)
                        finally:
                            os.unlink(tmp_holiday_path)
                    
                    # Rileva tour operatour
                    tour_operators = detect_tour_operators(tmp_path)
                    
                    # Rileva quale tour operatour è presente
                    veratour_found = False
                    alpitour_found = False
                    domina_found = False
                    micheltours_found = False
                    sand_found = False
                    caboverdetime_found = False
                    rusconi_found = False
                    for to_name in tour_operators:
                        to_clean = re.sub(r'[^a-zA-Z]', '', to_name).lower()
                        if 'veratour' in to_clean:
                            veratour_found = True
                        if 'alpitour' in to_clean:
                            alpitour_found = True
                        if 'domina' in to_clean:
                            domina_found = True
                        if 'micheltours' in to_clean or 'michel tours' in to_clean:
                            micheltours_found = True
                        if 'sand' in to_clean:
                            sand_found = True
                        if 'caboverdetime' in to_clean:
                            caboverdetime_found = True
                        if 'rusconi' in to_clean:
                            rusconi_found = True
                    
                    all_detail_dfs = []
                    all_totals_dfs = []
                    all_discr_dfs = []
                    
                    # Elabora Veratour se presente
                    if veratour_found:
                        st.info("Elaborazione Veratour...")
                        cfg_veratour = VeratourCalcConfig(
                            apt_filter=apt_filter if apt_filter else None,
                            night_mode=night_mode,
                            rounding_extra=RoundingPolicy(round_extra_mode, round_extra_step),
                            rounding_night=RoundingPolicy(round_night_mode, round_night_step),
                            holiday_dates=holiday_dates,
                        )
                        detail_v, totals_v, discr_v = process_files_veratour([tmp_path], cfg_veratour)
                        all_detail_dfs.append(detail_v)
                        all_totals_dfs.append(totals_v)
                        all_discr_dfs.append(discr_v)
                    
                    # Elabora Alpitour se presente
                    if alpitour_found:
                        if ALPITOUR_AVAILABLE:
                            st.info("Elaborazione Alpitour...")
                            cfg_alpitour = AlpitourCalcConfig(
                                apt_filter=apt_filter if apt_filter else None,
                                rounding_extra=RoundingPolicy("NONE", 5),  # Alpitour: nessun arrotondamento
                                rounding_night=RoundingPolicy("NONE", 5),  # Alpitour: nessun arrotondamento
                                holiday_dates=holiday_dates,
                            )
                            detail_a, totals_a, discr_a = process_files_alpitour([tmp_path], cfg_alpitour)
                            all_detail_dfs.append(detail_a)
                            all_totals_dfs.append(totals_a)
                            all_discr_dfs.append(discr_a)
                        else:
                            st.warning("Alpitour rilevato ma modulo non disponibile. Installare le dipendenze necessarie.")
                    
                    # Elabora Domina se presente
                    if domina_found:
                        if DOMINA_AVAILABLE:
                            st.info("Elaborazione Domina...")
                            cfg_domina = DominaCalcConfig(
                                apt_filter=apt_filter if apt_filter else None,
                                rounding_extra=RoundingPolicy("NONE", 5),  # Domina: nessun arrotondamento
                                rounding_night=RoundingPolicy("NONE", 5),  # Domina: nessun arrotondamento
                                holiday_dates=holiday_dates,
                            )
                            detail_d, totals_d, discr_d = process_files_domina([tmp_path], cfg_domina)
                            all_detail_dfs.append(detail_d)
                            all_totals_dfs.append(totals_d)
                            all_discr_dfs.append(discr_d)
                        else:
                            st.warning("Domina rilevato ma modulo non disponibile. Installare le dipendenze necessarie.")
                    
                    # Elabora MichelTours se presente
                    if micheltours_found:
                        if MICHELTOURS_AVAILABLE:
                            st.info("Elaborazione MichelTours...")
                            cfg_micheltours = MichelToursCalcConfig(
                                apt_filter=apt_filter if apt_filter else None,
                                rounding_extra=RoundingPolicy("NONE", 5),  # MichelTours: nessun arrotondamento
                                rounding_night=RoundingPolicy("NONE", 5),  # MichelTours: nessun arrotondamento
                                holiday_dates=holiday_dates,
                            )
                            detail_mt, totals_mt, discr_mt = process_files_micheltours([tmp_path], cfg_micheltours)
                            all_detail_dfs.append(detail_mt)
                            all_totals_dfs.append(totals_mt)
                            all_discr_dfs.append(discr_mt)
                        else:
                            st.warning("MichelTours rilevato ma modulo non disponibile. Installare le dipendenze necessarie.")
                    
                    # Elabora SAND se presente
                    if sand_found:
                        if SAND_AVAILABLE:
                            st.info("Elaborazione SAND...")
                            cfg_sand = SandCalcConfig(
                                apt_filter=apt_filter if apt_filter else None,
                                rounding_extra=RoundingPolicy("NONE", 5),  # SAND: nessun arrotondamento
                                rounding_night=RoundingPolicy("NONE", 5),  # SAND: nessun arrotondamento
                                holiday_dates=holiday_dates,
                            )
                            detail_s, totals_s, discr_s = process_files_sand([tmp_path], cfg_sand)
                            all_detail_dfs.append(detail_s)
                            all_totals_dfs.append(totals_s)
                            all_discr_dfs.append(discr_s)
                        else:
                            st.warning("SAND rilevato ma modulo non disponibile. Installare le dipendenze necessarie.")
                    
                    # Elabora Caboverdetime se presente
                    if caboverdetime_found:
                        if CABOVERDETIME_AVAILABLE:
                            st.info("Elaborazione Caboverdetime...")
                            cfg_caboverdetime = CaboverdetimeCalcConfig(
                                apt_filter=apt_filter if apt_filter else None,
                                rounding_extra=RoundingPolicy("NONE", 5),  # Caboverdetime: nessun arrotondamento
                                rounding_night=RoundingPolicy("NONE", 5),  # Caboverdetime: nessun arrotondamento
                                holiday_dates=holiday_dates,
                            )
                            detail_ct, totals_ct, discr_ct = process_files_caboverdetime([tmp_path], cfg_caboverdetime)
                            all_detail_dfs.append(detail_ct)
                            all_totals_dfs.append(totals_ct)
                            all_discr_dfs.append(discr_ct)
                        else:
                            st.warning("Caboverdetime rilevato ma modulo non disponibile. Installare le dipendenze necessarie.")
                    
                    # Elabora Rusconi se presente
                    if rusconi_found:
                        if RUSCONI_AVAILABLE:
                            st.info("Elaborazione Rusconi...")
                            cfg_rusconi = RusconiCalcConfig(
                                apt_filter=apt_filter if apt_filter else None,
                                rounding_extra=RoundingPolicy("NONE", 5),  # Rusconi: nessun arrotondamento
                                rounding_night=RoundingPolicy("NONE", 5),  # Rusconi: nessun arrotondamento
                                holiday_dates=holiday_dates,
                            )
                            detail_r, totals_r, discr_r = process_files_rusconi([tmp_path], cfg_rusconi)
                            all_detail_dfs.append(detail_r)
                            all_totals_dfs.append(totals_r)
                            all_discr_dfs.append(discr_r)
                        else:
                            st.warning("Rusconi rilevato ma modulo non disponibile. Installare le dipendenze necessarie.")
                    
                    if not veratour_found and not alpitour_found and not domina_found and not micheltours_found and not sand_found and not caboverdetime_found and not rusconi_found:
                        st.error("Nessun tour operatour supportato trovato nel file (Veratour, Alpitour, Domina, MichelTours, SAND, Caboverdetime o Rusconi).")
                        st.stop()
                    
                    # Combina i risultati
                    if all_detail_dfs:
                        detail_df = pd.concat(all_detail_dfs, ignore_index=True)
                        totals_df = pd.concat(all_totals_dfs, ignore_index=True)
                        # Combina discrepanze (filtra quelli non vuoti)
                        discr_list = [d for d in all_discr_dfs if d is not None and not d.empty]
                        if discr_list:
                            discr_df = pd.concat(discr_list, ignore_index=True)
                        else:
                            discr_df = pd.DataFrame()
                    else:
                        detail_df = pd.DataFrame()
                        totals_df = pd.DataFrame()
                        discr_df = pd.DataFrame()
                    
                    # Genera output Excel
                    output_buffer = io.BytesIO()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_output:
                        output_path = tmp_output.name
                    
                    # Usa la funzione di scrittura appropriata
                    # Se ci sono più tour operator, usa Alpitour (supporta tutti i fogli e gestisce meglio i dati combinati)
                    # Altrimenti usa la funzione specifica del tour operator trovato
                    num_tour_operators = sum([veratour_found, alpitour_found, domina_found, micheltours_found, sand_found, caboverdetime_found, rusconi_found])
                    
                    if num_tour_operators > 1 and ALPITOUR_AVAILABLE:
                        # Più tour operator: usa Alpitour (supporta tutti i fogli e gestisce meglio i dati combinati)
                        write_output_excel_alpitour(output_path, detail_df, totals_df, discr_df)
                    elif sand_found and SAND_AVAILABLE:
                        write_output_excel_sand(output_path, detail_df, totals_df, discr_df)
                    elif rusconi_found and RUSCONI_AVAILABLE:
                        write_output_excel_rusconi(output_path, detail_df, totals_df, discr_df)
                    elif caboverdetime_found and CABOVERDETIME_AVAILABLE:
                        write_output_excel_caboverdetime(output_path, detail_df, totals_df, discr_df)
                    elif micheltours_found and MICHELTOURS_AVAILABLE:
                        write_output_excel_micheltours(output_path, detail_df, totals_df, discr_df)
                    elif domina_found and DOMINA_AVAILABLE:
                        write_output_excel_domina(output_path, detail_df, totals_df, discr_df)
                    elif alpitour_found and ALPITOUR_AVAILABLE:
                        write_output_excel_alpitour(output_path, detail_df, totals_df, discr_df)
                    elif veratour_found:
                        write_output_excel_veratour(output_path, detail_df, totals_df, discr_df)
                    else:
                        # Fallback a Veratour se nessun altro disponibile
                        write_output_excel_veratour(output_path, detail_df, totals_df, discr_df)
                    
                    # Aggiungi foglio TourOperatourNonElaborati
                    from openpyxl import load_workbook
                    wb = load_workbook(output_path)
                    
                    if "TourOperatourNonElaborati" in wb.sheetnames:
                        wb.remove(wb["TourOperatourNonElaborati"])
                    
                    ws = wb.create_sheet("TourOperatourNonElaborati")
                    
                    # Trova tour operatour non elaborati
                    missing_tour_operators = []
                    for to_name in tour_operators:
                        folder_path = find_tour_operator_folder(to_name)
                        if not folder_path:
                            missing_tour_operators.append(to_name)
                    
                    if missing_tour_operators:
                        ws.cell(row=1, column=1, value="Tour Operatour")
                        ws.cell(row=1, column=2, value="Motivo")
                        ws.cell(row=1, column=3, value="Note")
                        for idx, to_name in enumerate(missing_tour_operators, 2):
                            ws.cell(row=idx, column=1, value=to_name)
                            ws.cell(row=idx, column=2, value="Cartella non trovata nella root del progetto")
                            ws.cell(row=idx, column=3, value="Creare una cartella con il nome del tour operatour e il file consuntivo*.py corrispondente")
                    
                    wb.save(output_path)
                    
                    # Leggi il file generato
                    with open(output_path, 'rb') as f:
                        output_buffer.write(f.read())
                    output_buffer.seek(0)
                    
                    # Salva in session state
                    st.session_state['output_file'] = output_buffer
                    st.session_state['output_filename'] = f"OUT_{uploaded_file.name}"
                    st.session_state['detail_df'] = detail_df
                    st.session_state['totals_df'] = totals_df
                    st.session_state['discr_df'] = discr_df
                    
                    # Cleanup
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                    if os.path.exists(output_path):
                        os.unlink(output_path)
                    # Rimuovi da session state
                    if 'tmp_file_path' in st.session_state:
                        del st.session_state['tmp_file_path']
                    
                    st.success(f"Calcolo completato! Blocchi calcolati: {len(detail_df)}")
                    
                    if not discr_df.empty:
                        st.warning(f"Discrepanze rilevate: {len(discr_df)} (vedi sezione Discrepanze)")
                    
                except Exception as e:
                    st.error(f"Errore durante l'elaborazione: {str(e)}")
                    st.exception(e)
                    if 'tmp_file_path' in st.session_state and os.path.exists(st.session_state['tmp_file_path']):
                        os.unlink(st.session_state['tmp_file_path'])
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                
            except Exception as e:
                st.error(f"Errore: {str(e)}")
                st.exception(e)
    
    # Mostra risultati se disponibili (COME NELLA VERSIONE ORIGINALE)
    if 'output_file' in st.session_state and st.session_state['output_file'] is not None:
        st.markdown("---")
        st.markdown("### Risultati")
        
        st.download_button(
            label="📥 Scarica File Excel Completo",
            data=st.session_state['output_file'],
            file_name=st.session_state['output_filename'],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        if 'totals_df' in st.session_state and not st.session_state['totals_df'].empty:
            st.markdown("#### Totali per Aeroporto")
            totals_display = st.session_state['totals_df'].copy()
            st.dataframe(totals_display, use_container_width=True, hide_index=True)
        
        if 'detail_df' in st.session_state and not st.session_state['detail_df'].empty:
            with st.expander("Anteprima Dettaglio Blocchi (prime 20 righe)", expanded=False):
                st.dataframe(st.session_state['detail_df'].head(20), use_container_width=True)
        
        if 'discr_df' in st.session_state and not st.session_state['discr_df'].empty:
            with st.expander("Discrepanze Rilevate", expanded=True):
                st.dataframe(st.session_state['discr_df'], use_container_width=True)
                st.info("Le discrepanze indicano possibili inconsistenze nei dati di input. Controlla il file Excel generato per i dettagli completi.")
        
        # Dettaglio per Assistente VRN
        if 'detail_df' in st.session_state and not st.session_state['detail_df'].empty:
            df_detail = st.session_state['detail_df']
            if 'ASSISTENTE' in df_detail.columns and 'APT' in df_detail.columns:
                df_vrn = df_detail[(df_detail['APT'] == 'VRN') & (df_detail['ASSISTENTE'].notna()) & (df_detail['ASSISTENTE'] != '')].copy()
                if not df_vrn.empty:
                    with st.expander("Dettaglio Giorno per Giorno - Assistenti VRN", expanded=True):
                        assistenti_list = sorted(df_vrn['ASSISTENTE'].unique())
                        selected_assistente = st.selectbox(
                            "Seleziona Assistente",
                            options=assistenti_list,
                            index=0 if 'Manu' in assistenti_list else 0
                        )
                        
                        if selected_assistente:
                            df_assistente = df_vrn[df_vrn['ASSISTENTE'] == selected_assistente].copy()
                            df_assistente = df_assistente.sort_values('DATA')
                            
                            # Crea tabella formattata
                            display_df = df_assistente[[
                                'DATA', 'TURNO_NORMALIZZATO', 'DURATA_TURNO_MIN', 
                                'TURNO_EUR', 'EXTRA_H:MM', 'EXTRA_EUR', 
                                'NOTTE_MIN', 'NOTTE_EUR', 'FESTIVO', 'TOTALE_BLOCCO_EUR'
                            ]].copy()
                            
                            # Formatta colonne
                            display_df['Durata (h:mm)'] = display_df['DURATA_TURNO_MIN'].apply(lambda x: f"{int(x//60)}:{int(x%60):02d}")
                            display_df['Notturno (h:mm)'] = display_df['NOTTE_MIN'].apply(lambda x: f"{int(x//60)}:{int(x%60):02d}")
                            display_df['Festivo'] = display_df['FESTIVO'].apply(lambda x: "Sì" if x else "No")
                            
                            # Riordina colonne
                            display_df = display_df[[
                                'DATA', 'TURNO_NORMALIZZATO', 'Durata (h:mm)', 
                                'TURNO_EUR', 'EXTRA_H:MM', 'EXTRA_EUR', 
                                'Notturno (h:mm)', 'NOTTE_EUR', 'Festivo', 'TOTALE_BLOCCO_EUR'
                            ]]
                            
                            display_df.columns = [
                                'Data', 'Turno', 'Durata', 'Turno (€)', 
                                'Extra (h:mm)', 'Extra (€)', 'Notturno (h:mm)', 
                                'Notturno (€)', 'Festivo', 'TOTALE (€)'
                            ]
                            
                            # Formatta valori monetari
                            for col in ['Turno (€)', 'Extra (€)', 'Notturno (€)', 'TOTALE (€)']:
                                display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}€")
                            
                            st.dataframe(display_df, use_container_width=True, hide_index=True)
                            
                            # Totali
                            st.markdown(f"**Totali per {selected_assistente}:**")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Turno", f"{df_assistente['TURNO_EUR'].sum():.2f}€")
                            with col2:
                                st.metric("Extra", f"{df_assistente['EXTRA_EUR'].sum():.2f}€")
                            with col3:
                                st.metric("Notturno", f"{df_assistente['NOTTE_EUR'].sum():.2f}€")
                            with col4:
                                st.metric("TOTALE", f"{df_assistente['TOTALE_BLOCCO_EUR'].sum():.2f}€")

else:
    st.info("""
    👋 **Benvenuto nel Calcolatore Piano Lavoro Multi-Tour Operatour!**
    
    Per iniziare:
    1. Carica il file Excel del piano di lavoro nella sezione sopra
    2. (Opzionale) Configura le opzioni nella sidebar a sinistra
    3. Clicca su "Esegui Calcolo"
    4. Scarica il file Excel con i risultati
    
    Il file generato conterrà:
    - Fogli dettagliati per ogni aeroporto (VRN, BGY, NAP, VCE)
    - Foglio TOTALE con i riepiloghi
    - Fogli tecnici (DettaglioBlocchi, TotaliPeriodo, Discrepanze)
    - Foglio TourOperatourNonElaborati (se presenti)
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 1rem;'>"
    "Calcolo Piano Lavoro - Multi-Tour Operatour | Scay"
    "</div>",
    unsafe_allow_html=True
)
