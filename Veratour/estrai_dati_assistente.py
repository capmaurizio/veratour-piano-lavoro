#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per estrarre dati giorno per giorno di un assistente
"""

import sys
import pandas as pd
from consuntivoveratour import process_files, CalcConfig, RoundingPolicy

def estrai_dati_assistente(file_excel: str, nome_assistente: str, apt: str = "VRN"):
    """Estrae i dati giorno per giorno per un assistente"""
    
    cfg = CalcConfig(
        apt_filter=[apt],
        night_mode="DIFF5",
        rounding_extra=RoundingPolicy("NONE", 5),
        rounding_night=RoundingPolicy("NONE", 5),
        holiday_dates=None,
    )
    
    detail_df, totals_df, discr_df = process_files([file_excel], cfg)
    
    if detail_df.empty:
        print("Nessun dato trovato")
        return
    
    # Filtra per assistente
    if 'ASSISTENTE' not in detail_df.columns:
        print("Colonna ASSISTENTE non trovata")
        return
    
    df_assistente = detail_df[
        (detail_df['ASSISTENTE'].str.contains(nome_assistente, case=False, na=False)) &
        (detail_df['APT'] == apt)
    ].copy()
    
    if df_assistente.empty:
        print(f"Nessun dato trovato per assistente '{nome_assistente}' in {apt}")
        return
    
    df_assistente = df_assistente.sort_values('DATA')
    
    print(f"\n{'='*100}")
    print(f"DATI GIORNO PER GIORNO - {nome_assistente.upper()} - {apt}")
    print(f"{'='*100}\n")
    
    # Header
    print(f"{'Data':<12} {'Turno':<20} {'Durata':<10} {'Turno (€)':<12} {'Extra':<10} {'Extra (€)':<12} {'Notturno':<12} {'Notturno (€)':<12} {'Festivo':<8} {'TOTALE (€)':<12}")
    print("-" * 100)
    
    # Dati
    for _, row in df_assistente.iterrows():
        data = row['DATA']
        turno = str(row['TURNO_NORMALIZZATO'])[:18]
        durata_min = int(row['DURATA_TURNO_MIN'])
        durata_str = f"{durata_min//60}:{durata_min%60:02d}"
        turno_eur = f"{row['TURNO_EUR']:.2f}€"
        extra_hmm = str(row.get('EXTRA_H:MM', '0:00'))
        extra_eur = f"{row['EXTRA_EUR']:.2f}€"
        notte_min = int(row['NOTTE_MIN'])
        notte_str = f"{notte_min//60}:{notte_min%60:02d}"
        notte_eur = f"{row['NOTTE_EUR']:.2f}€"
        festivo = "Sì" if row['FESTIVO'] else "No"
        totale = f"{row['TOTALE_BLOCCO_EUR']:.2f}€"
        
        print(f"{data:<12} {turno:<20} {durata_str:<10} {turno_eur:<12} {extra_hmm:<10} {extra_eur:<12} {notte_str:<12} {notte_eur:<12} {festivo:<8} {totale:<12}")
    
    # Totali
    print("-" * 100)
    print(f"{'TOTALE':<12} {'':<20} {'':<10} {df_assistente['TURNO_EUR'].sum():>10.2f}€ {'':<10} {df_assistente['EXTRA_EUR'].sum():>10.2f}€ {'':<12} {df_assistente['NOTTE_EUR'].sum():>10.2f}€ {'':<8} {df_assistente['TOTALE_BLOCCO_EUR'].sum():>10.2f}€")
    print(f"\nBlocchi totali: {len(df_assistente)}")
    print(f"Totale Extra (min): {int(df_assistente['EXTRA_MIN'].sum())} = {int(df_assistente['EXTRA_MIN'].sum())//60}h {int(df_assistente['EXTRA_MIN'].sum())%60}min")
    print(f"Totale Notturno (min): {int(df_assistente['NOTTE_MIN'].sum())} = {int(df_assistente['NOTTE_MIN'].sum())//60}h {int(df_assistente['NOTTE_MIN'].sum())%60}min")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python estrai_dati_assistente.py <file_excel> <nome_assistente> [apt]")
        print("Esempio: python estrai_dati_assistente.py 'Piano lavoro DICEMBRE 25.xlsx' Manu VRN")
        sys.exit(1)
    
    file_excel = sys.argv[1]
    nome_assistente = sys.argv[2]
    apt = sys.argv[3] if len(sys.argv) > 3 else "VRN"
    
    estrai_dati_assistente(file_excel, nome_assistente, apt)


