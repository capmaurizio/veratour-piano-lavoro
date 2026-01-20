#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Rusconi — Calcolatore blocchi

Cosa fa:
- Legge file Excel "Piano Lavoro" (anche con più fogli)
- Filtra TO=Rusconi e APT richiesto (opzionale)
- Forward-fill TURNO per DATA rispettando l'ordine: file -> foglio -> righe
- Blocco = (DATA, APT, TURNO_ffill_normalizzato)
- Parse TURNO robusto (08–11, 8:00-11, 8.00–11.30, ecc.; -, –, —)
- Gestisce mezzanotte (fine < inizio => +1 giorno)
- Output Excel: DettaglioBlocchi, TotaliPeriodo, Discrepanze, fogli per aeroporto, TOTALE

Requisiti:
  pip install pandas openpyxl python-dateutil

Esempi:
  python consuntivorusconi.py -i "Piano lavoro DICEMBRE 25.xlsx" -o "OUT_RUSCONI.xlsx"
  python consuntivorusconi.py -i "Piano lavoro DICEMBRE 25.xlsx" -o "OUT_RUSCONI.xlsx" --apt VRN
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Tuple, Iterable

import numpy as np
import pandas as pd

try:
    from dateutil.easter import easter
except ImportError:
    # Calcolo manuale di Pasqua usando l'algoritmo di Meeus/Jones/Butcher (Gregoriano)
    def easter(year: int) -> date:
        """Calcola la data di Pasqua per un dato anno (algoritmo Gregoriano)"""
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)


# -----------------------------
# Config
# -----------------------------

@dataclass
class RoundingPolicy:
    mode: str  # NONE | FLOOR | CEIL | NEAREST
    step_min: int

    def apply(self, minutes: int) -> int:
        if minutes is None:
            return None
        if self.mode.upper() == "NONE":
            return int(minutes)
        step = int(self.step_min)
        if step <= 0:
            return int(minutes)

        x = float(minutes) / step
        m = self.mode.upper()
        if m == "FLOOR":
            return int(np.floor(x) * step)
        if m == "CEIL":
            return int(np.ceil(x) * step)
        if m == "NEAREST":
            return int(np.round(x) * step)
        return int(minutes)


# Tariffe base Rusconi per 2h30 (150 min)
# Tutti gli scali nazionali: €100,00
# FCO e VCE: €110,00
TARIFFE_BASE_RUSCONI = {
    "FCO": 110.0,  # Roma Fiumicino
    "VCE": 110.0,  # Venezia
    # Tutti gli altri: €100,00 (default)
}

# Tariffa notturna Rusconi (€/min) - 20% su (Base + Extra)
# €0,12/min (20% di €0,60/min che è la base oraria media)
TARIFFA_NOTTE_RUSCONI = 0.12  # €0,12/min fisso

# Tariffe carte di imbarco
TARIFFA_CARTE_SOGLIA_20 = 0.18  # €0,18 per documento fino a 20 passeggeri
TARIFFA_CARTE_OLTRE_20 = 0.25   # €0,25 per documento oltre 20 passeggeri


@dataclass
class CalcConfig:
    apt_filter: Optional[List[str]]  # e.g. ["VRN"]
    to_keyword: str = "rusconi"  # Default
    rounding_extra: RoundingPolicy = field(default_factory=lambda: RoundingPolicy("NONE", 5))
    rounding_night: RoundingPolicy = field(default_factory=lambda: RoundingPolicy("NONE", 5))
    holiday_dates: Optional[set[date]] = None  # optional external list
    
    # Tariffe Rusconi
    rate_extra_per_h: float = 18.0  # €18/h = €0.30/min
    durata_base_min: int = 150  # 2h30 = 150 minuti
    festivo_multiplier: float = 1.30  # +30% per festivi


# -----------------------------
# Parsing utilities
# -----------------------------

def normalize_spaces(s: str) -> str:
    """Normalizza spazi multipli"""
    return re.sub(r"\s+", " ", str(s).strip())


def parse_excel_date(x) -> Optional[pd.Timestamp]:
    """Parse data da Excel (può essere stringa, numero, datetime)"""
    if pd.isna(x):
        return None
    
    if isinstance(x, pd.Timestamp):
        return x
    
    if isinstance(x, (datetime, date)):
        return pd.Timestamp(x)
    
    s = str(x).strip()
    if not s or s.lower() in ["nan", "none", ""]:
        return None
    
    # Prova vari formati
    for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%d/%m/%y"]:
        try:
            return pd.Timestamp(datetime.strptime(s, fmt))
        except:
            continue
    
    # Prova con pandas
    try:
        return pd.to_datetime(s, dayfirst=True)
    except:
        pass
    
    return None


def parse_time_value(x) -> Optional[Tuple[int, int]]:
    """Parse orario da cella Excel -> (ore, minuti)"""
    if pd.isna(x):
        return None
    
    if isinstance(x, time):
        return (x.hour, x.minute)
    
    if isinstance(x, datetime):
        return (x.hour, x.minute)
    
    s = str(x).strip()
    if not s or s.lower() in ["nan", "none", ""]:
        return None
    
    # Rimuovi spazi
    s = s.replace(" ", "")
    
    # HH:MM o HH.MM
    m = re.match(r"^(\d{1,2})[.:](\d{2})$", s)
    if m:
        h, mm = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mm <= 59:
            return (h, mm)
    
    # HHMM
    m = re.match(r"^(\d{3,4})$", s)
    if m:
        num = int(m.group(1))
        h = num // 100
        mm = num % 100
        if 0 <= h <= 23 and 0 <= mm <= 59:
            return (h, mm)
    
    return None


