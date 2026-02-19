#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaccia Web Streamlit per Assistenti
Permette agli assistenti di inserire le ore effettive dei turni e calcolare automaticamente le tariffe
"""

import streamlit as st
import pandas as pd
import os
import sys
import tempfile
from datetime import datetime, date, time
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path

# Aggiungi il path per importare tariffe_collaboratori
sys.path.insert(0, os.path.dirname(__file__))
from tariffe_collaboratori import calcola_tariffa_collaboratore
from genera_template_assistente import genera_template_assistente
from genera_file_calcolo_assistente import genera_file_calcolo_assistente

# Configurazione pagina
st.set_page_config(
    page_title="Area Assistenti - Calcolo Piano Lavoro",
    page_icon="👤",
    layout="wide"
)

# Password di default per tutti gli assistenti (per ora)
DEFAULT_PASSWORD = "12345"

# Directory per salvare i dati degli assistenti
ASSISTENTI_DATA_DIR = "dati_assistenti"
os.makedirs(ASSISTENTI_DATA_DIR, exist_ok=True)

# File del piano lavoro (da caricare)
PIANO_LAVORO_FILE = "piano_lavoro_corrente.xlsx"


def normalize_name(name: str) -> str:
    """Normalizza il nome dell'assistente per il matching"""
    return str(name).strip().upper()


def load_piano_lavoro(file_path: str) -> Optional[pd.DataFrame]:
    """Carica il piano lavoro dal file Excel"""
    try:
        if not os.path.exists(file_path):
            return None
        
        # Leggi solo il foglio "PIANO VOLI"
        xls = pd.ExcelFile(file_path)
        target_sheet = None
        for sheet in xls.sheet_names:
            if sheet.upper().strip() == "PIANO VOLI":
                target_sheet = sheet
                break
        
        if not target_sheet:
            st.error("Foglio 'PIANO VOLI' non trovato nel file Excel")
            return None
        
        df = pd.read_excel(file_path, sheet_name=target_sheet)
        
        # Normalizza colonne
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        return df
    except Exception as e:
        st.error(f"Errore nel caricare il piano lavoro: {str(e)}")
        return None


def get_turni_assistente(df: pd.DataFrame, nome_assistente: str) -> pd.DataFrame:
    """Filtra i turni per un assistente specifico"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Cerca colonna ASSISTENTE
    assistente_col = None
    for col in df.columns:
        if 'ASSISTENTE' in col.upper():
            assistente_col = col
            break
    
    if not assistente_col:
        return pd.DataFrame()
    
    # Filtra per assistente (case-insensitive)
    nome_norm = normalize_name(nome_assistente)
    mask = df[assistente_col].astype(str).str.upper().str.strip() == nome_norm
    turni = df[mask].copy()
    
    return turni


def get_assistente_data_file(nome_assistente: str) -> str:
    """Restituisce il path del file JSON per i dati dell'assistente"""
    nome_safe = normalize_name(nome_assistente).replace(" ", "_")
    return os.path.join(ASSISTENTI_DATA_DIR, f"{nome_safe}.json")


def load_assistente_data(nome_assistente: str) -> Dict:
    """Carica i dati salvati dell'assistente"""
    file_path = get_assistente_data_file(nome_assistente)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_assistente_data(nome_assistente: str, data: Dict):
    """Salva i dati dell'assistente"""
    file_path = get_assistente_data_file(nome_assistente)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        st.error(f"Errore nel salvare i dati: {str(e)}")
        return False


def parse_time_value(val) -> Optional[time]:
    """Converte un valore in time object"""
    if pd.isna(val):
        return None
    if isinstance(val, time):
        return val
    if isinstance(val, datetime):
        return val.time()
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['nan', 'none', '']:
        return None
    # Prova a parsare formato HH:MM o HH:MM:SS
    try:
        parts = val_str.split(':')
        if len(parts) >= 2:
            h = int(parts[0])
            m = int(parts[1])
            return time(h, m)
    except:
        pass
    return None


def parse_date_value(val) -> Optional[date]:
    """Converte un valore in date object"""
    if pd.isna(val):
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, pd.Timestamp):
        return val.date()
    return None


