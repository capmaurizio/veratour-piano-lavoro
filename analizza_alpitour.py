#!/usr/bin/env python3
import pandas as pd

file_excel = "OUT_ALPITOUR_DICEMBRE25_ALL.xlsx"

# Leggi tutti i fogli
xls = pd.ExcelFile(file_excel)
print("=" * 80)
print("RIEPILOGO CALCOLI ALPITOUR - DICEMBRE 2025")
print("=" * 80)
print(f"\nFogli presenti: {xls.sheet_names}\n")

# Totali periodo
df_tot = pd.read_excel(file_excel, sheet_name='TotaliPeriodo')
print("TOTALI PER PERIODO:")
print(df_tot.to_string(index=False))
print()

# Dettaglio blocchi
df_det = pd.read_excel(file_excel, sheet_name='DettaglioBlocchi')
print(f"Numero totale blocchi: {len(df_det)}")
print(f"Aeroporti presenti: {sorted(df_det['APT'].unique())}")
print()

# Riepilogo per aeroporto
print("RIEPILOGO PER AEROPORTO:")
riep_apt = df_det.groupby('APT').agg({
    'TOTALE_BLOCCO_EUR': 'sum',
    'TURNO_EUR': 'sum',
    'EXTRA_EUR': 'sum',
    'NOTTE_EUR': 'sum',
    'EXTRA_MIN': 'sum',
    'NOTTE_MIN': 'sum'
}).round(2)
riep_apt.columns = ['TOTALE (€)', 'TURNO (€)', 'EXTRA (€)', 'NOTTE (€)', 'EXTRA (min)', 'NOTTE (min)']
print(riep_apt.to_string())
print()

# Blocchi festivi
festivi = df_det[df_det['FESTIVO'] == True]
print(f"BLOCCHI FESTIVI: {len(festivi)}")
if len(festivi) > 0:
    print(festivi[['DATA', 'APT', 'TURNO_NORMALIZZATO', 'TURNO_EUR', 'EXTRA_EUR', 'TOTALE_BLOCCO_EUR']].to_string(index=False))
    print(f"Totale blocchi festivi: €{festivi['TOTALE_BLOCCO_EUR'].sum():.2f}")
print()

# Assistenti VRN
if 'Assistenti_VRN' in xls.sheet_names:
    df_ass = pd.read_excel(file_excel, sheet_name='Assistenti_VRN')
    print("ASSISTENTI VRN:")
    print(df_ass.to_string(index=False))
    print()
else:
    print("Nessun assistente VRN presente")
    print()

# Discrepanze
if 'Discrepanze' in xls.sheet_names:
    df_disc = pd.read_excel(file_excel, sheet_name='Discrepanze')
    if not df_disc.empty:
        print(f"DISCREPANZE TROVATE: {len(df_disc)}")
        print(df_disc[['DATA', 'APT', 'TURNO_NORMALIZZATO', 'DELTA_EXTRA_MIN', 'DELTA_NOTTE_MIN', 'DELTA_TOTALE_EUR']].head(10).to_string(index=False))
    else:
        print("Nessuna discrepanza trovata")
    print()

print("=" * 80)
print(f"File Excel generato: {file_excel}")
print("=" * 80)