def parse_turno(turno_raw: str) -> Tuple[Optional[str], Optional[str], bool, str]:
    """
    Parse stringa TURNO -> (inizio_str, fine_str, no_dec, turno_norm)
    Esempi: "08-11", "8:00-11", "8.00–11.30", "SC1 08-11", "NO DEC 08-11"
    """
    if not turno_raw or pd.isna(turno_raw):
        return (None, None, False, "")
    
    s = normalize_spaces(str(turno_raw))
    if not s:
        return (None, None, False, "")
    
    # Flag "NO DEC"
    no_dec = "NO DEC" in s.upper() or "NODEC" in s.upper()
    s = re.sub(r"(?i)no\s*dec", "", s).strip()
    
    # Rimuovi prefissi tipo "SC1", "SC2", ecc.
    s = re.sub(r"^(SC\d+|SC\s*\d+)\s*", "", s, flags=re.IGNORECASE).strip()
    
    # Cerca pattern: HH:MM-HH:MM, HH-HH, HH.MM-HH.MM, ecc.
    patterns = [
        r"(\d{1,2})[.:](\d{2})\s*[-–—]\s*(\d{1,2})[.:](\d{2})",  # 08:30-11:30
        r"(\d{1,2})\s*[-–—]\s*(\d{1,2})[.:](\d{2})",  # 8-11:30
        r"(\d{1,2})[.:](\d{2})\s*[-–—]\s*(\d{1,2})",  # 08:30-11
        r"(\d{1,2})\s*[-–—]\s*(\d{1,2})",  # 8-11
    ]
    
    for pat in patterns:
        m = re.match(pat, s)
        if m:
            groups = m.groups()
            if len(groups) == 4:
                h1, m1, h2, m2 = int(groups[0]), int(groups[1]), int(groups[2]), int(groups[3])
            elif len(groups) == 3:
                if ':' in s or '.' in s:
                    if groups[1].isdigit() and len(groups[1]) == 2:  # HH:MM-HH
                        h1, m1, h2 = int(groups[0]), int(groups[1]), int(groups[2])
                        m2 = 0
                    else:  # HH-HH:MM
                        h1, h2, m2 = int(groups[0]), int(groups[1]), int(groups[2])
                        m1 = 0
                else:
                    h1, h2, m2 = int(groups[0]), int(groups[1]), int(groups[2])
                    m1 = 0
            else:  # len == 2
                h1, h2 = int(groups[0]), int(groups[1])
                m1 = m2 = 0
            
            if 0 <= h1 <= 23 and 0 <= m1 <= 59 and 0 <= h2 <= 47 and 0 <= m2 <= 59:
                start_str = f"{h1:02d}:{m1:02d}"
                end_str = f"{h2 % 24:02d}:{m2:02d}"
                turno_norm = f"{start_str}-{end_str}"
                return (start_str, end_str, no_dec, turno_norm)
    
    return (None, None, no_dec, s)


def to_dt(date_val: pd.Timestamp, time_str: str) -> pd.Timestamp:
    """Combina data e orario stringa -> Timestamp"""
    h, m = map(int, time_str.split(":"))
    dt = date_val.replace(hour=h, minute=m, second=0, microsecond=0)
    return dt


def night_minutes(start_dt: pd.Timestamp, end_dt: pd.Timestamp) -> int:
    """
    Calcola minuti notturni nella fascia 22:00-06:00 (Rusconi)
    Gestisce attraversamento mezzanotte
    """
    if pd.isna(start_dt) or pd.isna(end_dt) or start_dt >= end_dt:
        return 0
    
    total_minutes = 0
    current = start_dt
    
    while current < end_dt:
        # Calcola fine del minuto corrente
        next_min = current + pd.Timedelta(minutes=1)
        if next_min > end_dt:
            next_min = end_dt
        
        # Verifica se il minuto corrente è nella fascia notturna
        hour = current.hour
        minute = current.minute
        
        # Fascia: 22:00-06:00 (Rusconi)
        is_night = False
        if hour == 22:
            is_night = True
        elif hour == 23:
            is_night = True
        elif hour >= 0 and hour < 6:
            is_night = True
        
        if is_night:
            total_minutes += 1
        
        current = next_min
    
    return total_minutes


def compute_turno_eur(apt: str) -> float:
    """Calcola importo turno base (sempre 2h30 = 150 min) - €100,00 o €110,00"""
    apt_upper = apt.upper().strip()
    return TARIFFE_BASE_RUSCONI.get(apt_upper, 100.0)  # Default: €100,00


def compute_extra_eur(durata_effettiva_min: int, cfg: CalcConfig) -> float:
    """
    Calcola importo extra: MAX(0, durata_effettiva - 180) × €18/h = €0.30/min
    Le ore extra decorrono dal decollo schedulato (STD)
    """
    extra_min = max(0, durata_effettiva_min - cfg.durata_base_min)
    return extra_min * (cfg.rate_extra_per_h / 60.0)


def compute_night_eur(night_min: int, base_eur: float, extra_eur: float) -> float:
    """
    Calcola importo notturno: 20% su (Base + Extra) proporzionato ai minuti notturni
    Formula: (Base_€ + Extra_€) × 20% × (night_min / durata_totale_min)
    Per semplicità: night_min × €0,12/min (equivalente)
    """
    # Per Rusconi, il notturno è calcolato come 20% su (Base + Extra)
    # ma proporzionato ai minuti effettivi nella fascia notturna
    # Usiamo il metodo semplificato: night_min × €0,12/min
    return night_min * TARIFFA_NOTTE_RUSCONI


def get_italian_holidays_2025() -> set[date]:
    """Restituisce set di date festivi italiani 2025"""
    holidays = set()
    
    # Festivi fissi 2025
    holidays.add(date(2025, 1, 1))   # Capodanno
    holidays.add(date(2025, 1, 6))   # Epifania
    holidays.add(date(2025, 4, 25))  # Liberazione
    holidays.add(date(2025, 5, 1))   # Festa del Lavoro
    holidays.add(date(2025, 6, 2))   # Festa della Repubblica
    holidays.add(date(2025, 11, 1))  # Ognissanti
    holidays.add(date(2025, 8, 15))  # Ferragosto
    holidays.add(date(2025, 12, 8))  # Immacolata
    holidays.add(date(2025, 12, 25)) # Natale
    holidays.add(date(2025, 12, 26)) # Santo Stefano
    
    # Pasqua 2025 (calcolata)
    easter_2025 = easter(2025)
    holidays.add(easter_2025)              # Pasqua
    holidays.add(easter_2025 + timedelta(days=1))  # Pasquetta
    
    return holidays


