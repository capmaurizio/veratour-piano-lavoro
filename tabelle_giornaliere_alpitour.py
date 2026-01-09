#!/usr/bin/env python3
import pandas as pd
import locale
import re

# Imposta locale italiana per i giorni della settimana
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'it_IT')
    except:
        pass  # Se non disponibile, useremo mapping manuale

# Mapping giorni della settimana in italiano
giorni_ita = {
    'Monday': 'Lunedì',
    'Tuesday': 'Martedì',
    'Wednesday': 'Mercoledì',
    'Thursday': 'Giovedì',
    'Friday': 'Venerdì',
    'Saturday': 'Sabato',
    'Sunday': 'Domenica',
    'Mon': 'Lun',
    'Tue': 'Mar',
    'Wed': 'Mer',
    'Thu': 'Gio',
    'Fri': 'Ven',
    'Sat': 'Sab',
    'Sun': 'Dom'
}

file_excel = "OUT_ALPITOUR_DICEMBRE25_ALL.xlsx"

# Leggi dettaglio blocchi
df = pd.read_excel(file_excel, sheet_name='DettaglioBlocchi')

# Converti DATA in datetime per ordinamento
df['DATA_DT'] = pd.to_datetime(df['DATA'], dayfirst=True)

# Ordina per data e aeroporto
df = df.sort_values(['DATA_DT', 'APT', 'TURNO_NORMALIZZATO'])

print("=" * 100)
print("TABELLE CALCOLO GIORNO PER GIORNO - ALPITOUR DICEMBRE 2025")
print("=" * 100)
print()

# Per ogni aeroporto
for apt in sorted(df['APT'].unique()):
    df_apt = df[df['APT'] == apt].copy()
    
    print("=" * 100)
    print(f"AEROPORTO: {apt}")
    print("=" * 100)
    print()
    
    # Raggruppa per data e crea tabella
    rows_table = []
    
    for data_dt, group in df_apt.groupby('DATA_DT'):
        data_str = data_dt.strftime('%d/%m/%Y')
        giorno_settimana_en = data_dt.strftime('%A')
        # Converti in italiano
        giorno_settimana = giorni_ita.get(giorno_settimana_en, giorno_settimana_en[:3])
        is_festivo = group['FESTIVO'].iloc[0] if len(group) > 0 else False
        
        # Calcola totali giornalieri
        tot_turno = group['TURNO_EUR'].sum()
        tot_extra = group['EXTRA_EUR'].sum()
        tot_notte = group['NOTTE_EUR'].sum()
        tot_giorno = group['TOTALE_BLOCCO_EUR'].sum()
        tot_turno_min = int(group['DURATA_TURNO_MIN'].sum())
        tot_extra_min = int(group['EXTRA_MIN'].sum())
        tot_notte_min = int(group['NOTTE_MIN'].sum())
        
        # Estrai fasce orarie turni (rimuovi prefissi SC1, SC2, ecc.)
        fasce_turni = []
        for turno_norm in group['TURNO_NORMALIZZATO'].unique():
            # Rimuovi prefissi tipo "SC1 ", "SC2 ", ecc.
            turno_clean = str(turno_norm).strip()
            # Cerca pattern tipo "SC1 06:25-10:25" o "06:25-10:25"
            import re
            match = re.search(r'(\d{1,2}:\d{2})\s*[-–—]\s*(\d{1,2}:\d{2})', turno_clean)
            if match:
                inizio = match.group(1)
                fine = match.group(2)
                fasce_turni.append(f"{inizio}-{fine}")
            else:
                # Se non trova pattern, usa il turno normalizzato pulito
                fasce_turni.append(turno_clean)
        
        fasce_orarie = ", ".join(fasce_turni) if fasce_turni else ""
        
        # Formatta ore:minuti
        def format_hmm(minutes):
            if minutes == 0:
                return "0:00"
            h = minutes // 60
            m = minutes % 60
            return f"{h}:{m:02d}"
        
        # Formatta periodo
        periodo = f"{data_str} ({giorno_settimana})"
        if is_festivo:
            periodo += " [FESTIVO]"
        
        rows_table.append({
            'Periodo': periodo,
            'Fasce Orarie': fasce_orarie,
            'Turno (h:mm)': format_hmm(tot_turno_min),
            'Turno (€)': f"{tot_turno:.2f}".replace('.', ','),
            'Extra (h:mm)': format_hmm(tot_extra_min),
            'Extra (€)': f"{tot_extra:.2f}".replace('.', ','),
            'Notturno (h:mm)': format_hmm(tot_notte_min),
            'Notturno (€)': f"{tot_notte:.2f}".replace('.', ','),
            'TOTALE (€)': f"{tot_giorno:.2f}".replace('.', ',')
        })
    
    # Crea DataFrame per tabella
    df_table = pd.DataFrame(rows_table)
    
    # Aggiungi riga totale
    tot_turno_apt = df_apt['TURNO_EUR'].sum()
    tot_extra_apt = df_apt['EXTRA_EUR'].sum()
    tot_notte_apt = df_apt['NOTTE_EUR'].sum()
    tot_apt = df_apt['TOTALE_BLOCCO_EUR'].sum()
    tot_turno_min_apt = int(df_apt['DURATA_TURNO_MIN'].sum())
    tot_extra_min_apt = int(df_apt['EXTRA_MIN'].sum())
    tot_notte_min_apt = int(df_apt['NOTTE_MIN'].sum())
    
    def format_hmm(minutes):
        if minutes == 0:
            return "0:00"
        h = minutes // 60
        m = minutes % 60
        return f"{h}:{m:02d}"
    
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
    
    # Stampa tabella
    print(f"Totali per periodo - {apt}")
    print("-" * 100)
    print(df_table.to_string(index=False))
    print()
    print()

