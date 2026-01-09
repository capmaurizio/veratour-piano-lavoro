#!/usr/bin/env python3
"""
Script per generare la tabella giorno per giorno per tutti gli aeroporti per Alpitour.
Uso: python tabella_verona_alpitour.py [file_excel_output]
"""

import pandas as pd
import re
import sys
from datetime import datetime

def format_hmm(minutes):
    """Formatta minuti in formato h:mm"""
    if minutes == 0:
        return "0:00"
    h = int(minutes) // 60
    m = int(minutes) % 60
    return f"{h}:{m:02d}"

def genera_tabella_aeroporto(df_apt, apt_name):
    """Genera la tabella giorno per giorno per un aeroporto"""
    df_apt['DATA_DT'] = pd.to_datetime(df_apt['DATA'], dayfirst=True)
    df_apt = df_apt.sort_values(['DATA_DT', 'TURNO_NORMALIZZATO'])
    
    # Mapping giorni
    giorni_ita = {
        'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì',
        'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica',
        'Mon': 'Lun', 'Tue': 'Mar', 'Wed': 'Mer', 'Thu': 'Gio', 'Fri': 'Ven', 'Sat': 'Sab', 'Sun': 'Dom'
    }
    
    # Estrai SC1, SC2, ecc. e fasce orarie
    rows_table = []
    for _, row in df_apt.iterrows():
        data_dt = row['DATA_DT']
        data_str = data_dt.strftime('%d/%m/%Y')
        giorno_settimana_en = data_dt.strftime('%A')
        giorno_settimana = giorni_ita.get(giorno_settimana_en, giorno_settimana_en[:3])
        is_festivo = row['FESTIVO']
        
        # Estrai SC1, SC2, ecc. e fascia oraria
        turno_norm = str(row['TURNO_NORMALIZZATO']).strip()
        
        # Cerca prefisso SC1, SC2, SC3, ecc.
        sc_match = re.search(r'\b(SC\d+|AB\d+)\b', turno_norm, re.I)
        sc_prefix = sc_match.group(1).upper() if sc_match else ""
        
        # Estrai fascia oraria
        time_match = re.search(r'(\d{1,2}:\d{2})\s*[-–—]\s*(\d{1,2}:\d{2})', turno_norm)
        if time_match:
            fascia_oraria = f"{time_match.group(1)}-{time_match.group(2)}"
        else:
            fascia_oraria = turno_norm
        
        # Combina SC e fascia oraria
        if sc_prefix:
            fasce_orarie = f"{sc_prefix} {fascia_oraria}"
        else:
            fasce_orarie = fascia_oraria
        
        periodo = f"{data_str} ({giorno_settimana})"
        if is_festivo:
            periodo += " [FESTIVO]"
        
        rows_table.append({
            'Periodo': periodo,
            'Fasce Orarie': fasce_orarie,
            'Turno (h:mm)': format_hmm(int(row['DURATA_TURNO_MIN'])),
            'Turno (€)': f"{row['TURNO_EUR']:.2f}".replace('.', ','),
            'Extra (h:mm)': format_hmm(int(row['EXTRA_MIN'])),
            'Extra (€)': f"{row['EXTRA_EUR']:.2f}".replace('.', ','),
            'Notturno (h:mm)': format_hmm(int(row['NOTTE_MIN'])),
            'Notturno (€)': f"{row['NOTTE_EUR']:.2f}".replace('.', ','),
            'TOTALE (€)': f"{row['TOTALE_BLOCCO_EUR']:.2f}".replace('.', ',')
        })
    
    # Crea DataFrame
    df_table = pd.DataFrame(rows_table)
    
    # Aggiungi totale
    tot_turno_apt = df_apt['TURNO_EUR'].sum()
    tot_extra_apt = df_apt['EXTRA_EUR'].sum()
    tot_notte_apt = df_apt['NOTTE_EUR'].sum()
    tot_apt = df_apt['TOTALE_BLOCCO_EUR'].sum()
    tot_turno_min_apt = int(df_apt['DURATA_TURNO_MIN'].sum())
    tot_extra_min_apt = int(df_apt['EXTRA_MIN'].sum())
    tot_notte_min_apt = int(df_apt['NOTTE_MIN'].sum())
    
    df_table = pd.concat([
        df_table,
        pd.DataFrame([{
            'Periodo': 'TOTALE',
            'Fasce Orarie': '',
            'Turno (h:mm)': format_hmm(tot_turno_min_apt),
            'Turno (€)': f"{tot_turno_apt:.2f}".replace('.', ','),
            'Extra (h:mm)': format_hmm(tot_extra_min_apt),
            'Extra (€)': f"{tot_extra_apt:.2f}".replace('.', ','),
            'Notturno (h:mm)': format_hmm(tot_notte_min_apt),
            'Notturno (€)': f"{tot_notte_apt:.2f}".replace('.', ','),
            'TOTALE (€)': f"{tot_apt:.2f}".replace('.', ',')
        }])
    ], ignore_index=True)
    
    # Stampa la tabella
    print(f'{apt_name} - DICEMBRE 2025')
    print('\t'.join(df_table.columns))
    for _, row in df_table.iterrows():
        print('\t'.join(str(val) for val in row.values))
    print()  # Riga vuota tra aeroporti

def genera_tabelle_tutti_aeroporti(file_excel="OUT_ALPITOUR_DICEMBRE25_FINALE.xlsx"):
    """Genera la tabella giorno per giorno per tutti gli aeroporti"""
    
    # Leggi il file
    df = pd.read_excel(file_excel, sheet_name='DettaglioBlocchi')
    
    # Ottieni lista aeroporti unici
    aeroporti = sorted(df['APT'].unique())
    
    # Genera tabella per ogni aeroporto
    for apt in aeroporti:
        df_apt = df[df['APT'] == apt].copy()
        genera_tabella_aeroporto(df_apt, apt)

if __name__ == "__main__":
    file_excel = sys.argv[1] if len(sys.argv) > 1 else "OUT_ALPITOUR_DICEMBRE25_FINALE.xlsx"
    genera_tabelle_tutti_aeroporti(file_excel)