def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [normalize_spaces(str(c)).upper() for c in df.columns]
    return df


def find_col(df: pd.DataFrame, patterns: Iterable[str]) -> Optional[str]:
    cols = list(df.columns)
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for c in cols:
            if rx.search(c):
                return c
    return None


def detect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Rileva colonne nel file Piano Lavoro
    """
    return {
        "data": find_col(df, [r"^DATA$", r"\bDATE\b"]),
        "tour_operator": find_col(df, [r"TOUR\s*OPERATOR", r"^TO$", r"\bOPERATORE\b"]),
        "apt": find_col(df, [r"^APT$", r"\bAEROPORTO\b", r"\bSCALO\b"]),
        "turno": find_col(df, [r"^TURNO$", r"^TURNO\s*ASSISTENTE$", r"\bTURNI\b"]),
        "atd": find_col(df, [r"^ATD$", r"\bORARIO\s*ATD\b"]),
        "std": find_col(df, [r"^STD$", r"\bORARIO\s*STD\b"]),
        "passeggeri": find_col(df, [r"^PASSEGGERI$", r"\bPAX\b", r"\bPASSENGERS\b", r"\bPASS\b"]),  # Per carte di imbarco
        "importo": find_col(df, [r"^IMPORTO$", r"\bTOTALE\b", r"^COSTO\s*$"]),
        "ore_extra": find_col(df, [r"\bORE\s*EXTRA\b", r"^EXTRA$", r"\bEXTRA\s*(MIN|ORE)\b"]),
        "notturno": find_col(df, [r"^NOTTURNO$", r"\bNIGHT\b"]),
        "festivo": find_col(df, [r"^FESTIVO$", r"\bHOLIDAY\b"]),
        "assistente": find_col(df, [r"^ASSISTENTE$", r"\bASSISTENTE\b"]),
    }


# -----------------------------
# Core computation
# -----------------------------

@dataclass
class SourceRowRef:
    file: str
    sheet: str
    row_index: int  # index within sheet df after load (0-based)
    original_order: int


@dataclass
class BlockAgg:
    date: pd.Timestamp
    apt: str
    turno_raw_ffill: str
    turno_norm: str
    start_dt: pd.Timestamp
    end_dt: pd.Timestamp
    durata_min: int
    no_dec: bool
    first_source: SourceRowRef
    atd_list: List[pd.Timestamp]
    std_list: List[pd.Timestamp]
    assistente: Optional[str] = None
    tour_operator_originale: Optional[str] = None  # TOUR OPERATOR originale dalla riga
    passeggeri: Optional[int] = None  # Numero passeggeri per carte di imbarco
    errore: Optional[str] = None  # Messaggio di errore se i dati non sono validi


def iter_excel_sheets(file_path: str) -> Iterable[Tuple[str, pd.DataFrame]]:
    """Itera su tutti i fogli del file Excel"""
    xls = pd.ExcelFile(file_path)
    for sheet in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet)
        yield sheet, df


def process_files(input_files: List[str], cfg: CalcConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Legge e processa i file Piano Lavoro per Rusconi
    
    Returns: (detail_blocks_df, totals_df, discrepancies_df)
    """
    blocks: Dict[Tuple[pd.Timestamp, str, str], BlockAgg] = {}
    global_order = 0

    for file_path in input_files:
        for sheet_name, sdf0 in iter_excel_sheets(file_path):
            if sdf0 is None or sdf0.empty:
                continue

            sdf = normalize_cols(sdf0)
            cols = detect_columns(sdf)

            # Minimal cols required
            if not cols["data"] or not cols["apt"] or not cols["turno"]:
                continue

            # Filter TO if present - Rusconi
            if cols["tour_operator"]:
                mask_rusconi = sdf[cols["tour_operator"]].astype(str).str.contains("rusconi", case=False, na=False)
                sdf = sdf[mask_rusconi].copy()
                if sdf.empty:
                    continue

            # Filter APT if requested
            if cfg.apt_filter and cols["apt"]:
                apt_pat = "|".join([re.escape(a) for a in cfg.apt_filter])
                mask_apt = sdf[cols["apt"]].astype(str).str.contains(rf"\b({apt_pat})\b", case=False, na=False)
                sdf = sdf[mask_apt].copy()
                if sdf.empty:
                    continue

            # Parse date
            sdf["__date"] = sdf[cols["data"]].apply(parse_excel_date)
            sdf = sdf[sdf["__date"].notna()].copy()
            if sdf.empty:
                continue

            # Preserve order within this sheet chunk
            sdf["__sheet_row_order"] = np.arange(len(sdf), dtype=int)
            sdf["__global_order"] = np.arange(global_order, global_order + len(sdf), dtype=int)
            global_order += len(sdf)

            # Forward-fill TURNO per DATA within the sheet chunk order
            turno_col = cols["turno"]
            sdf["__turno_raw"] = sdf[turno_col].astype(str)
            ffill_src = sdf[turno_col].replace("", np.nan)
            sdf["__turno_ffill"] = ffill_src.ffill()

            # Parse turno
            sdf["__turno_parsed"] = sdf["__turno_ffill"].apply(parse_turno)
            sdf["__start_str"] = sdf["__turno_parsed"].apply(lambda x: x[0] if x else None)
            sdf["__end_str"] = sdf["__turno_parsed"].apply(lambda x: x[1] if x else None)
            sdf["__no_dec"] = sdf["__turno_parsed"].apply(lambda x: x[2] if x else False)
            sdf["__turno_norm"] = sdf["__turno_parsed"].apply(lambda x: x[3] if x else "")

            # Calcola start_dt e end_dt
            sdf["__start_dt"] = sdf.apply(
                lambda r: to_dt(r["__date"], r["__start_str"]) if r["__start_str"] else pd.NaT, axis=1
            )
            sdf["__end_dt"] = sdf.apply(
                lambda r: to_dt(r["__date"], r["__end_str"]) if r["__end_str"] else pd.NaT, axis=1
            )

            # Gestisci mezzanotte (fine < inizio => +1 giorno)
            mask_overnight = (sdf["__end_dt"] < sdf["__start_dt"]) & sdf["__end_dt"].notna()
            sdf.loc[mask_overnight, "__end_dt"] = sdf.loc[mask_overnight, "__end_dt"] + pd.Timedelta(days=1)

            # Calcola durata
            sdf["__durata_min"] = (
                (sdf["__end_dt"] - sdf["__start_dt"]).dt.total_seconds() / 60.0
            )
            sdf["__durata_min"] = sdf["__durata_min"].fillna(0).astype(int)

            # Extract ATD/STD
            assistente_col = cols["assistente"]

            # Iterate rows and aggregate by block
            for idx, r in sdf.iterrows():
                d = r["__date"]
                apt = str(r[cols["apt"]]).strip() if cols["apt"] else ""
                turno_norm = str(r["__turno_norm"]).strip() if pd.notna(r.get("__turno_norm")) else ""
                turno_ffill_raw = str(r["__turno_ffill"]).strip() if pd.notna(r.get("__turno_ffill")) else ""
                assistente_val = str(r[assistente_col]).strip() if assistente_col and assistente_col in r.index and pd.notna(r[assistente_col]) else ""
                
                # Estrai TOUR OPERATOR originale
                tour_operator_orig = None
                if cols["tour_operator"] and cols["tour_operator"] in r.index:
                    to_val = str(r[cols["tour_operator"]]).strip()
                    if to_val and to_val.lower() not in ["nan", "none", ""]:
                        tour_operator_orig = to_val
                
                # Extract ATD candidates from row
                atd_times: List[Tuple[int, int]] = []
                if cols["atd"]:
                    atd_val = r[cols["atd"]]
                    parsed = parse_time_value(atd_val)
                    if parsed:
                        atd_times.append(parsed)

                # Extract STD candidates from row
                std_times: List[Tuple[int, int]] = []
                if cols["std"]:
                    std_val = r[cols["std"]]
                    parsed = parse_time_value(std_val)
                    if parsed:
                        std_times.append(parsed)

                # Extract PASSEGGERI per carte di imbarco
                passeggeri_val = None
                if cols.get("passeggeri"):
                    pax_val = r[cols["passeggeri"]]
                    try:
                        if pd.notna(pax_val):
                            passeggeri_val = int(float(pax_val))
                    except:
                        pass

                # Se turno_norm è vuoto, crea un placeholder descrittivo basato su STD
                if not turno_norm:
                    # Prova a usare STD per creare un placeholder più descrittivo
                    std_placeholder = "NO_TURNO"
                    if std_times:
                        hh, mm = std_times[0]
                        std_placeholder = f"NO_TURNO_STD{hh:02d}{mm:02d}"
                    elif atd_times:
                        hh, mm = atd_times[0]
                        std_placeholder = f"NO_TURNO_ATD{hh:02d}{mm:02d}"
                    turno_norm = std_placeholder

                # RUSCONI: ogni riga del Piano Lavoro genera un blocco separato
                # Usa un identificatore univoco per riga (indice globale) per evitare aggregazioni
                key = (d, apt, turno_norm, int(r["__global_order"]))

                # Anchor ATDs to date; if ATD < start_dt => +1 day
                atd_dt_list: List[pd.Timestamp] = []
                for hh, mm in atd_times:
                    tdt = d + pd.Timedelta(hours=hh, minutes=mm)
                    if tdt < r["__start_dt"]:
                        tdt = tdt + pd.Timedelta(days=1)
                    atd_dt_list.append(tdt)

                # Anchor STDs to date; if STD < start_dt => +1 day
                std_dt_list: List[pd.Timestamp] = []
                for hh, mm in std_times:
                    tdt = d + pd.Timedelta(hours=hh, minutes=mm)
                    if tdt < r["__start_dt"]:
                        tdt = tdt + pd.Timedelta(days=1)
                    std_dt_list.append(tdt)

                # Aggrega o crea nuovo blocco
                if key in blocks:
                    b = blocks[key]
                    b.atd_list.extend(atd_dt_list)
                    b.std_list.extend(std_dt_list)
                    # Mantieni passeggeri se non era già presente
                    if b.passeggeri is None and passeggeri_val is not None:
                        b.passeggeri = passeggeri_val
                else:
                    blocks[key] = BlockAgg(
                        date=d,
                        apt=apt,
                        turno_raw_ffill=turno_ffill_raw,
                        turno_norm=turno_norm,
                        start_dt=r["__start_dt"],
                        end_dt=r["__end_dt"],
                        durata_min=int(r["__durata_min"]) if pd.notna(r["__durata_min"]) else 0,
                        no_dec=r["__no_dec"],
                        first_source=SourceRowRef(
                            file=file_path,
                            sheet=sheet_name,
                            row_index=int(r["__sheet_row_order"]),
                            original_order=int(r["__global_order"]),
                        ),
                        atd_list=atd_dt_list,
                        std_list=std_dt_list,
                        assistente=assistente_val if assistente_val else None,
                        tour_operator_originale=tour_operator_orig,
                        passeggeri=passeggeri_val,
                    )

    # Converti blocchi in DataFrame per output
    rows_detail = []

    for key, b in sorted(blocks.items(), key=lambda kv: (kv[1].date, kv[1].apt, kv[1].first_source.original_order)):
        # RUSCONI: START = STD - 2:30
        # Base: quota fissa €100 o €110 (per volo, include 2h30)
        # Extra: solo sul ritardo (ATD - STD), non sulla durata totale
        # Notturno: 20% su (Base + Extra), calcolato proporzionalmente ai minuti nella fascia 22:00-06:00
        # Carte di imbarco: servizio accessorio
        
        std_sel = b.std_list[0] if b.std_list else None
        atd_sel = b.atd_list[0] if b.atd_list else None
        errore_msg = None
        
        # Per Rusconi, assicuriamoci che STD sia nella data corretta della riga
        if std_sel is not None and b.date and std_sel.date() != b.date.date():
            # Ricalcola STD usando la data della riga
            std_hour = std_sel.hour
            std_minute = std_sel.minute
            std_sel = pd.Timestamp.combine(b.date.date(), pd.Timestamp(f"{std_hour:02d}:{std_minute:02d}").time())
        
        # Inizializza variabili
        durata_base_min = 150  # 2h30 = 150 minuti (fisso)
        durata_extra_min = 0
        
        # Verifica che STD sia disponibile
        if pd.isna(std_sel):
            errore_msg = "STD non disponibile"
            turno_eur = 0.0
            extra_min = 0
            extra_eur = 0.0
            night_min = 0
            night_eur = 0.0
            carte_eur = 0.0
            totale = 0.0
            start_rusconi = b.start_dt
            end_rusconi = atd_sel if pd.notna(atd_sel) else b.end_dt
        else:
            # START = STD - 2:30
            start_rusconi = std_sel - pd.Timedelta(hours=2, minutes=30)
            
            # Base: quota fissa per volo (€100 o €110)
            turno_eur = compute_turno_eur(b.apt)
            
            # Extra: solo sul ritardo (ATD - STD), non sulla durata totale
            # Se il volo parte in orario o in anticipo → extra = 0
            if pd.notna(atd_sel) and atd_sel > std_sel:
                durata_extra_min = int((atd_sel - std_sel).total_seconds() / 60.0)
                extra_min = durata_extra_min
                # Calcola extra: durata_extra_min × €18/h = durata_extra_min × €0.30/min
                extra_eur = durata_extra_min * (cfg.rate_extra_per_h / 60.0)
            else:
                durata_extra_min = 0
                extra_min = 0
                extra_eur = 0.0
                if pd.isna(atd_sel):
                    errore_msg = "ATD non disponibile per calcolo extra"
                else:
                    errore_msg = None
            
            # Notturno: 20% su (Base + Extra), calcolato proporzionalmente ai minuti nella fascia 22:00-06:00
            # Calcolato su tutto l'intervallo (START a ATD o fine turno)
            end_for_night = atd_sel if pd.notna(atd_sel) else b.end_dt
            if pd.notna(end_for_night):
                night_min = night_minutes(start_rusconi, end_for_night)
                # Notturno: 20% su (Base + Extra) proporzionato ai minuti notturni
                # Usiamo il metodo semplificato: night_min × €0,12/min
                night_eur = compute_night_eur(night_min, turno_eur, extra_eur)
            else:
                night_min = 0
                night_eur = 0.0
            
            # Carte di imbarco: servizio accessorio
            carte_eur = 0.0
            if b.passeggeri is not None and b.passeggeri > 0:
                if b.passeggeri <= 20:
                    carte_eur = b.passeggeri * TARIFFA_CARTE_SOGLIA_20
                else:
                    carte_eur = b.passeggeri * TARIFFA_CARTE_OLTRE_20
            
            # Durata totale per output
            end_rusconi = atd_sel if pd.notna(atd_sel) else b.end_dt
            
            # Festivo: +30% su tutto (Base + Extra + Notturno + Carte)
            # Verifica se è festivo (da colonna o da lista date)
            is_festivo = False
            holiday_dates_to_use = cfg.holiday_dates
            if holiday_dates_to_use is None:
                holiday_dates_to_use = get_italian_holidays_2025()
            
            if pd.notna(b.date) and b.date.date() in holiday_dates_to_use:
                is_festivo = True
            
            if is_festivo:
                totale = (turno_eur + extra_eur + night_eur + carte_eur) * cfg.festivo_multiplier
            else:
                totale = turno_eur + extra_eur + night_eur + carte_eur
        
        # Usa TOUR OPERATOR originale salvato nel blocco
        tour_operator_val = b.tour_operator_originale if b.tour_operator_originale else "Rusconi"
        
        rows_detail.append({
            "DATA": b.date.strftime("%d/%m/%Y") if pd.notna(b.date) else "",
            "APT": b.apt,
            "TOUR OPERATOR": tour_operator_val,
            "ASSISTENTE": b.assistente if b.assistente else "",
            "TURNO_FFILL": b.turno_raw_ffill,
            "TURNO_NORMALIZZATO": b.turno_norm,
            "INIZIO_DT": start_rusconi if not pd.isna(start_rusconi) else b.start_dt,
            "FINE_DT": end_rusconi if not pd.isna(end_rusconi) else b.end_dt,
            "DURATA_TURNO_MIN": durata_base_min + durata_extra_min,
            "NO_DEC": "Sì" if b.no_dec else "No",
            "ATD_SCELTO": atd_sel,
            "STD_SCELTO": std_sel,
            "PASSEGGERI": b.passeggeri if b.passeggeri is not None else 0,
            "TURNO_EUR": round(turno_eur, 2),
            "EXTRA_MIN": extra_min,
            "EXTRA_EUR": round(extra_eur, 2),
            "NOTTE_MIN": night_min,
            "NOTTE_EUR": round(night_eur, 2),
            "CARTE_EUR": round(carte_eur, 2),
            "FESTIVO": is_festivo if 'is_festivo' in locals() else False,
            "TOTALE_BLOCCO_EUR": round(totale, 2),
            "ERRORE": str(errore_msg) if errore_msg else (str(b.errore) if b.errore else ""),
            "SRC_FILE": b.first_source.file,
            "SRC_SHEET": b.first_source.sheet,
            "SRC_ROW0": b.first_source.row_index + 2,  # Excel è 1-based
        })

    detail_df = pd.DataFrame(rows_detail)
    
    # Sostituisci NaN con stringa vuota nella colonna ERRORE
    if 'ERRORE' in detail_df.columns:
        detail_df['ERRORE'] = detail_df['ERRORE'].fillna('').astype(str).replace('nan', '').replace('None', '')

    # Totals by period (struttura base, da completare)
    if detail_df.empty:
        totals_df = pd.DataFrame(columns=[
            "TOUR OPERATOR", "PERIODO", "TOT_TURNO_EUR", "TOT_EXTRA_MIN", "TOT_EXTRA_H:MM", "TOT_EXTRA_EUR",
            "TOT_NOTTE_MIN", "TOT_NOTTE_EUR", "TOT_CARTE_EUR", "TOT_TOTALE_EUR"
        ])
        discr_df = pd.DataFrame(columns=[
            "DATA", "APT", "TOUR OPERATOR", "TURNO_NORMALIZZATO",
            "EXTRA_MIN_CALC", "EXTRA_MIN_FILE", "DELTA_EXTRA_MIN",
            "NOTTE_MIN_CALC", "NOTTE_MIN_FILE", "DELTA_NOTTE_MIN",
            "TOTALE_CALC_EUR", "TOTALE_FILE_EUR", "DELTA_TOTALE_EUR",
            "SRC_FILE", "SRC_SHEET", "SRC_ROW0"
        ])
        return detail_df, totals_df, discr_df

    detail_df["__DATE_TS"] = pd.to_datetime(detail_df["DATA"], dayfirst=True)
    detail_df["PERIODO"] = np.where(detail_df["__DATE_TS"].dt.day <= 15, "1–15", "16–31")

    def sum_hmm(minutes: int) -> str:
        minutes = int(minutes)
        return f"{minutes // 60}:{minutes % 60:02d}"

    # Raggruppa per TOUR OPERATOR e PERIODO
    
    groupby_cols = ["PERIODO"]
    if "TOUR OPERATOR" in detail_df.columns:
        # Usa TOUR OPERATOR originale per mantenere la distinzione nei dettagli
        groupby_cols = ["TOUR OPERATOR", "PERIODO"]
    
    totals = detail_df.groupby(groupby_cols, as_index=False).agg(
        TOT_TURNO_EUR=("TURNO_EUR", "sum"),
        TOT_EXTRA_MIN=("EXTRA_MIN", "sum"),
        TOT_EXTRA_EUR=("EXTRA_EUR", "sum"),
        TOT_NOTTE_MIN=("NOTTE_MIN", "sum"),
        TOT_NOTTE_EUR=("NOTTE_EUR", "sum"),
        TOT_CARTE_EUR=("CARTE_EUR", "sum") if "CARTE_EUR" in detail_df.columns else ("TURNO_EUR", lambda x: 0.0),
        TOT_TOTALE_EUR=("TOTALE_BLOCCO_EUR", "sum"),
    )

    totals["TOT_EXTRA_H:MM"] = totals["TOT_EXTRA_MIN"].apply(sum_hmm)
    
    # Riordina colonne
    if "TOUR OPERATOR" in totals.columns:
        totals = totals[[
            "TOUR OPERATOR", "PERIODO", "TOT_TURNO_EUR", "TOT_EXTRA_MIN", "TOT_EXTRA_H:MM", "TOT_EXTRA_EUR",
            "TOT_NOTTE_MIN", "TOT_NOTTE_EUR", "TOT_CARTE_EUR", "TOT_TOTALE_EUR"
        ]]
    else:
        totals = totals[[
            "PERIODO", "TOT_TURNO_EUR", "TOT_EXTRA_MIN", "TOT_EXTRA_H:MM", "TOT_EXTRA_EUR",
            "TOT_NOTTE_MIN", "TOT_NOTTE_EUR", "TOT_CARTE_EUR", "TOT_TOTALE_EUR"
        ]]

    # Riga totale mese
    month_row = pd.DataFrame([{
        "TOUR OPERATOR": "Rusconi" if "TOUR OPERATOR" in detail_df.columns else "",
        "PERIODO": "MESE",
        "TOT_TURNO_EUR": float(detail_df["TURNO_EUR"].sum()),
        "TOT_EXTRA_MIN": int(detail_df["EXTRA_MIN"].sum()),
        "TOT_EXTRA_H:MM": sum_hmm(int(detail_df["EXTRA_MIN"].sum())),
        "TOT_EXTRA_EUR": float(detail_df["EXTRA_EUR"].sum()),
        "TOT_NOTTE_MIN": int(detail_df["NOTTE_MIN"].sum()),
        "TOT_NOTTE_EUR": float(detail_df["NOTTE_EUR"].sum()),
        "TOT_CARTE_EUR": float(detail_df["CARTE_EUR"].sum()) if "CARTE_EUR" in detail_df.columns else 0.0,
        "TOT_TOTALE_EUR": float(detail_df["TOTALE_BLOCCO_EUR"].sum()),
    }])

    totals_df = pd.concat([totals, month_row], ignore_index=True)

    # cleanup helper col
    detail_df = detail_df.drop(columns=["__DATE_TS"], errors="ignore")

    # Discrepanze (vuoto per ora, ma con colonne corrette)
    discr_df = pd.DataFrame(columns=[
        "DATA", "APT", "TOUR OPERATOR", "TURNO_NORMALIZZATO",
        "EXTRA_MIN_CALC", "EXTRA_MIN_FILE", "DELTA_EXTRA_MIN",
        "NOTTE_MIN_CALC", "NOTTE_MIN_FILE", "DELTA_NOTTE_MIN",
        "TOTALE_CALC_EUR", "TOTALE_FILE_EUR", "DELTA_TOTALE_EUR",
        "SRC_FILE", "SRC_SHEET", "SRC_ROW0"
    ])

    return detail_df, totals_df, discr_df


