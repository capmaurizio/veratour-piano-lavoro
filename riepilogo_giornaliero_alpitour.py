#!/usr/bin/env python3
import pandas as pd

file_excel = "OUT_ALPITOUR_DICEMBRE25_ALL.xlsx"

# Leggi dettaglio blocchi
df = pd.read_excel(file_excel, sheet_name='DettaglioBlocchi')

# Converti DATA in datetime per ordinamento
df['DATA_DT'] = pd.to_datetime(df['DATA'], dayfirst=True)

# Ordina per data e aeroporto
df = df.sort_values(['DATA_DT', 'APT', 'TURNO_NORMALIZZATO'])

print("=" * 100)
print("CALCOLO GIORNO PER GIORNO - ALPITOUR DICEMBRE 2025")
print("=" * 100)
print()

# Raggruppa per data e aeroporto
for apt in sorted(df['APT'].unique()):
    df_apt = df[df['APT'] == apt].copy()
    
    print("=" * 100)
    print(f"AEROPORTO: {apt}")
    print("=" * 100)
    print()
    
    # Raggruppa per data
    for data_dt, group in df_apt.groupby('DATA_DT'):
        data_str = data_dt.strftime('%d/%m/%Y')
        giorno_settimana = data_dt.strftime('%A')
        
        # Verifica se è festivo
        is_festivo = group['FESTIVO'].iloc[0] if len(group) > 0 else False
        festivo_mark = " [FESTIVO]" if is_festivo else ""
        
        print(f"📅 {data_str} ({giorno_settimana}){festivo_mark}")
        print("-" * 100)
        
        # Mostra ogni blocco del giorno
        for idx, row in group.iterrows():
            print(f"  Turno: {row['TURNO_NORMALIZZATO']}")
            if pd.notna(row['ASSISTENTE']) and str(row['ASSISTENTE']).strip():
                print(f"    Assistente: {row['ASSISTENTE']}")
            print(f"    Turno €: {row['TURNO_EUR']:.2f}")
            if row['EXTRA_MIN'] > 0:
                print(f"    Extra: {row['EXTRA_MIN']} min ({row['EXTRA_H:MM']}) = €{row['EXTRA_EUR']:.2f}")
            if row['NOTTE_MIN'] > 0:
                print(f"    Notturno: {row['NOTTE_MIN']} min = €{row['NOTTE_EUR']:.2f}")
            print(f"    TOTALE: €{row['TOTALE_BLOCCO_EUR']:.2f}")
            print()
        
        # Totale giornaliero
        tot_giorno = group['TOTALE_BLOCCO_EUR'].sum()
        tot_turno = group['TURNO_EUR'].sum()
        tot_extra = group['EXTRA_EUR'].sum()
        tot_notte = group['NOTTE_EUR'].sum()
        tot_extra_min = group['EXTRA_MIN'].sum()
        tot_notte_min = group['NOTTE_MIN'].sum()
        
        print(f"  💰 TOTALE GIORNO {apt}:")
        print(f"     Turno: €{tot_turno:.2f}")
        print(f"     Extra: {tot_extra_min} min = €{tot_extra:.2f}")
        print(f"     Notturno: {tot_notte_min} min = €{tot_notte:.2f}")
        print(f"     TOTALE: €{tot_giorno:.2f}")
        print()
    
    # Totale aeroporto
    tot_apt = df_apt['TOTALE_BLOCCO_EUR'].sum()
    tot_turno_apt = df_apt['TURNO_EUR'].sum()
    tot_extra_apt = df_apt['EXTRA_EUR'].sum()
    tot_notte_apt = df_apt['NOTTE_EUR'].sum()
    tot_extra_min_apt = df_apt['EXTRA_MIN'].sum()
    tot_notte_min_apt = df_apt['NOTTE_MIN'].sum()
    num_blocchi = len(df_apt)
    
    print("=" * 100)
    print(f"📊 TOTALE {apt} (Dicembre 2025):")
    print(f"   Blocchi: {num_blocchi}")
    print(f"   Turno: €{tot_turno_apt:.2f}")
    print(f"   Extra: {tot_extra_min_apt} min ({tot_extra_min_apt//60}h {tot_extra_min_apt%60}min) = €{tot_extra_apt:.2f}")
    print(f"   Notturno: {tot_notte_min_apt} min ({tot_notte_min_apt//60}h {tot_notte_min_apt%60}min) = €{tot_notte_apt:.2f}")
    print(f"   TOTALE: €{tot_apt:.2f}")
    print("=" * 100)
    print()
    print()

# Riepilogo finale
print("=" * 100)
print("RIEPILOGO FINALE - TUTTI GLI AEROPORTI")
print("=" * 100)
riep_finale = df.groupby('APT').agg({
    'TOTALE_BLOCCO_EUR': 'sum',
    'TURNO_EUR': 'sum',
    'EXTRA_EUR': 'sum',
    'NOTTE_EUR': 'sum',
    'EXTRA_MIN': 'sum',
    'NOTTE_MIN': 'sum'
}).round(2)
riep_finale.columns = ['TOTALE (€)', 'TURNO (€)', 'EXTRA (€)', 'NOTTE (€)', 'EXTRA (min)', 'NOTTE (min)']
print(riep_finale.to_string())
print()

totale_generale = df['TOTALE_BLOCCO_EUR'].sum()
print(f"TOTALE GENERALE: €{totale_generale:.2f}")
print("=" * 100)