# Tabella riepilogo finale
print("=" * 100)
print("RIEPILOGO FINALE - TUTTI GLI AEROPORTI")
print("=" * 100)
print()

riep_finale = df.groupby('APT').agg({
    'TOTALE_BLOCCO_EUR': 'sum',
    'TURNO_EUR': 'sum',
    'EXTRA_EUR': 'sum',
    'NOTTE_EUR': 'sum',
    'DURATA_TURNO_MIN': 'sum',
    'EXTRA_MIN': 'sum',
    'NOTTE_MIN': 'sum'
}).round(2)

# Calcola anche minuti per riepilogo
riep_min = df.groupby('APT').agg({
    'DURATA_TURNO_MIN': 'sum',
    'EXTRA_MIN': 'sum',
    'NOTTE_MIN': 'sum'
}).round(0).astype(int)

def format_hmm(minutes):
    if minutes == 0:
        return "0:00"
    h = int(minutes) // 60
    m = int(minutes) % 60
    return f"{h}:{m:02d}"

riep_table = pd.DataFrame({
    'Aeroporto': riep_finale.index,
    'Fasce Orarie': [''] * len(riep_finale.index),  # Vuoto per riepilogo
    'Turno (h:mm)': [format_hmm(riep_min.loc[apt, 'DURATA_TURNO_MIN']) for apt in riep_finale.index],
    'Turno (€)': [f"{x:.2f}".replace('.', ',') for x in riep_finale['TURNO_EUR']],
    'Extra (h:mm)': [format_hmm(riep_min.loc[apt, 'EXTRA_MIN']) for apt in riep_finale.index],
    'Extra (€)': [f"{x:.2f}".replace('.', ',') for x in riep_finale['EXTRA_EUR']],
    'Notturno (h:mm)': [format_hmm(riep_min.loc[apt, 'NOTTE_MIN']) for apt in riep_finale.index],
    'Notturno (€)': [f"{x:.2f}".replace('.', ',') for x in riep_finale['NOTTE_EUR']],
    'TOTALE (€)': [f"{x:.2f}".replace('.', ',') for x in riep_finale['TOTALE_BLOCCO_EUR']]
})

# Aggiungi riga totale generale
totale_generale = df['TOTALE_BLOCCO_EUR'].sum()
tot_turno_gen = df['TURNO_EUR'].sum()
tot_extra_gen = df['EXTRA_EUR'].sum()
tot_notte_gen = df['NOTTE_EUR'].sum()
tot_turno_min_gen = int(df['DURATA_TURNO_MIN'].sum())
tot_extra_min_gen = int(df['EXTRA_MIN'].sum())
tot_notte_min_gen = int(df['NOTTE_MIN'].sum())

riep_table = pd.concat([
    riep_table,
    pd.DataFrame([{
        'Aeroporto': 'TOTALE',
        'Fasce Orarie': '',
        'Turno (h:mm)': format_hmm(tot_turno_min_gen),
        'Turno (€)': f"{tot_turno_gen:.2f}".replace('.', ','),
        'Extra (h:mm)': format_hmm(tot_extra_min_gen),
        'Extra (€)': f"{tot_extra_gen:.2f}".replace('.', ','),
        'Notturno (h:mm)': format_hmm(tot_notte_min_gen),
        'Notturno (€)': f"{tot_notte_gen:.2f}".replace('.', ','),
        'TOTALE (€)': f"{totale_generale:.2f}".replace('.', ',')
    }])
], ignore_index=True)

print(riep_table.to_string(index=False))
print()
print("=" * 100)