# -----------------------------
# Helper functions for output sheets
# -----------------------------

def format_minutes_to_hmm(minutes):
    """Convert minutes to H:MM format"""
    if pd.isna(minutes) or minutes == 0:
        return "0:00"
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h}:{m:02d}"


def create_apt_detail_sheet(df_apt: pd.DataFrame) -> pd.DataFrame:
    """Create detailed sheet for an airport with totals per row"""
    if df_apt.empty:
        return pd.DataFrame()
    
    # Sort by date
    df_apt = df_apt.sort_values('DATA').copy()
    
    # Format columns
    df_apt['DURATA_H:MM'] = df_apt['DURATA_TURNO_MIN'].apply(format_minutes_to_hmm)
    df_apt['EXTRA_H:MM'] = df_apt['EXTRA_MIN'].apply(format_minutes_to_hmm)
    df_apt['NOTTE_H:MM'] = df_apt['NOTTE_MIN'].apply(format_minutes_to_hmm)
    
    # Create output DataFrame
    output_cols = {
        'Data': df_apt['DATA'],
        'Tour Operator': df_apt['TOUR OPERATOR'].fillna('') if 'TOUR OPERATOR' in df_apt.columns else pd.Series([''] * len(df_apt)),
        'Turno': df_apt['TURNO_NORMALIZZATO'],
        'Durata': df_apt['DURATA_H:MM'],
        'Turno (€)': df_apt['TURNO_EUR'].round(2),
        'Extra (h:mm)': df_apt['EXTRA_H:MM'],
        'Extra (€)': df_apt['EXTRA_EUR'].round(2),
        'Notturno (h:mm)': df_apt['NOTTE_H:MM'],
        'Notturno (€)': df_apt['NOTTE_EUR'].round(2),
    }
    
    # Aggiungi Carte di imbarco se presente
    if 'CARTE_EUR' in df_apt.columns:
        output_cols['Carte (€)'] = df_apt['CARTE_EUR'].round(2)
    
    output_cols['TOTALE (€)'] = df_apt['TOTALE_BLOCCO_EUR'].round(2)
    
    # Add Assistente column if present (insert after Tour Operator)
    if 'ASSISTENTE' in df_apt.columns:
        new_cols = {'Data': output_cols['Data']}
        new_cols['Tour Operator'] = output_cols['Tour Operator']
        new_cols['Assistente'] = df_apt['ASSISTENTE'].fillna('')
        for k, v in output_cols.items():
            if k not in ['Data', 'Tour Operator']:
                new_cols[k] = v
        output_cols = new_cols
    
    result_df = pd.DataFrame(output_cols)
    
    # Add total row
    total_row_dict = {
        'Data': 'TOTALE',
        'Tour Operator': '',
        'Turno': '',
        'Durata': '',
        'Turno (€)': df_apt['TURNO_EUR'].sum(),
        'Extra (h:mm)': format_minutes_to_hmm(df_apt['EXTRA_MIN'].sum()),
        'Extra (€)': df_apt['EXTRA_EUR'].sum(),
        'Notturno (h:mm)': format_minutes_to_hmm(df_apt['NOTTE_MIN'].sum()),
        'Notturno (€)': df_apt['NOTTE_EUR'].sum(),
    }
    
    # Aggiungi Carte di imbarco se presente
    if 'CARTE_EUR' in df_apt.columns:
        total_row_dict['Carte (€)'] = df_apt['CARTE_EUR'].sum()
    
    total_row_dict['TOTALE (€)'] = df_apt['TOTALE_BLOCCO_EUR'].sum()
    
    # Add empty Assistente in total row if column exists
    if 'ASSISTENTE' in df_apt.columns:
        new_total_dict = {'Data': total_row_dict['Data']}
        new_total_dict['Tour Operator'] = total_row_dict['Tour Operator']
        new_total_dict['Assistente'] = ''
        for k, v in total_row_dict.items():
            if k not in ['Data', 'Tour Operator']:
                new_total_dict[k] = v
        total_row_dict = new_total_dict
    
    total_row = pd.DataFrame([total_row_dict])
    result_df = pd.concat([result_df, total_row], ignore_index=True)
    return result_df


