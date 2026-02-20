#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaccia Web Streamlit Multi-Tour Operatour
Single-section layout: Upload → Detect → Calculate → Results
"""

import streamlit as st
import os
import tempfile

from ui_styles import (
    inject_styles, render_top_bar, render_footer,
    render_stepper, render_stat_card, render_status_line,
)
from tour_operators import detect_tour_operators, find_tour_operator_folder
from processing import run_calculation

# ═══════════════════════════════════════════════════════════════════════════════
# Page config
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SCAY Group — Piano Lavoro",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_styles()

# ═══════════════════════════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════════════════════════
VALID_USERNAME = "silvia"
VALID_PASSWORD = "1"

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False


def login_page():
    st.markdown('<div style="height:10vh"></div>', unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1.2, 1, 1.2])
    with col_c:
        st.markdown("""
        <div class="login-card">
            <div class="login-brand">
                <div class="login-logo">S</div>
                <div class="login-brand-text">Piano Lavoro</div>
            </div>
            <div class="login-subtitle">Accedi al sistema di calcolo</div>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Username")
            password = st.text_input("Password", type="password", placeholder="Password")
            submit = st.form_submit_button("Accedi", use_container_width=True)
            if submit:
                if username == VALID_USERNAME and password == VALID_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Credenziali non valide.")
        st.markdown('<div class="login-footer">SCAY Group S.n.c. · Bergamo</div>',
                    unsafe_allow_html=True)


if not st.session_state.authenticated:
    login_page()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# Determine current step for stepper
# ═══════════════════════════════════════════════════════════════════════════════
has_results = ('output_file' in st.session_state and
               st.session_state['output_file'] is not None)

# ═══════════════════════════════════════════════════════════════════════════════
# Top bar + logout
# ═══════════════════════════════════════════════════════════════════════════════
render_top_bar()

col_spacer, col_dl, col_logout = st.columns([4, 1, 1])
with col_dl:
    if has_results:
        st.download_button(
            label="Scarica risultati",
            data=st.session_state['output_file'],
            file_name=st.session_state.get('output_filename', 'output.xlsx'),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="download_top",
        )
with col_logout:
    if st.button("Esci", use_container_width=True, type="secondary"):
        for k in list(st.session_state.keys()):
            if k != 'authenticated':
                del st.session_state[k]
        st.session_state.authenticated = False
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# File uploader (always visible at top)
# ═══════════════════════════════════════════════════════════════════════════════
uploaded_file = st.file_uploader(
    "Seleziona il file Excel del piano di lavoro",
    type=["xlsx", "xls"],
    help="File Excel contenente il piano di lavoro",
)

if uploaded_file is None:
    # Step 0: waiting for upload
    render_stepper(0)
    st.markdown(
        '<div style="text-align:center;padding:24px 0;color:var(--ink-4);font-size:0.85rem;">'
        'Seleziona un file Excel per iniziare l\'elaborazione.</div>',
        unsafe_allow_html=True,
    )
    render_footer()
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# File uploaded — save temp + detect TOs
# ═══════════════════════════════════════════════════════════════════════════════
st.session_state['uploaded_file'] = uploaded_file

with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
    tmp_file.write(uploaded_file.getvalue())
    tmp_path = tmp_file.name
st.session_state['tmp_file_path'] = tmp_path

# Detect tour operators
tour_operators, aliservice_managed = detect_tour_operators(tmp_path)

aliservice_available = False
if aliservice_managed:
    aliservice_folder = find_tour_operator_folder("Aliservice")
    if aliservice_folder:
        aliservice_available = True

all_tour_operators = set(tour_operators)
if aliservice_available:
    all_tour_operators.add("ALISERVICE")

available_folders = {}
missing = []
for to_name in sorted(all_tour_operators):
    if to_name in aliservice_managed and aliservice_available:
        continue
    folder = find_tour_operator_folder(to_name)
    if folder:
        available_folders[to_name] = folder
    else:
        missing.append(to_name)

