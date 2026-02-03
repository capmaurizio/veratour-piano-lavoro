#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnosi foglio PIANO VOLI: verifica perché i blocchi non vengono elaborati.
Uso: python diagnosi_piano_voli.py [percorso_file.xlsx]
Se non passi il percorso, cerca *.xlsx nella cartella corrente.
"""
import re
import sys
from pathlib import Path

import pandas as pd


def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_spaces(str(c)).upper() for c in df.columns]
    return df


def find_col(df: pd.DataFrame, patterns: list) -> str | None:
    cols = list(df.columns)
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for c in cols:
            if rx.search(c):
                return c
    return None


def detect_columns(df: pd.DataFrame) -> dict:
    """Stessa logica di Alpitour/consuntivoalpitour.py"""
    return {
        "data": find_col(df, [r"^DATA$", r"\bDATE\b"]),
        "tour_operator": find_col(df, [r"TOUR\s*OPERATOR", r"^TO$", r"\bOPERATORE\b"]),
        "apt": find_col(df, [r"^APT$", r"\bAEROPORTO\b", r"\bSCALO\b"]),
        "turno": find_col(df, [r"^TURNO$", r"^TURNO\s*ASSISTENTE$", r"\bTURNI\b"]),
        "atd": find_col(df, [r"^ATD$", r"\bORARIO\s*ATD\b"]),
        "std": find_col(df, [r"^STD$", r"\bORARIO\s*STD\b"]),
    }


def main():
    if len(sys.argv) >= 2:
        path = Path(sys.argv[1])
    else:
        xlsx = list(Path(".").glob("*.xlsx"))
        # Escludi output temporanei
        xlsx = [p for p in xlsx if not p.name.startswith("OUT_") and "TEMP" not in p.name]
        if not xlsx:
            print("Nessun file .xlsx nella cartella corrente.")
            print("Uso: python diagnosi_piano_voli.py <percorso_file.xlsx>")
            sys.exit(1)
        path = xlsx[0]
        print(f"Usato file: {path}\n")

    if not path.exists():
        print(f"File non trovato: {path}")
        sys.exit(1)

    print("=" * 60)
    print("DIAGNOSI PIANO VOLI")
    print("=" * 60)
    xls = pd.ExcelFile(path)
    print(f"\nFogli nel file: {xls.sheet_names}")

    # Cerca PIANO VOLI
    target = None
    for sh in xls.sheet_names:
        if sh.upper().strip() == "PIANO VOLI":
            target = sh
            break
    if target:
        print(f"\nTrovato foglio 'PIANO VOLI' (nome esatto: '{target}')")
        sheets_to_read = [target]
    else:
        print("\nNessun foglio chiamato 'PIANO VOLI'. Verranno letti tutti i fogli.")
        sheets_to_read = xls.sheet_names

    for sheet_name in sheets_to_read:
        print(f"\n--- Foglio: {sheet_name!r} ---")
        df0 = pd.read_excel(path, sheet_name=sheet_name)
        if df0 is None or df0.empty:
            print("  (vuoto o nessun dato)")
            continue
        print(f"  Righe: {len(df0)}, Colonne: {len(df0.columns)}")
        print(f"  Nomi colonne (prima della normalizzazione): {list(df0.columns)}")

        df = normalize_cols(df0)
        print(f"  Nomi colonne (dopo normalizzazione .upper()): {list(df.columns)}")

        cols = detect_columns(df)
        print("\n  Colonne richieste per il calcolo:")
        for key, val in cols.items():
            status = "OK" if val else "MANCANTE"
            print(f"    {key}: {repr(val)} [{status}]")

        if not cols["data"] or not cols["apt"] or not cols["turno"]:
            print("\n  >>> MOTIVO 0 BLOCCHI: manca almeno una colonna obbligatoria (DATA, APT, TURNO).")
            print("     I moduli saltano il foglio se DATA, APT o TURNO non vengono riconosciuti.")
        else:
            # Conta righe con dati
            to_col = cols["tour_operator"]
            if to_col:
                non_empty = df[to_col].dropna().astype(str).str.strip()
                non_empty = non_empty[(non_empty != "") & (non_empty.str.lower() != "nan")]
                unique_to = non_empty.unique()
                print(f"\n  Valori unici in TOUR OPERATOR: {list(unique_to)[:20]}{'...' if len(unique_to) > 20 else ''}")
            print("\n  Prime 3 righe (colonne rilevate):")
            show_cols = [c for c in [cols["data"], cols["tour_operator"], cols["apt"], cols["turno"]] if c]
            if show_cols:
                print(df[show_cols].head(3).to_string())

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