def create_total_by_apt_sheet(detail_df: pd.DataFrame) -> pd.DataFrame:
    """Create total sheet grouped by airport and tour operator"""
    if detail_df.empty:
        return pd.DataFrame(columns=['Tour Operator', 'Aeroporto', 'Blocchi', 'Assistenze', 'Extra', 'Notturno', 'TOTALE'])
    
    # Group by airport (e tour operator se presente)
    groupby_cols = ['APT']
    if 'TOUR OPERATOR' in detail_df.columns:
        groupby_cols = ['TOUR OPERATOR', 'APT']
    
    totals_by_apt = detail_df.groupby(groupby_cols).agg({
        'TURNO_EUR': 'sum',
        'EXTRA_EUR': 'sum',
        'EXTRA_MIN': 'sum',
        'NOTTE_EUR': 'sum',
        'NOTTE_MIN': 'sum',
        'TOTALE_BLOCCO_EUR': 'sum'
    }).round(2)
    
    block_counts = detail_df.groupby(groupby_cols).size()
    
    # Format function
    def format_eur(value):
        if value >= 1000:
            return f"{value:,.2f}€"
        else:
            return f"{value:.2f}€"
    
    def min_to_hours_minutes_text(minutes):
        """Convert minutes to 'X ore e Y minuti' format"""
        if pd.isna(minutes) or minutes == 0:
            return "0 ore e 0 minuti"
        total_minutes = int(minutes)
        hours = total_minutes // 60
        mins = total_minutes % 60
        if hours == 0:
            return f"{mins} minuti"
        elif mins == 0:
            return f"{hours} ore"
        else:
            return f"{hours} ore e {mins} minuti"
    
    # Estrai indici
    if isinstance(totals_by_apt.index, pd.MultiIndex):
        # MultiIndex: (TOUR OPERATOR, APT)
        tour_operators = [idx[0] for idx in totals_by_apt.index]
        aeroporti = [idx[1] for idx in totals_by_apt.index]
    else:
        # Single Index: solo APT
        tour_operators = [''] * len(totals_by_apt)
        aeroporti = totals_by_apt.index.tolist()
    
    result = pd.DataFrame({
        'Tour Operator': tour_operators,
        'Aeroporto': aeroporti,
        'Blocchi': block_counts.values,
        'Assistenze': totals_by_apt['TURNO_EUR'].values,
        'Extra_min': totals_by_apt['EXTRA_MIN'].values,
        'Extra_eur': totals_by_apt['EXTRA_EUR'].values,
        'Notturno_min': totals_by_apt['NOTTE_MIN'].values,
        'Notturno_eur': totals_by_apt['NOTTE_EUR'].values,
        'TOTALE': totals_by_apt['TOTALE_BLOCCO_EUR'].values,
    })
    
    # Format columns
    output_df = pd.DataFrame({
        'Tour Operator': result['Tour Operator'],
        'Aeroporto': result['Aeroporto'],
        'Blocchi': result['Blocchi'],
        'Assistenze': result['Assistenze'].apply(format_eur),
        'Extra': result.apply(lambda x: f"{format_eur(x['Extra_eur'])} ({min_to_hours_minutes_text(x['Extra_min'])})", axis=1),
        'Notturno': result.apply(lambda x: f"{format_eur(x['Notturno_eur'])} ({min_to_hours_minutes_text(x['Notturno_min'])})", axis=1),
        'TOTALE': result['TOTALE'].apply(format_eur),
    })
    
    # Order by tour operator, then airport (VRN, BGY, NAP, VCE)
    order = ['VRN', 'BGY', 'NAP', 'VCE']
    output_df['sort_order'] = output_df['Aeroporto'].apply(lambda x: order.index(x) if x in order else 999)
    output_df = output_df.sort_values(['Tour Operator', 'sort_order']).drop('sort_order', axis=1)
    
    # Add total row
    total_row = pd.DataFrame([{
        'Tour Operator': '',
        'Aeroporto': 'TOTALE',
        'Blocchi': output_df['Blocchi'].sum(),
        'Assistenze': format_eur(result['Assistenze'].sum()),
        'Extra': f"{format_eur(result['Extra_eur'].sum())} ({min_to_hours_minutes_text(result['Extra_min'].sum())})",
        'Notturno': f"{format_eur(result['Notturno_eur'].sum())} ({min_to_hours_minutes_text(result['Notturno_min'].sum())})",
        'TOTALE': format_eur(result['TOTALE'].sum()),
    }])
    
    output_df = pd.concat([output_df, total_row], ignore_index=True)
    return output_df


