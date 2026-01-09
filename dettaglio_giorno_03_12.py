#!/usr/bin/env python3
import pandas as pd

file_excel = "OUT_ALPITOUR_DICEMBRE25_ALL.xlsx"

# Leggi dettaglio blocchi
df = pd.read_excel(file_excel, sheet_name='DettaglioBlocchi')

# Converti DATA in datetime
df['DATA_DT'] = pd.to_datetime(df['DATA'], dayfirst=True)

# Filtra solo 03/12/2025
data_target = pd.to_datetime('03/12/2025', dayfirst=True)
df_giorno = df[df['DATA_DT'] == data_target].copy()

print("=" * 100)
print("DETTAGLIO COMPLETO - 03 DICEMBRE 2025")
print("=" * 100)
print()

if df_giorno.empty:
    print("Nessun dato trovato per il 03/12/2025")
else:
    # Ordina per aeroporto
    df_giorno = df_giorno.sort_values(['APT', 'TURNO_NORMALIZZATO'])
    
    for apt in sorted(df_giorno['APT'].unique()):
        df_apt = df_giorno[df_giorno['APT'] == apt].copy()
        
        print("=" * 100)
        print(f"AEROPORTO: {apt}")
        print("=" * 100)
        print()
        
        for idx, row in df_apt.iterrows():
            print(f"📋 BLOCCO {idx + 1}")
            print("-" * 100)
            print(f"  Turno normalizzato: {row['TURNO_NORMALIZZATO']}")
            print(f"  Turno originale: {row['TURNO_FFILL']}")
            
            if pd.notna(row['ASSISTENTE']) and str(row['ASSISTENTE']).strip():
                print(f"  Assistente: {row['ASSISTENTE']}")
            
            # Fasce orarie
            inizio_dt = pd.to_datetime(row['INIZIO_DT'])
            fine_dt = pd.to_datetime(row['FINE_DT'])
            print(f"  Inizio turno: {inizio_dt.strftime('%d/%m/%Y %H:%M')}")
            print(f"  Fine turno: {fine_dt.strftime('%d/%m/%Y %H:%M')}")
            print(f"  Durata turno: {row['DURATA_TURNO_MIN']} minuti ({row['DURATA_TURNO_MIN']//60}h {row['DURATA_TURNO_MIN']%60}min)")
            
            # ATD selezionato
            if pd.notna(row['ATD_SCELTO']):
                atd = pd.to_datetime(row['ATD_SCELTO'])
                print(f"  ATD selezionato: {atd.strftime('%d/%m/%Y %H:%M')}")
            else:
                print(f"  ATD selezionato: Non disponibile")
            
            # NO DEC
            if row['NO_DEC']:
                print(f"  ⚠️  NO DEC: Sì (extra forzato a 0)")
            
            # Calcoli
            print()
            print(f"  💰 CALCOLI:")
            print(f"     Turno: €{row['TURNO_EUR']:.2f}")
            
            if row['EXTRA_MIN'] > 0:
                print(f"     Extra: {row['EXTRA_MIN']} minuti ({row['EXTRA_H:MM']}) = €{row['EXTRA_EUR']:.2f}")
                if pd.notna(row['EXTRA_MIN_RAW']):
                    print(f"       (Raw: {int(row['EXTRA_MIN_RAW'])} minuti, arrotondato a {row['EXTRA_MIN']} minuti)")
            else:
                print(f"     Extra: 0 minuti = €0,00")
            
            if row['NOTTE_MIN'] > 0:
                print(f"     Notturno: {row['NOTTE_MIN']} minuti = €{row['NOTTE_EUR']:.2f}")
                if pd.notna(row['NOTTE_MIN_RAW']):
                    print(f"       (Raw: {int(row['NOTTE_MIN_RAW'])} minuti)")
            else:
                print(f"     Notturno: 0 minuti = €0,00")
            
            if row['FESTIVO']:
                print(f"     ⭐ Festivo: +20% su turno e extra")
            
            print(f"     TOTALE BLOCCO: €{row['TOTALE_BLOCCO_EUR']:.2f}")
            print()
        
        # Totale giornaliero aeroporto
        tot_turno = df_apt['TURNO_EUR'].sum()
        tot_extra = df_apt['EXTRA_EUR'].sum()
        tot_notte = df_apt['NOTTE_EUR'].sum()
        tot_giorno = df_apt['TOTALE_BLOCCO_EUR'].sum()
        tot_turno_min = int(df_apt['DURATA_TURNO_MIN'].sum())
        tot_extra_min = int(df_apt['EXTRA_MIN'].sum())
        tot_notte_min = int(df_apt['NOTTE_MIN'].sum())
        
        print("=" * 100)
        print(f"💰 TOTALE GIORNO {apt} - 03/12/2025:")
        print(f"   Turno: {tot_turno_min//60}h {tot_turno_min%60}min ({tot_turno_min} minuti) = €{tot_turno:.2f}")
        print(f"   Extra: {tot_extra_min//60}h {tot_extra_min%60}min ({tot_extra_min} minuti) = €{tot_extra:.2f}")
        print(f"   Notturno: {tot_notte_min//60}h {tot_notte_min%60}min ({tot_notte_min} minuti) = €{tot_notte:.2f}")
        print(f"   TOTALE: €{tot_giorno:.2f}")
        print("=" * 100)
        print()
        print()

# Totale generale del giorno
print("=" * 100)
print("RIEPILOGO TOTALE GIORNO 03/12/2025")
print("=" * 100)
tot_turno_gen = df_giorno['TURNO_EUR'].sum()
tot_extra_gen = df_giorno['EXTRA_EUR'].sum()
tot_notte_gen = df_giorno['NOTTE_EUR'].sum()
tot_giorno_gen = df_giorno['TOTALE_BLOCCO_EUR'].sum()
tot_turno_min_gen = int(df_giorno['DURATA_TURNO_MIN'].sum())
tot_extra_min_gen = int(df_giorno['EXTRA_MIN'].sum())
tot_notte_min_gen = int(df_giorno['NOTTE_MIN'].sum())

print(f"Turno totale: {tot_turno_min_gen//60}h {tot_turno_min_gen%60}min = €{tot_turno_gen:.2f}")
print(f"Extra totale: {tot_extra_min_gen//60}h {tot_extra_min_gen%60}min = €{tot_extra_gen:.2f}")
print(f"Notturno totale: {tot_notte_min_gen//60}h {tot_notte_min_gen%60}min = €{tot_notte_gen:.2f}")
print(f"TOTALE GIORNO: €{tot_giorno_gen:.2f}")
print("=" * 100)

