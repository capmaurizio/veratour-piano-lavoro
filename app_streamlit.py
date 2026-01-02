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

# Aggiungi Veratour al path per import
veratour_path = os.path.join(os.path.dirname(__file__), 'Veratour')
if veratour_path not in sys.path:
    sys.path.insert(0, veratour_path)

from consuntivoveratour import (
    CalcConfig,
    RoundingPolicy,
    process_files,
    write_output_excel,
    load_holiday_list
)

# Configurazione pagina
st.set_page_config(
    page_title="Calcolo Piano Lavoro - Multi-Tour Operatour",
    page_icon="📊",
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
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📊 Calcolo Piano Lavoro - Multi-Tour Operatour</div>', unsafe_allow_html=True)


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
    
    night_mode = st.selectbox(
        "Modalità Notturno",
        options=["DIFF5", "FULL30"],
        index=0,
        help="DIFF5: Maggiorazione differenziale (€5/h). FULL30: Tariffa piena (€30/h)."
    )
    
    st.subheader("Arrotondamenti")
    
    round_extra_mode = st.selectbox(
        "Arrotondamento Extra",
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
        "Arrotondamento Notturno",
        options=["NONE", "FLOOR", "CEIL", "NEAREST"],
        index=0
    )
    round_night_step = st.number_input(
        "Step Arrotondamento Notturno (minuti)",
        min_value=1,
        value=5,
        step=1
    )
    
    holiday_file = st.file_uploader(
        "File Festivi (opzionale)",
        type=["txt", "csv"],
        help="File con lista festivi (una data per riga, formato YYYY-MM-DD)"
    )

# Area principale
st.markdown("### 📁 Carica File Excel del Piano di Lavoro")

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
                st.info(f"📋 Tour operatour rilevati: {', '.join(sorted(tour_operators))}")
                
                available_folders = {}
                missing_tour_operators = []
                
                for to_name in tour_operators:
                    folder_path = find_tour_operator_folder(to_name)
                    if folder_path:
                        available_folders[to_name] = folder_path
                    else:
                        missing_tour_operators.append(to_name)
                
                if available_folders:
                    st.success(f"✅ Tour operatour con calcolo disponibile: {', '.join(available_folders.keys())}")
                
                if missing_tour_operators:
                    st.warning(f"⚠️ Tour operatour senza cartella (non elaborati): {', '.join(missing_tour_operators)}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    # Pulsante per eseguire il calcolo
    if st.button("🚀 Esegui Calcolo", type="primary", use_container_width=True):
        with st.spinner("⏳ Elaborazione in corso..."):
            try:
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
                    
                    # Per ora elabora solo Veratour (come nella versione originale)
                    # TODO: estendere per supportare altri tour operatour
                    veratour_found = False
                    for to_name in tour_operators:
                        to_clean = re.sub(r'[^a-zA-Z]', '', to_name).lower()
                        if 'veratour' in to_clean:
                            veratour_found = True
                            break
                    
                    if not veratour_found:
                        st.warning("⚠️ Nessun tour operatour Veratour trovato nel file. Elaborazione solo per Veratour.")
                    
                    # Configurazione (come nella versione originale)
                    cfg = CalcConfig(
                        apt_filter=apt_filter if apt_filter else None,
                        night_mode=night_mode,
                        rounding_extra=RoundingPolicy(round_extra_mode, round_extra_step),
                        rounding_night=RoundingPolicy(round_night_mode, round_night_step),
                        holiday_dates=holiday_dates,
                    )
                    
                    # Processa file (COME NELLA VERSIONE ORIGINALE)
                    detail_df, totals_df, discr_df = process_files([tmp_path], cfg)
                    
                    # Genera output Excel
                    output_buffer = io.BytesIO()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_output:
                        output_path = tmp_output.name
                    
                    # USA LA FUNZIONE ORIGINALE
                    write_output_excel(output_path, detail_df, totals_df, discr_df)
                    
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
                    os.unlink(tmp_path)
                    os.unlink(output_path)
                    
                    st.success(f"✅ Calcolo completato! Blocchi calcolati: {len(detail_df)}")
                    
                    if not discr_df.empty:
                        st.warning(f"⚠️ Discrepanze rilevate: {len(discr_df)} (vedi sezione Discrepanze)")
                    
                except Exception as e:
                    st.error(f"❌ Errore durante l'elaborazione: {str(e)}")
                    st.exception(e)
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                
            except Exception as e:
                st.error(f"❌ Errore: {str(e)}")
                st.exception(e)
    
    # Mostra risultati se disponibili (COME NELLA VERSIONE ORIGINALE)
    if 'output_file' in st.session_state and st.session_state['output_file'] is not None:
        st.markdown("---")
        st.markdown("### 📊 Risultati")
        
        st.download_button(
            label="📥 Scarica File Excel Completo",
            data=st.session_state['output_file'],
            file_name=st.session_state['output_filename'],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        if 'totals_df' in st.session_state and not st.session_state['totals_df'].empty:
            st.markdown("#### 📈 Totali per Aeroporto")
            totals_display = st.session_state['totals_df'].copy()
            st.dataframe(totals_display, use_container_width=True, hide_index=True)
        
        if 'detail_df' in st.session_state and not st.session_state['detail_df'].empty:
            with st.expander("📋 Anteprima Dettaglio Blocchi (prime 20 righe)", expanded=False):
                st.dataframe(st.session_state['detail_df'].head(20), use_container_width=True)
        
        if 'discr_df' in st.session_state and not st.session_state['discr_df'].empty:
            with st.expander("⚠️ Discrepanze Rilevate", expanded=True):
                st.dataframe(st.session_state['discr_df'], use_container_width=True)
                st.info("Le discrepanze indicano possibili inconsistenze nei dati di input. Controlla il file Excel generato per i dettagli completi.")

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