def write_output_excel(output_path: str, detail_df: pd.DataFrame, totals_df: pd.DataFrame, discr_df: pd.DataFrame) -> None:
    """Scrive file Excel di output"""
    with pd.ExcelWriter(output_path, engine="openpyxl", datetime_format="YYYY-MM-DD HH:MM") as writer:
        # Order columns for readability
        if not detail_df.empty:
            cols = [
                "DATA", "APT", "TOUR OPERATOR", "ASSISTENTE", "TURNO_FFILL", "TURNO_NORMALIZZATO",
                "INIZIO_DT", "FINE_DT", "DURATA_TURNO_MIN", "NO_DEC",
                "ATD_SCELTO", "STD_SCELTO", "PASSEGGERI",
                "TURNO_EUR",
                "EXTRA_MIN", "EXTRA_EUR",
                "NOTTE_MIN", "NOTTE_EUR",
                "CARTE_EUR",
                "FESTIVO", "TOTALE_BLOCCO_EUR",
                "ERRORE",
                "SRC_FILE", "SRC_SHEET", "SRC_ROW0",
            ]
            cols = [c for c in cols if c in detail_df.columns]
            detail_df[cols].to_excel(writer, sheet_name="DettaglioBlocchi", index=False)
        else:
            pd.DataFrame().to_excel(writer, sheet_name="DettaglioBlocchi", index=False)

        totals_df.to_excel(writer, sheet_name="TotaliPeriodo", index=False)

        if not discr_df.empty:
            discr_df.to_excel(writer, sheet_name="Discrepanze", index=False)
        else:
            # Crea DataFrame vuoto con colonne corrette
            empty_discr = pd.DataFrame(columns=[
                "DATA", "APT", "TOUR OPERATOR", "TURNO_NORMALIZZATO",
                "EXTRA_MIN_CALC", "EXTRA_MIN_FILE", "DELTA_EXTRA_MIN",
                "NOTTE_MIN_CALC", "NOTTE_MIN_FILE", "DELTA_NOTTE_MIN",
                "TOTALE_CALC_EUR", "TOTALE_FILE_EUR", "DELTA_TOTALE_EUR",
                "SRC_FILE", "SRC_SHEET", "SRC_ROW0"
            ])
            empty_discr.to_excel(writer, sheet_name="Discrepanze", index=False)
        
        # Create sheets for each airport
        if not detail_df.empty:
            apts = sorted(detail_df['APT'].unique())
            for apt in apts:
                df_apt = detail_df[detail_df['APT'] == apt].copy()
                apt_sheet = create_apt_detail_sheet(df_apt)
                if not apt_sheet.empty:
                    apt_sheet.to_excel(writer, sheet_name=apt, index=False)
        
        # Create TOTALE sheet
        if not detail_df.empty:
            total_sheet = create_total_by_apt_sheet(detail_df)
            if not total_sheet.empty:
                total_sheet.to_excel(writer, sheet_name="TOTALE", index=False)
        
        # Create Collaboratori sheet
        try:
            from tariffe_collaboratori import create_collaboratori_sheet, get_italian_holidays_2025
            festivi_2025 = get_italian_holidays_2025()
            collaboratori_sheet = create_collaboratori_sheet(detail_df, holiday_dates=festivi_2025)
            if not collaboratori_sheet.empty:
                collaboratori_sheet.to_excel(writer, sheet_name="Collaboratori", index=False)
        except ImportError:
            pass  # Modulo tariffe non disponibile, salta

        # Basic column widths
        for sheet in writer.book.worksheets:
            for col_cells in sheet.columns:
                col_letter = col_cells[0].column_letter
                max_len = 0
                for cell in col_cells[:500]:
                    v = cell.value
                    if v is None:
                        continue
                    max_len = max(max_len, len(str(v)))
                if max_len > 0:
                    sheet.column_dimensions[col_letter].width = min(max_len + 2, 50)


def main():
    parser = argparse.ArgumentParser(description="Calcolatore blocchi Rusconi")
    parser.add_argument("-i", "--input", nargs="+", required=True, help="File Excel Piano Lavoro (uno o più)")
    parser.add_argument("-o", "--output", required=True, help="File Excel output")
    parser.add_argument("--apt", nargs="+", help="Filtra aeroporti (es: --apt VRN BGY)")
    parser.add_argument("--to", default="rusconi", help="Keyword tour operator (default: rusconi)")

    args = parser.parse_args()

    cfg = CalcConfig(
        apt_filter=args.apt,
        to_keyword=args.to,
    )

    print(f"📄 Elaborazione file: {args.input}")
    detail_df, totals_df, discr_df = process_files(args.input, cfg)

    print(f"✅ Blocchi letti: {len(detail_df)}")
    write_output_excel(args.output, detail_df, totals_df, discr_df)
    print(f"✅ Output creato: {args.output}")


if __name__ == "__main__":
    main()

