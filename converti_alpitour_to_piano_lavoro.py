#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script isolato per convertire file Alpitour in formato Piano Lavoro
Legge file .xls/.xlsx di Alpitour e genera un file Excel "Piano Lavoro" compatibile

REQUISITI:
- pandas
- openpyxl (per file .xlsx)
- xlrd (per file .xls) - installare con: pip install xlrd

USO:
    python3 converti_alpitour_to_piano_lavoro.py [file_input] [file_output]
    
ESEMPIO:
    python3 converti_alpitour_to_piano_lavoro.py "VERONA DAL 12 AL 18 GEN 2026 (1).xls"
"""

import pandas as pd
import re
import sys
import os
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

def normalize_col_name(col: str) -> str:
    """Normalizza nome colonna per matching"""
    return str(col).strip().upper().replace("_", " ").replace("-", " ")


def find_column(df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
    """Trova colonna che corrisponde a uno dei pattern"""
    cols_normalized = {normalize_col_name(c): c for c in df.columns}
    
    for pattern in patterns:
        pattern_upper = pattern.upper().strip()
        # Match esatto
        if pattern_upper in cols_normalized:
            return cols_normalized[pattern_upper]
        # Match parziale
        for col_norm, col_orig in cols_normalized.items():
            if pattern_upper in col_norm or col_norm in pattern_upper:
                return col_orig
        # Match regex
        try:
            rx = re.compile(pattern, re.IGNORECASE)
            for col_norm, col_orig in cols_normalized.items():
                if rx.search(col_norm):
                    return col_orig
        except:
            pass
    
    return None


def detect_columns_alpitour(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Rileva colonne nel file Alpitour con pattern flessibili"""
    cols = {
        "data": find_column(df, [
            r"^DATA$", r"^DATE$", r"GIORNO", r"DATA\s*VOLO", r"DATA\s*SERVIZIO",
            r"DATA\s*ASSISTENZA", r"^D$"
        ]),
        "tour_operator": find_column(df, [
            r"TOUR\s*OPERATOR", r"^TO$", r"OPERATORE", r"TOUR\s*OP", r"CLIENTE"
        ]),
        "apt": find_column(df, [
            r"^APT$", r"AEROPORTO", r"SCALO", r"AEROPORTO\s*DI", r"^A$"
        ]),
        "turno": find_column(df, [
            r"^TURNO$", r"TURNO\s*ASSISTENTE", r"TURNI", r"ORARIO\s*TURNO",
            r"FASCIA\s*ORARIA", r"ORARIO", r"FASCIA"
        ]),
        "turno_dalle": find_column(df, [
            r"^DALLE$", r"^DALLE\s*ORE$", r"INIZIO", r"ORA\s*INIZIO"
        ]),
        "turno_alle": find_column(df, [
            r"^ALLE$", r"^ALLE\s*ORE$", r"FINE", r"ORA\s*FINE"
        ]),
        "atd": find_column(df, [
            r"^ATD$", r"ORARIO\s*ATD", r"DECOLLO\s*EFFETTIVO", r"ATD\s*EFFETTIVO",
            r"DECOLLO", r"PARTENZA\s*EFFETTIVA"
        ]),
        "std": find_column(df, [
            r"^STD$", r"ORARIO\s*STD", r"DECOLLO\s*PROGRAMMATO", r"STD\s*PROGRAMMATO",
            r"PARTENZA\s*PROGRAMMATA", r"ORARIO\s*PROGRAMMATO"
        ]),
        "assistente": find_column(df, [
            r"^ASSISTENTE$", r"ASSISTENTI", r"NOME\s*ASSISTENTE", r"OPERATORE"
        ]),
    }
    
    # Cerca colonne "dalle" e "alle" anche se hanno nomi generici
    # Controlla se ci sono colonne con valori "dalle" o "alle" nella prima riga
    if not cols["turno_dalle"] or not cols["turno_alle"]:
        for col in df.columns:
            col_str = str(col).upper()
            # Controlla se nella colonna ci sono valori che sembrano orari di inizio/fine
            if df[col].dtype == 'object':
                sample_values = df[col].dropna().head(10).astype(str)
                # Cerca pattern orari (HH:MM o HH.MM)
                has_time_pattern = sample_values.str.match(r'^\d{1,2}[.:]\d{2}$').any()
                if has_time_pattern and not cols["turno_dalle"]:
                    # Verifica se è "dalle" guardando la posizione (di solito prima di "alle")
                    cols["turno_dalle"] = col
                elif has_time_pattern and not cols["turno_alle"]:
                    cols["turno_alle"] = col
    
    return cols