# ═══════════════════════════════════════════════════════════════════════════════
# Show results if available, else show detection + calculate
# ═══════════════════════════════════════════════════════════════════════════════
if has_results:
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 3: Completed — show stepper + results
    # ═════════════════════════════════════════════════════════════════════════
    render_stepper(4)  # all done

    detail_df = st.session_state.get('detail_df')
    discr_df = st.session_state.get('discr_df')
    processed_count = st.session_state.get('processed_count', 0)

    # Stat cards
    col1, col2, col3 = st.columns(3)
    with col1:
        render_stat_card(processed_count, "Tour Operator")
    with col2:
        render_stat_card(
            len(detail_df) if detail_df is not None else 0,
            "Blocchi calcolati",
            "green",
        )
    with col3:
        discr_count = len(discr_df) if discr_df is not None and not discr_df.empty else 0
        render_stat_card(
            discr_count,
            "Discrepanze",
            "amber" if discr_count > 0 else "green",
        )

    st.markdown("")

    # Detected TOs summary
    if all_tour_operators:
        render_status_line("●", f"Rilevati: {', '.join(sorted(all_tour_operators))}", "info")
    if available_folders:
        render_status_line("✓", f"Elaborati: {', '.join(sorted(available_folders.keys()))}", "success")
    if missing:
        render_status_line("–", f"Non codificati: {', '.join(sorted(missing))}", "warn")

    # Discrepanze
    if discr_df is not None and not discr_df.empty:
        with st.expander(f"Discrepanze rilevate ({discr_count})", expanded=False):
            st.dataframe(discr_df, use_container_width=True)

    st.markdown("")

    # Download
    st.download_button(
        label="Scarica file Excel completo",
        data=st.session_state['output_file'],
        file_name=st.session_state.get('output_filename', 'output.xlsx'),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="download_bottom",
    )

    render_status_line(
        "i",
        "Fogli per aeroporto, TOTALE, DettaglioBlocchi, TotaliPeriodo, Discrepanze, TourOperatourRilevati.",
        "info",
    )

else:
    # ═════════════════════════════════════════════════════════════════════════
    # STEP 1-2: Detected TOs — show status lines + calculate button
    # ═════════════════════════════════════════════════════════════════════════
    render_stepper(2)  # at elaboration step

    if all_tour_operators:
        render_status_line("●", f"Rilevati: {', '.join(sorted(all_tour_operators))}", "info")
    if available_folders:
        render_status_line("✓", f"Calcolo disponibile: {', '.join(sorted(available_folders.keys()))}", "success")
    if missing:
        render_status_line("–", f"Senza modulo: {', '.join(sorted(missing))}", "warn")

    st.markdown("")

    # Defaults
    apt_filter = []
    night_mode = "DIFF5"
    round_extra_mode = "NONE"
    round_extra_step = 5
    round_night_mode = "NONE"
    round_night_step = 5
    holiday_file = None

    if st.button("Esegui elaborazione", type="primary", use_container_width=True):
        with st.spinner("Elaborazione in corso..."):
            try:
                result = run_calculation(
                    tmp_path=tmp_path,
                    uploaded_file_name=uploaded_file.name,
                    apt_filter=apt_filter,
                    night_mode=night_mode,
                    round_extra_mode=round_extra_mode,
                    round_extra_step=round_extra_step,
                    round_night_mode=round_night_mode,
                    round_night_step=round_night_step,
                    holiday_file=holiday_file,
                )
                if result:
                    st.session_state['output_file'] = result['output_buffer']
                    st.session_state['output_filename'] = result['output_filename']
                    st.session_state['detail_df'] = result['detail_df']
                    st.session_state['totals_df'] = result['totals_df']
                    st.session_state['discr_df'] = result['discr_df']
                    st.session_state['processed_count'] = result['processed_count']
                    st.rerun()
            except Exception as e:
                st.error(f"Errore: {str(e)}")
                st.exception(e)

# ═══════════════════════════════════════════════════════════════════════════════
render_footer()