def calculate_tariffa_from_inputs(
    apt: str,
    nome_assistente: str,
    data_turno: date,
    std_time: Optional[time],
    durata_effettiva_min: int,
    extra_min: int,
    notte_min: int,
    tour_operator: Optional[str] = None,
    tipo_servizio: Optional[str] = None
) -> Dict[str, float]:
    """Calcola la tariffa basata sugli input dell'assistente"""
    
    # Verifica se è festivo
    is_festivo = False
    if data_turno:
        # Per FCO usa festivi specifici (include 29/6 Santi Pietro e Paolo)
        # Per altri aeroporti usa festivi nazionali standard
        try:
            from tariffe_collaboratori import get_fco_holidays, get_italian_holidays_2025
            apt_upper = apt.upper().strip() if apt else ''
            if apt_upper == 'FCO':
                holidays = get_fco_holidays()
            else:
                holidays = get_italian_holidays_2025()
        except ImportError:
            # Fallback: calcola festivi manualmente
            try:
                from dateutil.easter import easter
            except ImportError:
                def easter(year: int) -> date:
                    a = year % 19
                    b = year // 100
                    c = year % 100
                    d = (19 * a + b - b // 4 - ((b - (b + 8) // 25 + 1) // 3) + 15) % 30
                    e = (32 + 2 * (b % 4) + 2 * (c // 4) - d - (c % 4)) % 7
                    f = d + e - 7 * ((a + 11 * d + 22 * e) // 451) + 114
                    month = f // 31
                    day = (f % 31) + 1
                    return date(year, month, day)
            
            holidays = set()
            for year in (2025, 2026, 2027):
                holidays.update({
                    date(year, 1, 1), date(year, 1, 6), date(year, 4, 25),
                    date(year, 5, 1), date(year, 6, 2), date(year, 8, 15),
                    date(year, 11, 1), date(year, 12, 8), date(year, 12, 25), date(year, 12, 26)
                })
                easter_date = easter(year)
                holidays.add(easter_date)
                from datetime import timedelta
                holidays.add(easter_date + timedelta(days=1))
                # 29/6 per FCO (Santi Pietro e Paolo)
                apt_upper = apt.upper().strip() if apt else ''
                if apt_upper == 'FCO':
                    holidays.add(date(year, 6, 29))
        
        if data_turno in holidays:
            is_festivo = True
    
    # Calcola la tariffa usando il modulo tariffe_collaboratori
    tariffe = calcola_tariffa_collaboratore(
        aeroporto=apt,
        nome=nome_assistente,
        durata_min=durata_effettiva_min,
        extra_min=extra_min,
        minuti_notturni=notte_min,
        is_festivo=is_festivo,
        tour_operator=tour_operator,
        tipo_servizio=tipo_servizio
    )
    
    return tariffe


# ==================== INTERFACCIA ====================

# Inizializza session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'nome_assistente' not in st.session_state:
    st.session_state.nome_assistente = ""
if 'piano_lavoro_df' not in st.session_state:
    st.session_state.piano_lavoro_df = None

# Titolo principale
st.title("👤 Area Assistenti")
st.markdown("---")

# Sezione Login
if not st.session_state.logged_in:
    st.subheader("🔐 Login")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        nome_input = st.text_input("Nome Assistente", placeholder="Inserisci il tuo nome")
        password_input = st.text_input("Password", type="password", placeholder="Password")
        
        if st.button("Accedi", type="primary", use_container_width=True):
            if nome_input and password_input:
                # Per ora password fissa 12345 per tutti
                if password_input == DEFAULT_PASSWORD:
                    st.session_state.logged_in = True
                    st.session_state.nome_assistente = nome_input.strip()
                    st.rerun()
                else:
                    st.error("Password non corretta")
            else:
                st.warning("Inserisci nome e password")
    
    with col2:
        st.info("""
        **Istruzioni:**
        - Inserisci il tuo nome come appare nel piano lavoro
        - Password di default: **12345**
        - Dopo il login vedrai solo i tuoi turni assegnati
        """)

else:
    # Area assistente loggato
    nome_assistente = st.session_state.nome_assistente
    dati_salvati = load_assistente_data(nome_assistente)
    
    # Calcola statistiche PRIMA di mostrare l'header
    # Se il piano lavoro è caricato, calcola ore/minuti e giorni, altrimenti è zero
    totale_ore_prestate = 0.0
    totale_minuti_prestati = 0
    giorni_lavorati = 0
    num_turni_compilati = 0
    date_lavorate = set()
    
    if st.session_state.piano_lavoro_df is not None:
        # Piano lavoro caricato: calcola statistiche dai turni visibili
        df_piano = st.session_state.piano_lavoro_df
        turni = get_turni_assistente(df_piano, nome_assistente)
        
        if not turni.empty:
            # Calcola statistiche per ogni turno
            for idx, row in turni.iterrows():
                data_val = parse_date_value(row.get('DATA', None))
                apt_val = str(row.get('APT', '')).strip()
                volo_val = str(row.get('VOLO', '')).strip()
                
                if data_val:
                    data_key = data_val.strftime("%Y-%m-%d")
                    
                    # Prova tutte le varianti possibili di chiave
                    chiavi_possibili = []
                    if volo_val and volo_val.lower() not in ['nan', 'none', '']:
                        chiavi_possibili.append(f"{data_key}_{apt_val}_{volo_val.replace(' ', '_')}")
                    
                    std_val = row.get('STD', None)
                    std_time_val = parse_time_value(std_val)
                    if std_time_val:
                        chiavi_possibili.append(f"{data_key}_{apt_val}_{std_time_val.strftime('%H%M')}")
                    
                    chiavi_possibili.append(f"{data_key}_{apt_val}")
                    
                    # Cerca dati salvati
                    dati_turno = {}
                    for chiave in chiavi_possibili:
                        if chiave in dati_salvati:
                            dati_turno = dati_salvati[chiave]
                            break
                    
                    # Se ci sono dati salvati, aggiungi alle statistiche
                    if dati_turno and 'durata_effettiva_h' in dati_turno:
                        durata_h = float(dati_turno.get('durata_effettiva_h', 0))
                        extra_min = int(dati_turno.get('extra_min', 0))
                        
                        # Calcola totale ore (durata base + extra)
                        ore_turno = durata_h + (extra_min / 60.0)
                        totale_ore_prestate += ore_turno
                        
                        # Calcola totale minuti
                        minuti_turno = int(durata_h * 60) + extra_min
                        totale_minuti_prestati += minuti_turno
                        
                        # Aggiungi data ai giorni lavorati
                        date_lavorate.add(data_key)
                        num_turni_compilati += 1
            
            # Calcola giorni lavorati (date uniche)
            giorni_lavorati = len(date_lavorate)
    
    # Header con logout e statistiche
    col_header1, col_header2, col_header3, col_header4, col_header5 = st.columns([2, 1, 1, 1, 1])
    with col_header1:
        st.subheader(f"Benvenuto, {nome_assistente}")
        if num_turni_compilati > 0:
            st.caption(f"Turni compilati: {num_turni_compilati}")
    with col_header2:
        # Converti minuti in ore e minuti per display
        ore_totali = int(totale_minuti_prestati // 60)
        minuti_totali = int(totale_minuti_prestati % 60)
        st.metric(
            "⏱️ Ore Prestate", 
            f"{ore_totali}h {minuti_totali}m", 
            help=f"Totale ore e minuti prestati come assistenza"
        )
    with col_header3:
        st.metric(
            "📅 Giorni Lavorati", 
            f"{giorni_lavorati}", 
            help=f"Numero di giorni con turni compilati"
        )
    with col_header4:
        # Pulsante download template
        try:
            # Genera template solo quando necessario (lazy loading)
            nome_file_template = f"RIEPILOGO_ASSISTENZE_{nome_assistente.replace(' ', '_').replace('/', '_')}.xlsx"
            
            # Usa session state per evitare di rigenerare ogni volta
            template_key = f"template_{nome_assistente}"
            
            # Se il piano lavoro è caricato, includi i dati
            turni_piano = None
            if st.session_state.piano_lavoro_df is not None:
                turni_piano = get_turni_assistente(st.session_state.piano_lavoro_df, nome_assistente)
            
            # Genera file calcolo assistente se non esiste
            nome_safe = nome_assistente.replace(" ", "_").replace("/", "_").upper()
            file_calcolo_path = os.path.join("calcoli_assistenti", f"calcolo_{nome_safe}.py")
            if not os.path.exists(file_calcolo_path):
                try:
                    genera_file_calcolo_assistente(nome_assistente)
                except Exception as e:
                    st.warning(f"Non è stato possibile generare il file di calcolo: {str(e)}")
            
            # Genera template con dati aggiornati
            if template_key not in st.session_state or st.session_state.get('piano_lavoro_df') is not None:
                # Genera in file temporaneo
                with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                    template_path = tmp_file.name
                
                genera_template_assistente(
                    nome_assistente, 
                    template_path,
                    turni_piano_lavoro=turni_piano,
                    dati_salvati=dati_salvati
                )
                
                # Leggi i bytes
                with open(template_path, 'rb') as f:
                    st.session_state[template_key] = f.read()
                
                # Rimuovi file temporaneo
                try:
                    os.remove(template_path)
                except:
                    pass
            
            st.download_button(
                label="📥 Scarica Template",
                data=st.session_state[template_key],
                file_name=nome_file_template,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Scarica il template Excel con i dati del piano lavoro già compilati",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Errore generazione template: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    with col_header5:
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.nome_assistente = ""
            st.rerun()
    
    st.markdown("---")
    
    # Carica piano lavoro
    if st.session_state.piano_lavoro_df is None:
        st.info("📁 Carica il file del piano lavoro per vedere i tuoi turni")
        uploaded_file = st.file_uploader("Carica Piano Lavoro", type=["xlsx", "xls"])
        
        if uploaded_file is not None:
            # Salva temporaneamente il file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            df = load_piano_lavoro(tmp_path)
            if df is not None and not df.empty:
                st.session_state.piano_lavoro_df = df
                st.session_state.piano_lavoro_path = tmp_path
                st.success("✅ Piano lavoro caricato con successo!")
                st.rerun()
    else:
        # Mostra turni dell'assistente
        df_piano = st.session_state.piano_lavoro_df
        turni = get_turni_assistente(df_piano, nome_assistente)
        
        if turni.empty:
            st.warning(f"⚠️ Nessun turno trovato per {nome_assistente}")
            st.info("Verifica che il tuo nome nel piano lavoro corrisponda esattamente al nome inserito")
        else:
            st.success(f"✅ Trovati {len(turni)} turni")
            
            # Carica dati salvati dell'assistente (già caricati sopra per il totale)
            # dati_salvati = load_assistente_data(nome_assistente)  # Già caricato sopra
            
            # Prepara colonne per la visualizzazione
            display_cols = []
            for col in ['DATA', 'APT', 'TOUR OPERATOR', 'TURNO', 'STD', 'ATD', 'SERVIZIO', 'VOLO']:
                for df_col in turni.columns:
                    if col in df_col.upper():
                        display_cols.append(df_col)
                        break
            
            # Aggiungi colonne con ore/minuti prestati per ogni turno
            turni_display = turni[display_cols].copy() if display_cols else turni.copy()
            
            # Calcola ore/minuti per ogni riga
            ore_minuti_turni = []
            stati_compilazione = []
            
            for idx, row in turni.iterrows():
                # Crea chiave univoca come nel form
                data_val = parse_date_value(row.get('DATA', None))
                apt_val = str(row.get('APT', '')).strip()
                volo_val = str(row.get('VOLO', '')).strip()
                
                if data_val:
                    data_key = data_val.strftime("%Y-%m-%d")
                    
                    # Prova tutte le varianti possibili di chiave (per retrocompatibilità)
                    chiavi_possibili = []
                    
                    # 1. Chiave con volo (più specifica) - PRIORITARIA
                    if volo_val and volo_val.lower() not in ['nan', 'none', '']:
                        chiavi_possibili.append(f"{data_key}_{apt_val}_{volo_val.replace(' ', '_')}")
                    
                    # 2. Chiave con STD
                    std_val = row.get('STD', None)
                    std_time_val = parse_time_value(std_val)
                    if std_time_val:
                        chiavi_possibili.append(f"{data_key}_{apt_val}_{std_time_val.strftime('%H%M')}")
                    
                    # 3. Chiave semplice data_apt (retrocompatibilità con dati vecchi) - ULTIMA
                    chiavi_possibili.append(f"{data_key}_{apt_val}")
                    
                    # Cerca dati salvati per questo turno (prova tutte le varianti)
                    dati_turno = {}
                    for chiave in chiavi_possibili:
                        if chiave in dati_salvati:
                            dati_turno = dati_salvati[chiave]
                            break
                    
                    if dati_turno and 'durata_effettiva_h' in dati_turno:
                        durata_h = float(dati_turno.get('durata_effettiva_h', 0))
                        extra_min = int(dati_turno.get('extra_min', 0))
                        notte_min = int(dati_turno.get('notte_min', 0))
                        
                        # Calcola totale minuti (durata base + extra)
                        minuti_totali = int(durata_h * 60) + extra_min
                        ore_totali = minuti_totali // 60
                        minuti_rimanenti = minuti_totali % 60
                        
                        # Formatta display
                        if ore_totali > 0:
                            ore_minuti_turni.append(f"{ore_totali}h {minuti_rimanenti}m")
                        else:
                            ore_minuti_turni.append(f"{minuti_rimanenti}m")
                        
                        stati_compilazione.append("✅")
                    else:
                        ore_minuti_turni.append("—")  # Non ancora compilato
                        stati_compilazione.append("⏳")
                else:
                    ore_minuti_turni.append("—")
                    stati_compilazione.append("⏳")
            
            # Aggiungi colonne alla tabella
            turni_display['⏱️ Ore/Minuti'] = ore_minuti_turni
            turni_display['Stato'] = stati_compilazione
            
            # Conta turni compilati e non compilati
            turni_compilati = sum(1 for s in stati_compilazione if s == "✅")
            turni_non_compilati = len(stati_compilazione) - turni_compilati
            
            # Mostra turni in una tabella interattiva
            st.subheader("📋 I tuoi turni")
            
            if turni_non_compilati > 0:
                st.info(f"💡 {turni_non_compilati} turno/i devono ancora essere compilati.")
            
            if not turni_display.empty:
                st.dataframe(turni_display, use_container_width=True, hide_index=True)