def extract_apt_from_filename(filename: str) -> Optional[str]:
    """Estrae codice aeroporto dal nome file"""
    filename_upper = filename.upper()
    
    # Mapping aeroporti
    apt_map = {
        "VERONA": "VRN",
        "VRN": "VRN",
        "BERGAMO": "BGY",
        "BGY": "BGY",
        "NAPOLI": "NAP",
        "NAP": "NAP",
        "VENEZIA": "VCE",
        "VCE": "VCE",
        "VENEZIA MARCO POLO": "VCE",
    }
    
    for key, apt in apt_map.items():
        if key in filename_upper:
            return apt
    
    return None


def normalize_apt(apt_value: str, filename: str = "") -> str:
    """Normalizza codice aeroporto"""
    if pd.isna(apt_value) or str(apt_value).strip() == "":
        # Prova a estrarre dal filename
        apt_from_file = extract_apt_from_filename(filename)
        if apt_from_file:
            return apt_from_file
        return ""
    
    apt_str = str(apt_value).strip().upper()
    
    # Mapping
    apt_map = {
        "VERONA": "VRN",
        "VRN": "VRN",
        "BERGAMO": "BGY",
        "BGY": "BGY",
        "NAPOLI": "NAP",
        "NAP": "NAP",
        "VENEZIA": "VCE",
        "VCE": "VCE",
        "VENEZIA MARCO POLO": "VCE",
    }
    
    return apt_map.get(apt_str, apt_str)


def parse_date(value) -> Optional[str]:
    """Converte data in formato standard"""
    if pd.isna(value):
        return None
    
    # Se è già una data
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.strftime("%d/%m/%Y")
    
    value_str = str(value).strip()
    if not value_str or value_str.lower() in ["nan", "none", ""]:
        return None
    
    # Prova vari formati
    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d/%m/%y",
        "%d-%m-%y",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(value_str, fmt)
            return dt.strftime("%d/%m/%Y")
        except:
            continue
    
    # Se non riesce, prova con pandas
    try:
        dt = pd.to_datetime(value_str, dayfirst=True)
        return dt.strftime("%d/%m/%Y")
    except:
        pass
    
    return value_str  # Ritorna come stringa se non riesce a parsare


def normalize_turno(turno_value) -> str:
    """Normalizza formato turno"""
    if pd.isna(turno_value):
        return ""
    
    turno_str = str(turno_value).strip()
    if not turno_str or turno_str.lower() in ["nan", "none"]:
        return ""
    
    # Rimuovi spazi multipli
    turno_str = re.sub(r"\s+", " ", turno_str)
    
    return turno_str


def normalize_time(time_value) -> Optional[str]:
    """Normalizza formato orario (HH:MM)"""
    if pd.isna(time_value):
        return None
    
    # Se è già un time
    if isinstance(time_value, (pd.Timestamp, datetime)):
        return time_value.strftime("%H:%M")
    
    time_str = str(time_value).strip()
    if not time_str or time_str.lower() in ["nan", "none", ""]:
        return None
    
    # Rimuovi spazi
    time_str = time_str.replace(" ", "")
    
    # Prova vari formati
    # HH:MM
    if re.match(r"^\d{1,2}:\d{2}$", time_str):
        parts = time_str.split(":")
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    
    # HH.MM
    if re.match(r"^\d{1,2}\.\d{2}$", time_str):
        parts = time_str.split(".")
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}"
    
    # HHMM
    if re.match(r"^\d{3,4}$", time_str):
        if len(time_str) == 3:
            time_str = "0" + time_str
        return f"{time_str[:2]}:{time_str[2:]}"
    
    # Prova con pandas
    try:
        dt = pd.to_datetime(time_str, format="%H:%M")
        return dt.strftime("%H:%M")
    except:
        try:
            dt = pd.to_datetime(time_str)
            return dt.strftime("%H:%M")
        except:
            pass
    
    return time_str  # Ritorna come stringa se non riesce


