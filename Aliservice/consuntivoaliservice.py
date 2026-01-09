#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aliservice — Calcolatore blocchi

NOTA: Aliservice è un'AGENZIA che gestisce più TOUR OPERATOR.
Nel file di input, si cerca la colonna "AGENZIA" (non "TOUR OPERATOR") per filtrare.
Il TOUR OPERATOR viene letto separatamente per identificare quale tour operator
specifico è gestito dall'agenzia Aliservice.

Cosa fa:
- Legge file Excel "Piano Lavoro" (anche con più fogli)
- Filtra per AGENZIA=Aliservice e APT richiesto (opzionale)
- Legge anche TOUR OPERATOR per identificare il tour operator specifico
- Forward-fill TURNO per DATA risettando l'ordine: file -> foglio -> righe
- Blocco = (DATA, APT, TURNO_ffill_normalizzato, TOUR_OPERATOR se presente)
- Parse TURNO robusto (08–11, 8:00-11, 8.00–11.30, ecc.; -, –, —)
- Gestisce mezzanotte (fine < inizio => +1 giorno)
- Output Excel: DettaglioBlocchi, TotaliPeriodo, Discrepanze, fogli per aeroporto, TOTALE

Requisiti:
  pip install pandas openpyxl python-dateutil

Esempi:
  python consuntivoaliservice.py -i "Piano lavoro DICEMBRE 25.xlsx" -o "OUT_ALISERVICE.xlsx"
  python consuntivoaliservice.py -i "Piano lavoro DICEMBRE 25.xlsx" -o "OUT_ALISERVICE.xlsx" --apt VRN
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from datetime import datetime, date, time
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


@dataclass
class CalcConfig:
    apt_filter: Optional[List[str]]  # e.g. ["BGY"]
    to_keyword: str = "aliservice"
    rounding_extra: RoundingPolicy = field(default_factory=lambda: RoundingPolicy("CEIL", 5))  # Arrotondamento per eccesso a 5 min
    rounding_night: RoundingPolicy = field(default_factory=lambda: RoundingPolicy("NONE", 5))
    holiday_dates: Optional[set[date]] = None  # optional external list
    extra_window_minutes: int = 30  # ATD + 30 minuti per calcolo extra
    
    # Tariffe Aliservice 2025 (dalla colonna "Servizi") - come costante di classe
    pass  # Le tariffe sono definite come costante globale sotto
    
    # Festivo: +20%
    festivo_multiplier: float = 1.20
    
    # Durata base turno: 3 ore
    durata_base_ore: int = 3


# Tariffe Aliservice 2025 (dalla colonna "Servizi")
TARIFFE_SERVIZI_ALISERVICE = {
    "Tour Operator": {"base": 55.0, "extra_per_h": 15.0},
    "MICE": {"base": 65.0, "extra_per_h": 15.0},
    "Viaggi Studio": {"base": 55.0, "extra_per_h": 15.0},
    "VIP Service": {"base": 110.0, "extra_per_h": 15.0},
    "VIP Gate": {"base": 130.0, "extra_per_h": 15.0},
    "Meet & Greet": {"base": 65.0, "extra_per_h": 15.0},
}


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
    Calcola minuti notturni nella fascia 23:00-03:30 (Aliservice BGY)
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
        
        # Fascia: 23:00-03:30
        is_night = False
        if hour == 23:
            is_night = True
        elif hour >= 0 and hour < 3:
            is_night = True
        elif hour == 3 and minute < 30:
            is_night = True
        
        if is_night:
            total_minutes += 1
        
        current = next_min
    
    return total_minutes


def compute_turno_eur(servizio_tipo: str, arrivi_trf: Optional[str], cfg: CalcConfig) -> float:
    """
    Calcola importo turno base secondo tipo servizio
    Se arrivi_trf contiene "M&G" → Meet & Greet (€65)
    Altrimenti usa servizio_tipo dalla colonna "Servizi"
    """
    # Prima verifica arrivi/trf per M&G (Meet & Greet)
    if arrivi_trf and pd.notna(arrivi_trf):
        arrivi_str = str(arrivi_trf).strip().upper()
        if "M&G" in arrivi_str or "M G" in arrivi_str or "MEET" in arrivi_str:
            return TARIFFE_SERVIZI_ALISERVICE["Meet & Greet"]["base"]
    
    # Poi verifica tipo servizio dalla colonna "Servizi"
    if servizio_tipo:
        servizio_norm = str(servizio_tipo).strip()
        
        # Cerca corrispondenza (case-insensitive)
        for key, tariffa in TARIFFE_SERVIZI_ALISERVICE.items():
            if key.lower() in servizio_norm.lower() or servizio_norm.lower() in key.lower():
                return tariffa["base"]
    
    # Default: Tour Operator (€55)
    return TARIFFE_SERVIZI_ALISERVICE["Tour Operator"]["base"]


