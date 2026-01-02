#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaccia Web Streamlit per Calcolatore Veratour 2025
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
from consuntivoveratour import (
    CalcConfig,
    RoundingPolicy,
    process_files,
    write_output_excel,
    load_holiday_list
)

# Configurazione pagina
st.set_page_config(
    page_title="Veratour 2025 - Calcolatore",
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
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">📊 Veratour 2025 - Calcolatore Blocchi</div>', unsafe_allow_html=True)

# Sidebar con opzioni avanzate
with st.sidebar:
    st.header("⚙️ Opzioni di Calcolo")
    
    # Filtro aeroporti
    apt_filter = st.multiselect(
        "Filtra Aeroporti (opzionale)",
        options=["VRN", "BGY", "NAP", "VCE"],
        help="Seleziona gli aeroporti da includere. Lascia vuoto per includere tutti."
    )
    
    # Modalità notturno
    night_mode = st.selectbox(
        "Modalità Notturno",
        options=["DIFF5", "FULL30"],
        index=0,
        help="DIFF5: Maggiorazione differenziale (€5/h). FULL30: Tariffa piena (€30/h)."
    )
    
    st.subheader("Arrotondamenti")
    
    # Arrotondamento Extra
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
    
    # Arrotondamento Notturno
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
    
    # File festivi (opzionale)
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
    help="Carica il file Excel contenente il piano di lavoro Veratour"
)

if uploaded_file is not None:
    # Mostra info file
    file_details = {
        "Nome file": uploaded_file.name,
        "Dimensione": f"{uploaded_file.size / 1024:.2f} KB",
        "Tipo": uploaded_file.type
    }
    
    with st.expander("ℹ️ Informazioni File", expanded=False):
        st.json(file_details)
    
    # Pulsante per eseguire il calcolo
    if st.button("🚀 Esegui Calcolo", type="primary", use_container_width=True):
        with st.spinner("⏳ Elaborazione in corso..."):
            try:
                # Salva file temporaneo
                import tempfile
                import os
                
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
                    
                    # Configurazione
                    cfg = CalcConfig(
                        apt_filter=apt_filter if apt_filter else None,
                        night_mode=night_mode,
                        rounding_extra=RoundingPolicy(round_extra_mode, round_extra_step),
                        rounding_night=RoundingPolicy(round_night_mode, round_night_step),
                        holiday_dates=holiday_dates,
                    )
                    
                    # Processa file
                    detail_df, totals_df, discr_df = process_files([tmp_path], cfg)
                    
                    # Genera output Excel in memoria
                    output_buffer = io.BytesIO()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_output:
                        output_path = tmp_output.name
                    
                    write_output_excel(output_path, detail_df, totals_df, discr_df)
                    
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
    
    # Mostra risultati se disponibili
    if 'output_file' in st.session_state and st.session_state['output_file'] is not None:
        st.markdown("---")
        st.markdown("### 📊 Risultati")
        
        # Download button
        st.download_button(
            label="📥 Scarica File Excel Completo",
            data=st.session_state['output_file'],
            file_name=st.session_state['output_filename'],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        # Anteprima Totali
        if 'totals_df' in st.session_state and not st.session_state['totals_df'].empty:
            st.markdown("#### 📈 Totali per Aeroporto")
            totals_display = st.session_state['totals_df'].copy()
            
            # Formatta le colonne numeriche
            if 'Turno (€)' in totals_display.columns:
                totals_display['Turno (€)'] = totals_display['Turno (€)'].apply(lambda x: f"{x:,.2f}€" if pd.notna(x) else "")
            if 'Extra (€)' in totals_display.columns:
                totals_display['Extra (€)'] = totals_display['Extra (€)'].apply(lambda x: f"{x:,.2f}€" if pd.notna(x) else "")
            if 'Notturno (€)' in totals_display.columns:
                totals_display['Notturno (€)'] = totals_display['Notturno (€)'].apply(lambda x: f"{x:,.2f}€" if pd.notna(x) else "")
            if 'TOTALE (€)' in totals_display.columns:
                totals_display['TOTALE (€)'] = totals_display['TOTALE (€)'].apply(lambda x: f"{x:,.2f}€" if pd.notna(x) else "")
            
            st.dataframe(totals_display, use_container_width=True, hide_index=True)
        
        # Anteprima Dettaglio (prime righe)
        if 'detail_df' in st.session_state and not st.session_state['detail_df'].empty:
            with st.expander("📋 Anteprima Dettaglio Blocchi (prime 20 righe)", expanded=False):
                st.dataframe(st.session_state['detail_df'].head(20), use_container_width=True)
        
        # Discrepanze
        if 'discr_df' in st.session_state and not st.session_state['discr_df'].empty:
            with st.expander("⚠️ Discrepanze Rilevate", expanded=True):
                st.dataframe(st.session_state['discr_df'], use_container_width=True)
                st.info("Le discrepanze indicano possibili inconsistenze nei dati di input. Controlla il file Excel generato per i dettagli completi.")

else:
    # Istruzioni iniziali
    st.info("""
    👋 **Benvenuto nel Calcolatore Veratour 2025!**
    
    Per iniziare:
    1. Carica il file Excel del piano di lavoro nella sezione sopra
    2. (Opzionale) Configura le opzioni nella sidebar a sinistra
    3. Clicca su "Esegui Calcolo"
    4. Scarica il file Excel con i risultati
    
    Il file generato conterrà:
    - Fogli dettagliati per ogni aeroporto (VRN, BGY, NAP, VCE)
    - Foglio TOTALE con i riepiloghi
    - Fogli tecnici (DettaglioBlocchi, TotaliPeriodo, Discrepanze)
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 1rem;'>"
    "Veratour 2025 - Calcolatore Blocchi | Scay"
    "</div>",
    unsafe_allow_html=True
)