def convert_alpitour_to_piano_lavoro(input_file: str, output_file: str = None) -> str:
    """
    Converte file Alpitour in formato Piano Lavoro
    
    Args:
        input_file: Path al file .xls/.xlsx di Alpitour
        output_file: Path al file Excel di output (opzionale)
    
    Returns:
        Path al file generato
    """
    print(f"📄 Leggendo file: {input_file}")
    
    # Determina output file
    if output_file is None:
        input_path = Path(input_file)
        output_file = str(input_path.parent / f"Piano_Lavoro_{input_path.stem}.xlsx")
    
    # Prova a leggere con diversi engine
    df_list = []
    try:
        # Prova prima con xlrd per .xls
        if input_file.endswith('.xls'):
            try:
                xls = pd.ExcelFile(input_file, engine='xlrd')
                print("  ✅ File .xls letto con xlrd")
            except ImportError:
                print("  ⚠️  xlrd non installato. Installare con: pip install xlrd")
                print("  💡 Tentativo conversione in .xlsx...")
                # Prova a convertire usando LibreOffice o altro metodo
                raise ImportError("xlrd necessario per file .xls. Installare con: pip install xlrd")
            except Exception as e:
                print(f"  ⚠️  Errore leggendo .xls: {e}")
                # Prova con openpyxl come ultimo tentativo
                try:
                    xls = pd.ExcelFile(input_file, engine='openpyxl')
                    print("  ✅ File .xls letto con openpyxl")
                except:
                    raise ValueError(f"Impossibile leggere file .xls. Installare xlrd: pip install xlrd")
        else:
            xls = pd.ExcelFile(input_file, engine='openpyxl')
        
        print(f"📋 Fogli trovati: {xls.sheet_names}")
        
        # Processa ogni foglio
        for sheet_name in xls.sheet_names:
            print(f"  📊 Elaborando foglio: {sheet_name}")
            
            try:
                # Cerca la riga con l'header (contiene "DATA")
                header_row = None
                max_rows_to_check = 20
                
                for skip in range(max_rows_to_check):
                    try:
                        df_test = pd.read_excel(input_file, sheet_name=sheet_name, 
                                                engine='xlrd' if input_file.endswith('.xls') else 'openpyxl',
                                                header=None, nrows=1, skiprows=skip)
                        first_row_values = [str(v).upper().strip() for v in df_test.iloc[0].values if pd.notna(v)]
                        if any('DATA' in v for v in first_row_values):
                            header_row = skip
                            print(f"    ✅ Header trovato alla riga {skip + 1}")
                            break
                    except:
                        continue
                
                # Leggi il file: usa header_row per DATA, ma cerca anche "dalle"/"alle" nella riga successiva
                if header_row is not None:
                    # Leggi con header alla riga trovata (di solito contiene "DATA")
                    if input_file.endswith('.xls'):
                        try:
                            df = pd.read_excel(input_file, sheet_name=sheet_name, engine='xlrd', header=header_row)
                        except:
                            df = pd.read_excel(input_file, sheet_name=sheet_name, engine='openpyxl', header=header_row)
                    else:
                        df = pd.read_excel(input_file, sheet_name=sheet_name, engine='openpyxl', header=header_row)
                    
                    # Se non trova "dalle"/"alle", prova a cercare nella riga successiva
                    if not any('dalle' in str(c).lower() or 'alle' in str(c).lower() for c in df.columns):
                        # Leggi anche la riga successiva per vedere se ci sono "dalle"/"alle"
                        try:
                            df_next = pd.read_excel(input_file, sheet_name=sheet_name, 
                                                   engine='xlrd' if input_file.endswith('.xls') else 'openpyxl',
                                                   header=None, nrows=1, skiprows=header_row+1)
                            next_row = df_next.iloc[0].values
                            # Cerca colonne con "dalle" o "alle"
                            for idx, val in enumerate(next_row):
                                val_str = str(val).lower().strip() if pd.notna(val) else ""
                                if val_str in ['dalle', 'alle']:
                                    # Usa questa colonna
                                    col_name = f"Unnamed: {idx}" if f"Unnamed: {idx}" in df.columns else df.columns[idx]
                                    if val_str == 'dalle' and 'turno_dalle' not in locals():
                                        df = df.rename(columns={col_name: 'DALLE'})
                                    elif val_str == 'alle':
                                        df = df.rename(columns={col_name: 'ALLE'})
                        except:
                            pass
                else:
                    # Fallback: leggi normalmente
                    print(f"    ⚠️  Header non trovato, uso prima riga")
                    if input_file.endswith('.xls'):
                        try:
                            df = pd.read_excel(input_file, sheet_name=sheet_name, engine='xlrd')
                        except:
                            df = pd.read_excel(input_file, sheet_name=sheet_name, engine='openpyxl')
                    else:
                        df = pd.read_excel(input_file, sheet_name=sheet_name, engine='openpyxl')
                
                if df.empty:
                    print(f"    ⚠️  Foglio vuoto, saltato")
                    continue
                
                # Rileva colonne
                cols = detect_columns_alpitour(df)
                
                print(f"    Colonne rilevate:")
                for key, col_name in cols.items():
                    if col_name:
                        print(f"      ✅ {key}: {col_name}")
                    else:
                        print(f"      ❌ {key}: NON TROVATA")
                
                # Verifica colonne minime
                if not cols["data"]:
                    print(f"    ⚠️  Colonna DATA non trovata, saltato")
                    continue
                
                # Crea DataFrame Piano Lavoro
                piano_lavoro_rows = []
                
                for idx, row in df.iterrows():
                    # DATA
                    data_val = parse_date(row[cols["data"]]) if cols["data"] else None
                    if not data_val:
                        continue  # Salta righe senza data
                    
                    # APT
                    apt_val = ""
                    if cols["apt"]:
                        apt_val = normalize_apt(row[cols["apt"]], input_file)
                    else:
                        # Estrai dal filename
                        apt_val = extract_apt_from_filename(input_file) or ""
                    
                    # TOUR OPERATOR
                    to_val = "Alpitour"
                    if cols["tour_operator"]:
                        to_raw = str(row[cols["tour_operator"]]).strip()
                        if to_raw and to_raw.lower() not in ["nan", "none", ""]:
                            to_val = to_raw
                    
                    # TURNO - costruisci da "dalle" e "alle" se disponibili
                    turno_val = ""
                    if cols["turno"]:
                        turno_val = normalize_turno(row[cols["turno"]])
                    elif cols["turno_dalle"] and cols["turno_alle"]:
                        # Costruisci turno da "dalle" e "alle"
                        dalle_val = normalize_time(row[cols["turno_dalle"]])
                        alle_val = normalize_time(row[cols["turno_alle"]])
                        if dalle_val and alle_val:
                            turno_val = f"{dalle_val}-{alle_val}"
                        elif dalle_val:
                            turno_val = dalle_val
                    elif cols["turno_dalle"]:
                        dalle_val = normalize_time(row[cols["turno_dalle"]])
                        if dalle_val:
                            turno_val = dalle_val
                    
                    # ATD
                    atd_val = None
                    if cols["atd"]:
                        atd_val = normalize_time(row[cols["atd"]])
                    
                    # STD
                    std_val = None
                    if cols["std"]:
                        std_val = normalize_time(row[cols["std"]])
                    
                    # ASSISTENTE
                    assistente_val = ""
                    if cols["assistente"]:
                        assistente_raw = str(row[cols["assistente"]]).strip()
                        if assistente_raw and assistente_raw.lower() not in ["nan", "none", ""]:
                            assistente_val = assistente_raw
                    
                    # Crea riga Piano Lavoro
                    piano_row = {
                        "DATA": data_val,
                        "TOUR OPERATOR": to_val,
                        "APT": apt_val,
                        "TURNO": turno_val,
                    }
                    
                    if atd_val:
                        piano_row["ATD"] = atd_val
                    
                    if std_val:
                        piano_row["STD"] = std_val
                    
                    if assistente_val:
                        piano_row["ASSISTENTE"] = assistente_val
                    
                    piano_lavoro_rows.append(piano_row)
                
                if piano_lavoro_rows:
                    df_piano = pd.DataFrame(piano_lavoro_rows)
                    df_list.append(df_piano)
                    print(f"    ✅ {len(piano_lavoro_rows)} righe convertite")
                else:
                    print(f"    ⚠️  Nessuna riga valida trovata")
            
            except Exception as e:
                print(f"    ❌ Errore elaborando foglio {sheet_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Combina tutti i fogli
        if not df_list:
            raise ValueError("Nessun dato valido trovato nel file")
        
        df_final = pd.concat(df_list, ignore_index=True)
        
        # Ordina per data
        df_final = df_final.sort_values("DATA")
        
        print(f"\n✅ Totale righe convertite: {len(df_final)}")
        
        # Salva file Excel
        print(f"💾 Salvando file: {output_file}")
        df_final.to_excel(output_file, index=False, engine='openpyxl')
        
        print(f"✅ File generato con successo: {output_file}")
        print(f"\n📊 Riepilogo:")
        print(f"   - Righe totali: {len(df_final)}")
        print(f"   - Date: {df_final['DATA'].nunique()}")
        print(f"   - Aeroporti: {df_final['APT'].unique().tolist()}")
        
        return output_file
    
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # Verifica dipendenze
    try:
        import pandas as pd
    except ImportError:
        print("❌ pandas non installato. Installare con: pip install pandas")
        sys.exit(1)
    
    try:
        import openpyxl
    except ImportError:
        print("❌ openpyxl non installato. Installare con: pip install openpyxl")
        sys.exit(1)
    
    # File di input
    input_file = "Alpitour/comeArrivanoiTurni/gennaio2026/VERONA DAL 12 AL 18 GEN 2026 (1).xls"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    elif len(sys.argv) == 1:
        print("ℹ️  Uso: python3 converti_alpitour_to_piano_lavoro.py [file_input] [file_output]")
        print(f"   Usando file di default: {input_file}")
        print()
    
    if not os.path.exists(input_file):
        print(f"❌ File non trovato: {input_file}")
        print(f"   Verifica il percorso del file")
        sys.exit(1)
    
    # Verifica se serve xlrd per file .xls
    if input_file.endswith('.xls'):
        try:
            import xlrd
        except ImportError:
            print("❌ xlrd non installato. Necessario per file .xls")
            print("   Installare con: pip install xlrd")
            print("   Oppure converti il file in .xlsx prima di usare lo script")
            sys.exit(1)
    
    # File di output
    output_file = None
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    try:
        result_file = convert_alpitour_to_piano_lavoro(input_file, output_file)
        print(f"\n🎉 Conversione completata!")
        print(f"📁 File generato: {result_file}")
        print(f"\n💡 Puoi ora usare questo file come input per il calcolo Piano Lavoro")
    except ImportError as e:
        if 'xlrd' in str(e):
            print(f"\n❌ {e}")
            print("   Per file .xls è necessario installare xlrd:")
            print("   pip install xlrd")
        else:
            print(f"\n❌ Errore importazione: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore durante la conversione: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