def compute_extra_min(end_dt: pd.Timestamp, atd_dt: Optional[pd.Timestamp], no_dec: bool, cfg: CalcConfig) -> Tuple[int, int]:
    """
    Calcola minuti extra: ATD - fine_turno_base
    Solo se DEC (non NO DEC)
    Arrotondamento per eccesso a multipli di 5 min
    
    Returns: (extra_min_raw, extra_min_rounded)
    """
    if no_dec or pd.isna(end_dt) or atd_dt is None or pd.isna(atd_dt):
        return (0, 0)
    
    # Extra = ATD - fine_turno_base
    delta = atd_dt - end_dt
    if delta.total_seconds() <= 0:
        return (0, 0)
    
    extra_min_raw = int(delta.total_seconds() / 60)
    
    # Arrotondamento per eccesso a multipli di 5 min
    extra_min_rounded = cfg.rounding_extra.apply(extra_min_raw)
    
    return (extra_min_raw, extra_min_rounded)


def compute_extra_eur(extra_min: int, servizio_tipo: str, cfg: CalcConfig) -> float:
    """
    Calcola importo extra: extra_min / 60 × €15
    """
    if extra_min <= 0:
        return 0.0
    
    # Tutti i servizi hanno €15/h extra
    extra_h = extra_min / 60.0
    return round(extra_h * 15.0, 2)


def compute_night_eur(night_min: int, cfg: CalcConfig) -> float:
    """
    Calcola importo notturno: minuti × €0,031
    """
    if night_min <= 0:
        return 0.0
    
    return round(night_min * 0.031, 2)  # €0,031/min per Aliservice BGY


def is_festivo_from_giorno(giorno_val: Optional[str]) -> bool:
    """
    Verifica se è festivo dalla colonna "giorno"
    Cerca la parola "festivo" (case-insensitive)
    """
    if not giorno_val or pd.isna(giorno_val):
        return False
    
    giorno_str = str(giorno_val).strip().lower()
    return "festivo" in giorno_str


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
    Per Aliservice: cerca AGENZIA (non TOUR OPERATOR) per il filtro
    """
    return {
        "data": find_col(df, [r"^DATA$", r"\bDATE\b", r"^data$"]),
        "agenzia": find_col(df, [r"^AGENZIA$", r"\bAGENCY\b"]),  # Aliservice è un'AGENZIA
        "tour_operator": find_col(df, [r"TOUR\s*OPERATOR", r"^TO$", r"\bOPERATORE\b"]),  # Tour operator gestito dall'agenzia
        "servizi": find_col(df, [r"^SERVIZI$", r"^Servizi$", r"\bSERVIZIO\b"]),  # Tipo servizio (Tour Operator, MICE, VIP, ecc.)
        "arrivi_trf": find_col(df, [r"^ARRIVI/TRF$", r"^arrivi/trf$", r"^ARRIVI\s*TRF$", r"^arrivi\s*trf$", r"^ARRIVI$", r"^TRF$", r"\bARRIVI\b", r"\bTRF\b"]),  # Campo arrivi/trf (colonna I) - M&G = Meet & Greet
        "giorno": find_col(df, [r"^GIORNO$", r"^giorno$", r"\bDAY\b"]),  # Per verificare festivo
        "convocazione": find_col(df, [r"^CONVOCAZIONE$", r"^conv\.ne$", r"^conv\.?ne$", r"\bCONV\b"]),  # Convocazione
        "apt": find_col(df, [r"^APT$", r"\bAEROPORTO\b", r"\bSCALO\b", r"^apt$"]),
        "turno": find_col(df, [r"^TURNO$", r"^TURNO\s*ASSISTENTE$", r"\bTURNI\b", r"^turni$", r"^turno$"]),
        "fine_turno": find_col(df, [r"^FINE\s*TURNO$", r"^fine\s*turno$"]),  # Fine turno esplicita
        "atd": find_col(df, [r"^ATD$", r"\bORARIO\s*ATD\b", r"^atd$"]),
        "std": find_col(df, [r"^STD$", r"\bORARIO\s*STD\b", r"^std$"]),
        "importo": find_col(df, [r"^IMPORTO$", r"\bTOTALE\b", r"^COSTO\s*$", r"^importo$"]),
        "ore_extra": find_col(df, [r"\bORE\s*EXTRA\b", r"^EXTRA$", r"\bEXTRA\s*(MIN|ORE)\b", r"^ore\s*extra$"]),
        "notturno": find_col(df, [r"^NOTTURNO$", r"\bNIGHT\b", r"^Notturno$"]),
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
    agenzia: Optional[str] = None  # AGENZIA (es. "Aliservice")
    tour_operator: Optional[str] = None  # TOUR OPERATOR gestito dall'agenzia
    servizio_tipo: Optional[str] = None  # Tipo servizio (Tour Operator, MICE, VIP, ecc.)
    arrivi_trf: Optional[str] = None  # Campo arrivi/trf (colonna I) - M&G = Meet & Greet
    turno_raw_ffill: str = ""
    turno_norm: str = ""
    start_dt: Optional[pd.Timestamp] = None
    end_dt: Optional[pd.Timestamp] = None
    durata_min: int = 0
    no_dec: bool = False
    festivo_flag: bool = False  # Festivo dalla colonna "giorno"
    first_source: Optional[SourceRowRef] = None
    atd_list: List[pd.Timestamp] = field(default_factory=list)
    std_list: List[pd.Timestamp] = field(default_factory=list)
    assistente: Optional[str] = None
    errore: Optional[str] = None  # Messaggio di errore se i dati non sono validi


def iter_excel_sheets(file_path: str) -> Iterable[Tuple[str, pd.DataFrame]]:
    """Itera su tutti i fogli del file Excel"""
    xls = pd.ExcelFile(file_path)
    for sheet in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet)
        yield sheet, df


def process_files(input_files: List[str], cfg: CalcConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Legge e processa i file Piano Lavoro per Aliservice
    
    IMPORTANTE: Filtra per AGENZIA (non TOUR OPERATOR), poiché Aliservice è un'agenzia
    che gestisce più tour operator. Il TOUR OPERATOR viene letto e salvato separatamente.
    
    Returns: (detail_blocks_df, totals_df, discrepancies_df)
    Per ora solo lettura, senza calcoli (da implementare secondo regole Aliservice)
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

            # Filter per AGENZIA (Aliservice è un'AGENZIA, non un tour operator)
            if cols["agenzia"]:
                mask_agenzia = sdf[cols["agenzia"]].astype(str).str.contains(cfg.to_keyword, case=False, na=False)
                sdf = sdf[mask_agenzia].copy()
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
            ).astype(int)

            # Extract colonne aggiuntive
            assistente_col = cols["assistente"]
            agenzia_col = cols["agenzia"]
            tour_operator_col = cols["tour_operator"]
            servizi_col = cols["servizi"]
            arrivi_trf_col = cols["arrivi_trf"]  # Colonna I: arrivi/trf (M&G = Meet & Greet)
            giorno_col = cols["giorno"]
            convocazione_col = cols["convocazione"]
            fine_turno_col = cols["fine_turno"]

            # Gestisci caso turno mancante: inizio = convocazione - 15 min, fine = inizio + 3h
            if convocazione_col:
                sdf["__convocazione"] = sdf[convocazione_col].apply(parse_time_value)
                # Se turno manca, calcola da convocazione
                mask_no_turno = sdf["__start_str"].isna()
                if mask_no_turno.any():
                    for idx in sdf[mask_no_turno].index:
                        conv = sdf.loc[idx, "__convocazione"]
                        if conv:
                            hh, mm = conv
                            # Inizio = convocazione - 15 min
                            conv_dt = to_dt(sdf.loc[idx, "__date"], f"{hh:02d}:{mm:02d}")
                            start_dt = conv_dt - pd.Timedelta(minutes=15)
                            # Fine = inizio + 3h
                            end_dt = start_dt + pd.Timedelta(hours=cfg.durata_base_ore)
                            sdf.loc[idx, "__start_dt"] = start_dt
                            sdf.loc[idx, "__end_dt"] = end_dt
                            sdf.loc[idx, "__start_str"] = start_dt.strftime("%H:%M")
                            sdf.loc[idx, "__end_str"] = end_dt.strftime("%H:%M")
                            sdf.loc[idx, "__turno_norm"] = f"{sdf.loc[idx, '__start_str']}-{sdf.loc[idx, '__end_str']}"
                            sdf.loc[idx, "__durata_min"] = int((end_dt - start_dt).total_seconds() / 60)

            # Iterate rows and aggregate by block
            for idx, r in sdf.iterrows():
                d = r["__date"]
                apt = str(r[cols["apt"]]).strip() if cols["apt"] else ""
                agenzia_val = str(r[agenzia_col]).strip() if agenzia_col and agenzia_col in r.index and pd.notna(r[agenzia_col]) else ""
                tour_operator_val = str(r[tour_operator_col]).strip() if tour_operator_col and tour_operator_col in r.index and pd.notna(r[tour_operator_col]) else ""
                servizio_tipo = str(r[servizi_col]).strip() if servizi_col and servizi_col in r.index and pd.notna(r[servizi_col]) else ""
                arrivi_trf_val = str(r[arrivi_trf_col]).strip() if arrivi_trf_col and arrivi_trf_col in r.index and pd.notna(r[arrivi_trf_col]) else ""
                giorno_val = str(r[giorno_col]).strip() if giorno_col and giorno_col in r.index and pd.notna(r[giorno_col]) else ""
                turno_norm = str(r["__turno_norm"]).strip() if pd.notna(r.get("__turno_norm")) else ""
                turno_ffill_raw = str(r["__turno_ffill"]).strip() if pd.notna(r.get("__turno_ffill")) else ""
                assistente_val = str(r[assistente_col]).strip() if assistente_col and assistente_col in r.index and pd.notna(r[assistente_col]) else ""
                no_dec = r["__no_dec"] if pd.notna(r.get("__no_dec")) else False
                festivo_flag = is_festivo_from_giorno(giorno_val)

                # Se turno_norm è vuoto, usa un placeholder per la chiave
                if not turno_norm:
                    turno_norm = f"ERRORE_{idx}"

                # Chiave include anche tour_operator se presente (per distinguere blocchi di tour operator diversi)
                if tour_operator_val:
                    key = (d, apt, turno_norm, tour_operator_val)
                else:
                    key = (d, apt, turno_norm)

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
                    start_dt_val = r["__start_dt"]
                    if pd.notna(start_dt_val) and tdt < start_dt_val:
                        tdt = tdt + pd.Timedelta(days=1)
                    std_dt_list.append(tdt)

                # Fine turno = ATD (se manca → STD)
                # Per Aliservice: fine turno effettivo è ATD, non end_dt del turno
                fine_turno_dt = None
                if atd_dt_list:
                    fine_turno_dt = max(atd_dt_list)  # Prendi l'ultimo ATD
                elif std_dt_list:
                    fine_turno_dt = max(std_dt_list)  # Se manca ATD, usa STD
                else:
                    # Se manca anche STD, usa end_dt del turno
                    fine_turno_dt = r["__end_dt"] if pd.notna(r.get("__end_dt")) else None

                # Se fine_turno_dt < start_dt (oltre mezzanotte) => +1 giorno
                start_dt_val = r["__start_dt"]
                if pd.notna(start_dt_val) and pd.notna(fine_turno_dt) and fine_turno_dt < start_dt_val:
                    fine_turno_dt = fine_turno_dt + pd.Timedelta(days=1)

                # Aggrega o crea nuovo blocco
                if key in blocks:
                    b = blocks[key]
                    b.atd_list.extend(atd_dt_list)
                    b.std_list.extend(std_dt_list)
                    # Aggiorna fine_turno se ATD è più tardi
                    if fine_turno_dt and (b.end_dt is None or fine_turno_dt > b.end_dt):
                        b.end_dt = fine_turno_dt
                else:
                    # Fine turno base = start_dt + 3h
                    end_dt_base = r["__end_dt"] if pd.notna(r.get("__end_dt")) else None
                    if pd.notna(start_dt_val):
                        if end_dt_base is None:
                            end_dt_base = start_dt_val + pd.Timedelta(hours=cfg.durata_base_ore)
                    
                    blocks[key] = BlockAgg(
                        date=d,
                        apt=apt,
                        agenzia=agenzia_val if agenzia_val else None,
                        tour_operator=tour_operator_val if tour_operator_val else None,
                        servizio_tipo=servizio_tipo if servizio_tipo else None,
                        arrivi_trf=arrivi_trf_val if arrivi_trf_val else None,  # Campo arrivi/trf (M&G = Meet & Greet)
                        turno_raw_ffill=turno_ffill_raw,
                        turno_norm=turno_norm,
                        start_dt=start_dt_val,
                        end_dt=fine_turno_dt if fine_turno_dt else end_dt_base,  # Fine turno = ATD (o STD o end_dt)
                        durata_min=int(r["__durata_min"]) if pd.notna(r["__durata_min"]) else 0,
                        no_dec=no_dec,
                        festivo_flag=festivo_flag,
                        first_source=SourceRowRef(
                            file=file_path,
                            sheet=sheet_name,
                            row_index=int(r["__sheet_row_order"]),
                            original_order=int(r["__global_order"]),
                        ),
                        atd_list=atd_dt_list,
                        std_list=std_dt_list,
                        assistente=assistente_val if assistente_val else None,
                    )

    # Converti blocchi in DataFrame per output
    rows_detail = []

    for key, b in sorted(blocks.items(), key=lambda kv: (kv[1].date, kv[1].apt, kv[1].first_source.original_order if kv[1].first_source else 0)):
        # Se c'è un errore, metti tutti i valori a zero
        if b.errore:
            rows_detail.append({
                "DATA": b.date.strftime("%d/%m/%Y") if pd.notna(b.date) else "",
                "APT": b.apt,
                "AGENZIA": b.agenzia if b.agenzia else "",
                "TOUR OPERATOR": b.tour_operator if b.tour_operator else "",
                "ASSISTENTE": b.assistente if b.assistente else "",
                "TURNO_FFILL": b.turno_raw_ffill,
                "TURNO_NORMALIZZATO": b.turno_norm,
                "INIZIO_DT": b.start_dt,
                "FINE_DT": b.end_dt,
                "DURATA_TURNO_MIN": 0,
                "NO_DEC": "Sì" if b.no_dec else "No",
                "ATD_SCELTO": b.atd_list[0] if b.atd_list else None,
                "STD_SCELTO": b.std_list[0] if b.std_list else None,
                "TURNO_EUR": 0.0,
                "EXTRA_MIN": 0,
                "EXTRA_EUR": 0.0,
                "NOTTE_MIN": 0,
                "NOTTE_EUR": 0.0,
                "FESTIVO": b.festivo_flag,
                "TOTALE_BLOCCO_EUR": 0.0,
                "ERRORE": b.errore,
                "SRC_FILE": b.first_source.file if b.first_source else "",
                "SRC_SHEET": b.first_source.sheet if b.first_source else "",
                "SRC_ROW0": b.first_source.row_index + 2 if b.first_source else 0,
            })
            continue

        # Calcolo turno base secondo tipo servizio
        # Se arrivi_trf contiene "M&G" → Meet & Greet (€65)
        # Altrimenti usa servizio_tipo dalla colonna "Servizi"
        servizio_tipo = b.servizio_tipo if b.servizio_tipo else None
        arrivi_trf = b.arrivi_trf if b.arrivi_trf else None
        turno_eur = compute_turno_eur(servizio_tipo, arrivi_trf, cfg)

        # Fine turno base = start_dt + 3h
        fine_turno_base = None
        if pd.notna(b.start_dt):
            fine_turno_base = b.start_dt + pd.Timedelta(hours=cfg.durata_base_ore)

        # ATD scelto (ultimo disponibile)
        atd_sel = b.atd_list[-1] if b.atd_list else None
        if not atd_sel and b.std_list:
            atd_sel = b.std_list[-1]

        # Calcolo extra: ATD - fine_turno_base (solo se DEC)
        extra_min_raw, extra_min = compute_extra_min(fine_turno_base, atd_sel, b.no_dec, cfg)
        extra_eur = compute_extra_eur(extra_min, servizio_tipo, cfg)

        # Calcolo notturno: minuti nella fascia 23:00-03:30
        night_min_raw = 0
        if pd.notna(b.start_dt) and pd.notna(b.end_dt):
            # Minuti notturni nel turno base
            night_turno = night_minutes(b.start_dt, fine_turno_base if fine_turno_base else b.end_dt)
            # Minuti notturni nelle ore extra
            night_extra = 0
            if extra_min_raw > 0 and (not b.no_dec) and extra_min > 0 and fine_turno_base:
                extra_end = fine_turno_base + pd.Timedelta(minutes=extra_min)
                night_extra = night_minutes(fine_turno_base, extra_end)
            night_min_raw = night_turno + night_extra

        night_min = night_min_raw  # Nessun arrotondamento per notturno
        night_eur = compute_night_eur(night_min, cfg)

        # Festivo: +20% su tutto (turno + extra + notturno)
        if b.festivo_flag:
            subtotal = (turno_eur + extra_eur + night_eur) * cfg.festivo_multiplier
        else:
            subtotal = turno_eur + extra_eur + night_eur
        totale = round(subtotal, 2)

        # Format H:MM
        def hmm(m: int) -> str:
            return f"{m // 60}:{m % 60:02d}"

        rows_detail.append({
            "DATA": b.date.strftime("%d/%m/%Y") if pd.notna(b.date) else "",
            "APT": b.apt,
            "AGENZIA": b.agenzia if b.agenzia else "",
            "TOUR OPERATOR": b.tour_operator if b.tour_operator else "",
            "SERVIZI": b.servizio_tipo if b.servizio_tipo else "",
            "ARRIVI/TRF": b.arrivi_trf if b.arrivi_trf else "",  # Campo arrivi/trf (M&G = Meet & Greet)
            "ASSISTENTE": b.assistente if b.assistente else "",
            "TURNO_FFILL": b.turno_raw_ffill,
            "TURNO_NORMALIZZATO": b.turno_norm,
            "INIZIO_DT": b.start_dt,
            "FINE_DT": b.end_dt,
            "DURATA_TURNO_MIN": b.durata_min,
            "NO_DEC": "Sì" if b.no_dec else "No",
            "ATD_SCELTO": atd_sel,
            "STD_SCELTO": b.std_list[0] if b.std_list else None,
            "TURNO_EUR": round(turno_eur, 2),
            "EXTRA_MIN": int(extra_min),
            "EXTRA_EUR": round(extra_eur, 2),
            "NOTTE_MIN": int(night_min),
            "NOTTE_EUR": round(night_eur, 2),
            "FESTIVO": b.festivo_flag,
            "TOTALE_BLOCCO_EUR": totale,
            "ERRORE": "",
            "SRC_FILE": b.first_source.file if b.first_source else "",
            "SRC_SHEET": b.first_source.sheet if b.first_source else "",
            "SRC_ROW0": b.first_source.row_index + 2 if b.first_source else 0,
        })

    detail_df = pd.DataFrame(rows_detail)

    # Totals by period (come Alpitour/Veratour)
    if detail_df.empty:
        totals_df = pd.DataFrame(columns=[
            "AGENZIA", "TOUR OPERATOR", "PERIODO", "TOT_TURNO_EUR", "TOT_EXTRA_MIN", "TOT_EXTRA_H:MM", "TOT_EXTRA_EUR",
            "TOT_NOTTE_MIN", "TOT_NOTTE_EUR", "TOT_TOTALE_EUR"
        ])
        discr_df = pd.DataFrame(columns=[
            "DATA", "APT", "AGENZIA", "TOUR OPERATOR", "TURNO_NORMALIZZATO",
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

    # Raggruppa per AGENZIA, TOUR OPERATOR e PERIODO se presenti
    groupby_cols = ["PERIODO"]
    if "AGENZIA" in detail_df.columns:
        groupby_cols = ["AGENZIA"] + groupby_cols
    if "TOUR OPERATOR" in detail_df.columns:
        groupby_cols = groupby_cols[:1] + ["TOUR OPERATOR"] + groupby_cols[1:] if "AGENZIA" in detail_df.columns else ["TOUR OPERATOR"] + groupby_cols
    
    totals = detail_df.groupby(groupby_cols, as_index=False).agg(
        TOT_TURNO_EUR=("TURNO_EUR", "sum"),
        TOT_EXTRA_MIN=("EXTRA_MIN", "sum"),
        TOT_EXTRA_EUR=("EXTRA_EUR", "sum"),
        TOT_NOTTE_MIN=("NOTTE_MIN", "sum"),
        TOT_NOTTE_EUR=("NOTTE_EUR", "sum"),
        TOT_TOTALE_EUR=("TOTALE_BLOCCO_EUR", "sum"),
    )

    totals["TOT_EXTRA_H:MM"] = totals["TOT_EXTRA_MIN"].apply(sum_hmm)
    
    # Riordina colonne
    if "AGENZIA" in totals.columns and "TOUR OPERATOR" in totals.columns:
        totals = totals[[
            "AGENZIA", "TOUR OPERATOR", "PERIODO", "TOT_TURNO_EUR", "TOT_EXTRA_MIN", "TOT_EXTRA_H:MM", "TOT_EXTRA_EUR",
            "TOT_NOTTE_MIN", "TOT_NOTTE_EUR", "TOT_TOTALE_EUR"
        ]]
    elif "TOUR OPERATOR" in totals.columns:
        totals = totals[[
            "TOUR OPERATOR", "PERIODO", "TOT_TURNO_EUR", "TOT_EXTRA_MIN", "TOT_EXTRA_H:MM", "TOT_EXTRA_EUR",
            "TOT_NOTTE_MIN", "TOT_NOTTE_EUR", "TOT_TOTALE_EUR"
        ]]
    else:
        totals = totals[[
            "PERIODO", "TOT_TURNO_EUR", "TOT_EXTRA_MIN", "TOT_EXTRA_H:MM", "TOT_EXTRA_EUR",
            "TOT_NOTTE_MIN", "TOT_NOTTE_EUR", "TOT_TOTALE_EUR"
        ]]

    # Riga totale mese
    agenzia_val = detail_df["AGENZIA"].iloc[0] if "AGENZIA" in detail_df.columns else ""
    tour_operator_val = detail_df["TOUR OPERATOR"].iloc[0] if "TOUR OPERATOR" in detail_df.columns else ""
    month_row = pd.DataFrame([{
        "AGENZIA": agenzia_val if "AGENZIA" in detail_df.columns else "",
        "TOUR OPERATOR": tour_operator_val if "TOUR OPERATOR" in detail_df.columns else "",
        "PERIODO": "MESE",
        "TOT_TURNO_EUR": float(detail_df["TURNO_EUR"].sum()),
        "TOT_EXTRA_MIN": int(detail_df["EXTRA_MIN"].sum()),
        "TOT_EXTRA_H:MM": sum_hmm(int(detail_df["EXTRA_MIN"].sum())),
        "TOT_EXTRA_EUR": float(detail_df["EXTRA_EUR"].sum()),
        "TOT_NOTTE_MIN": int(detail_df["NOTTE_MIN"].sum()),
        "TOT_NOTTE_EUR": float(detail_df["NOTTE_EUR"].sum()),
        "TOT_TOTALE_EUR": float(detail_df["TOTALE_BLOCCO_EUR"].sum()),
    }])
    
    # Se AGENZIA/TOUR OPERATOR non sono nel month_row ma sono nelle colonne, aggiungili
    if "AGENZIA" not in month_row.columns and "AGENZIA" in totals.columns:
        month_row.insert(0, "AGENZIA", agenzia_val)
    if "TOUR OPERATOR" not in month_row.columns and "TOUR OPERATOR" in totals.columns:
        insert_pos = 1 if "AGENZIA" in month_row.columns else 0
        month_row.insert(insert_pos, "TOUR OPERATOR", tour_operator_val)

    totals_df = pd.concat([totals, month_row], ignore_index=True)

    # cleanup helper col
    detail_df = detail_df.drop(columns=["__DATE_TS"], errors="ignore")

    # Discrepanze (vuoto per ora, ma con colonne corrette)
    discr_df = pd.DataFrame(columns=[
        "DATA", "APT", "AGENZIA", "TOUR OPERATOR", "TURNO_NORMALIZZATO",
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
        'Agenzia': df_apt['AGENZIA'].fillna('') if 'AGENZIA' in df_apt.columns else pd.Series([''] * len(df_apt)),
        'Tour Operator': df_apt['TOUR OPERATOR'].fillna('') if 'TOUR OPERATOR' in df_apt.columns else pd.Series([''] * len(df_apt)),
        'Servizi': df_apt['SERVIZI'].fillna('') if 'SERVIZI' in df_apt.columns else pd.Series([''] * len(df_apt)),
        'Arrivi/TRF': df_apt['ARRIVI/TRF'].fillna('') if 'ARRIVI/TRF' in df_apt.columns else pd.Series([''] * len(df_apt)),
        'Turno': df_apt['TURNO_NORMALIZZATO'],
        'Durata': df_apt['DURATA_H:MM'],
        'Turno (€)': df_apt['TURNO_EUR'].round(2),
        'Extra (h:mm)': df_apt['EXTRA_H:MM'],
        'Extra (€)': df_apt['EXTRA_EUR'].round(2),
        'Notturno (h:mm)': df_apt['NOTTE_H:MM'],
        'Notturno (€)': df_apt['NOTTE_EUR'].round(2),
        'TOTALE (€)': df_apt['TOTALE_BLOCCO_EUR'].round(2),
    }
    
    # Add Assistente column if present (insert after Servizi)
    if 'ASSISTENTE' in df_apt.columns:
        new_cols = {'Data': output_cols['Data']}
        new_cols['Agenzia'] = output_cols['Agenzia']
        new_cols['Tour Operator'] = output_cols['Tour Operator']
        new_cols['Servizi'] = output_cols['Servizi']
        new_cols['Arrivi/TRF'] = output_cols['Arrivi/TRF']
        new_cols['Assistente'] = df_apt['ASSISTENTE'].fillna('')
        for k, v in output_cols.items():
            if k not in ['Data', 'Agenzia', 'Tour Operator', 'Servizi', 'Arrivi/TRF']:
                new_cols[k] = v
        output_cols = new_cols
    
    result_df = pd.DataFrame(output_cols)
    
    # Add total row
    total_row_dict = {
        'Data': 'TOTALE',
        'Agenzia': '',
        'Tour Operator': '',
        'Servizi': '',
        'Arrivi/TRF': '',
        'Turno': '',
        'Durata': '',
        'Turno (€)': df_apt['TURNO_EUR'].sum(),
        'Extra (h:mm)': format_minutes_to_hmm(df_apt['EXTRA_MIN'].sum()),
        'Extra (€)': df_apt['EXTRA_EUR'].sum(),
        'Notturno (h:mm)': format_minutes_to_hmm(df_apt['NOTTE_MIN'].sum()),
        'Notturno (€)': df_apt['NOTTE_EUR'].sum(),
        'TOTALE (€)': df_apt['TOTALE_BLOCCO_EUR'].sum(),
    }
    
    # Add empty Assistente in total row if column exists
    if 'ASSISTENTE' in df_apt.columns:
        new_total_dict = {'Data': total_row_dict['Data']}
        new_total_dict['Agenzia'] = total_row_dict['Agenzia']
        new_total_dict['Tour Operator'] = total_row_dict['Tour Operator']
        new_total_dict['Servizi'] = total_row_dict['Servizi']
        new_total_dict['Arrivi/TRF'] = total_row_dict['Arrivi/TRF']
        new_total_dict['Assistente'] = ''
        for k, v in total_row_dict.items():
            if k not in ['Data', 'Agenzia', 'Tour Operator', 'Servizi', 'Arrivi/TRF']:
                new_total_dict[k] = v
        total_row_dict = new_total_dict
    
    total_row = pd.DataFrame([total_row_dict])
    result_df = pd.concat([result_df, total_row], ignore_index=True)
    return result_df


def create_total_by_apt_sheet(detail_df: pd.DataFrame) -> pd.DataFrame:
    """Create total sheet grouped by airport, agenzia and tour operator"""
    if detail_df.empty:
        return pd.DataFrame(columns=['Agenzia', 'Tour Operator', 'Aeroporto', 'Blocchi', 'Assistenze', 'Extra', 'Notturno', 'TOTALE'])
    
    # Group by AGENZIA, TOUR OPERATOR, and APT
    groupby_cols = ['APT']
    if 'AGENZIA' in detail_df.columns:
        groupby_cols = ['AGENZIA'] + groupby_cols
    if 'TOUR OPERATOR' in detail_df.columns:
        groupby_cols = groupby_cols[:1] + ['TOUR OPERATOR'] + groupby_cols[1:] if 'AGENZIA' in detail_df.columns else ['TOUR OPERATOR'] + groupby_cols
    
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
        if len(groupby_cols) == 3:  # AGENZIA, TOUR OPERATOR, APT
            agenzie = [idx[0] for idx in totals_by_apt.index]
            tour_operators = [idx[1] for idx in totals_by_apt.index]
            aeroporti = [idx[2] for idx in totals_by_apt.index]
        elif len(groupby_cols) == 2:
            if 'AGENZIA' in groupby_cols:
                agenzie = [idx[0] for idx in totals_by_apt.index]
                tour_operators = [''] * len(totals_by_apt)
                aeroporti = [idx[1] for idx in totals_by_apt.index]
            else:  # TOUR OPERATOR, APT
                agenzie = [''] * len(totals_by_apt)
                tour_operators = [idx[0] for idx in totals_by_apt.index]
                aeroporti = [idx[1] for idx in totals_by_apt.index]
        else:
            agenzie = [''] * len(totals_by_apt)
            tour_operators = [''] * len(totals_by_apt)
            aeroporti = totals_by_apt.index.tolist()
    else:
        agenzie = [''] * len(totals_by_apt)
        tour_operators = [''] * len(totals_by_apt)
        aeroporti = totals_by_apt.index.tolist()
    
    result = pd.DataFrame({
        'Agenzia': agenzie,
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
        'Agenzia': result['Agenzia'],
        'Tour Operator': result['Tour Operator'],
        'Aeroporto': result['Aeroporto'],
        'Blocchi': result['Blocchi'],
        'Assistenze': result['Assistenze'].apply(format_eur),
        'Extra': result.apply(lambda x: f"{format_eur(x['Extra_eur'])} ({min_to_hours_minutes_text(x['Extra_min'])})", axis=1),
        'Notturno': result.apply(lambda x: f"{format_eur(x['Notturno_eur'])} ({min_to_hours_minutes_text(x['Notturno_min'])})", axis=1),
        'TOTALE': result['TOTALE'].apply(format_eur),
    })
    
    # Order by agenzia, tour operator, then airport
    order = ['VRN', 'BGY', 'NAP', 'VCE']
    output_df['sort_order'] = output_df['Aeroporto'].apply(lambda x: order.index(x) if x in order else 999)
    output_df = output_df.sort_values(['Agenzia', 'Tour Operator', 'sort_order']).drop('sort_order', axis=1)
    
    # Add total row
    total_row = pd.DataFrame([{
        'Agenzia': '',
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
                "DATA", "APT", "AGENZIA", "TOUR OPERATOR", "SERVIZI", "ARRIVI/TRF", "ASSISTENTE", "TURNO_FFILL", "TURNO_NORMALIZZATO",
                "INIZIO_DT", "FINE_DT", "DURATA_TURNO_MIN", "NO_DEC",
                "ATD_SCELTO", "STD_SCELTO",
                "TURNO_EUR",
                "EXTRA_MIN", "EXTRA_EUR",
                "NOTTE_MIN", "NOTTE_EUR",
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
                "DATA", "APT", "AGENZIA", "TOUR OPERATOR", "TURNO_NORMALIZZATO",
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
    parser = argparse.ArgumentParser(description="Calcolatore blocchi Aliservice")
    parser.add_argument("-i", "--input", required=True, help="File Excel Piano Lavoro")
    parser.add_argument("-o", "--output", required=True, help="File Excel output")
    parser.add_argument("--apt", nargs="+", help="Filtra aeroporti (es: --apt VRN BGY)")
    parser.add_argument("--to", default="aliservice", help="Keyword tour operator (default: aliservice)")

    args = parser.parse_args()

    cfg = CalcConfig(
        apt_filter=args.apt,
        to_keyword=args.to,
    )

    print(f"📄 Elaborazione file: {args.input}")
    detail_df, totals_df, discr_df = process_files([args.input], cfg)

    print(f"✅ Blocchi letti: {len(detail_df)}")
    write_output_excel(args.output, detail_df, totals_df, discr_df)
    print(f"✅ Output creato: {args.output}")


if __name__ == "__main__":
    main()

