#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Alpitour 2025 — Calcolatore blocchi (Scay/Alpitour rules)

Cosa fa:
- Legge file Excel "PianoLavoroOTTOBRE 25 .xlsx" (anche con più fogli)
- Filtra TO=Alpitour e APT richiesto (opzionale)
- Forward-fill TURNO per DATA rispettando l'ordine: file -> foglio -> righe
- Blocco = (DATA, APT, TURNO_ffill_normalizzato)
- Dedup blocchi anche cross-fogli/cross-file unendo ATD e STD
- Parse TURNO robusto (08–11, 8:00-11, 8.00–11.30, ecc.; -, –, —)
- Gestisce mezzanotte (fine < inizio => +1 giorno)
- Regola decollo => EXTRA: ultimo ATD (o STD se ATD non disponibile) + 30 minuti > fine_turno
- "NO DEC" nel TURNO => extra = 0 (ma notturno dentro turno resta)
- Turno € = tariffe fisse per BGY (3h=75, 4h=90, 5h=105, 6h=120, 7h=135, 8h=150)
              o VRN (3h=80, 4h=95, 5h=110, 6h=125, 7h=140, 8h=155)
              oltre 3h: +€15/ora pro-rata
- Extra € = extra_min/60 * 20 (arrotondato per eccesso al multiplo di 5 minuti)
- Notturno (23:00–06:00) su turno + extra: maggiorazione 15% = €0,0625/minuto
- Festivi: +20% su turno e extra (non su notturno)
- Output Excel: DettaglioBlocchi, TotaliPeriodo, Discrepanze

Requisiti:
  pip install pandas openpyxl python-dateutil

Esempi:
  python consuntivoalpitour.py -o "OUT_ALPITOUR.xlsx" --apt VRN
  python consuntivoalpitour.py -o "OUT_ALPITOUR.xlsx" --apt BGY VRN
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
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
    apt_filter: Optional[List[str]]  # e.g. ["VRN"]
    to_keyword: str = "alpitour"
    rate_extra_per_h: float = 20.0  # Alpitour 2025: €20,00/ora
    over_3h_rate_per_h: float = 15.0  # Alpitour 2025: €15,00/ora oltre le prime 3h
    night_eur_per_min: float = 0.0625  # Alpitour 2025: maggiorazione 15% = €3,75/h = €0,0625/min
    rounding_extra: RoundingPolicy = RoundingPolicy("CEIL", 5)  # Alpitour: sempre arrotondamento per eccesso al multiplo di 5
    rounding_night: RoundingPolicy = RoundingPolicy("NONE", 5)
    festivo_multiplier: float = 1.20  # Alpitour 2025: +20% su turno e extra
    holiday_dates: Optional[set[date]] = None  # optional external list
    extra_window_minutes: int = 30  # Alpitour: ATD + 30 minuti per calcolo extra
    
    def get_turno_rates(self, apt: str) -> Dict[int, float]:
        """
        Restituisce le tariffe turno per APT secondo Alpitour 2025.
        BGY: 3h=75, 4h=90, 5h=105, 6h=120, 7h=135, 8h=150
        VRN: 3h=80, 4h=95, 5h=110, 6h=125, 7h=140, 8h=155
        """
        apt_upper = apt.upper()
        if apt_upper == "BGY":
            return {3: 75.0, 4: 90.0, 5: 105.0, 6: 120.0, 7: 135.0, 8: 150.0}
        elif apt_upper == "VRN":
            return {3: 80.0, 4: 95.0, 5: 110.0, 6: 125.0, 7: 140.0, 8: 155.0}
        else:
            # Default a BGY se APT non riconosciuto
            return {3: 75.0, 4: 90.0, 5: 105.0, 6: 120.0, 7: 135.0, 8: 150.0}


# -----------------------------
# Helpers: parsing + normalization
# -----------------------------

TIME_SEP_PATTERN = r"[-–—]"
TIME_TOKEN = r"(?:(\d{1,2})(?:[:\.](\d{1,2}))?)"
TIME_RANGE_RE = re.compile(rf"{TIME_TOKEN}\s*{TIME_SEP_PATTERN}\s*{TIME_TOKEN}", re.IGNORECASE)

NO_DEC_RE = re.compile(r"\bno\s*dec\b", re.IGNORECASE)


def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def normalize_hyphens(s: str) -> str:
    return s.replace("–", "-").replace("—", "-").replace("−", "-")


def parse_excel_date(x) -> Optional[pd.Timestamp]:
    if pd.isna(x):
        return None
    try:
        ts = pd.to_datetime(x, dayfirst=True, errors="coerce")
        if pd.isna(ts):
            return None
        return ts.normalize()
    except Exception:
        return None


def parse_time_value(x) -> Optional[Tuple[int, int]]:
    """
    Convert possible Excel time representations into (hh, mm).
    Accepts:
    - datetime/time
    - pandas Timestamp
    - floats (Excel times)
    - strings 'H', 'HH', 'H:MM', 'HH.MM', 'HH:MM:SS'
    """
    if x is None or pd.isna(x):
        return None

    # datetime/time
    if isinstance(x, time):
        return (x.hour, x.minute)
    if isinstance(x, (datetime, pd.Timestamp)):
        return (x.hour, x.minute)

    # numeric Excel time (fraction of day)
    if isinstance(x, (int, float, np.floating)) and not isinstance(x, bool):
        # heuristic: excel time usually in [0,1)
        val = float(x)
        if 0 <= val < 1.0:
            total_minutes = int(round(val * 24 * 60))
            hh = (total_minutes // 60) % 24
            mm = total_minutes % 60
            return (hh, mm)

    s = str(x).strip()
    if not s:
        return None

    s = s.replace(",", ":")
    s = s.replace(".", ":")
    s = s.replace(";", ":")  # Gestisce punto e virgola (es: "20;30" -> "20:30")
    # hh:mm:ss
    m = re.match(r"^\s*(\d{1,2})\s*:\s*(\d{1,2})(?:\s*:\s*(\d{1,2}))?\s*$", s)
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2))
        if 0 <= hh <= 47 and 0 <= mm <= 59:
            return (hh % 24, mm)

    # single hour "8" or "08"
    m = re.match(r"^\s*(\d{1,2})\s*$", s)
    if m:
        hh = int(m.group(1))
        if 0 <= hh <= 47:
            return (hh % 24, 0)

    return None


def parse_turno(turno_raw: str) -> Tuple[Optional[str], Optional[str], bool, str]:
    """
    Returns:
      start_str "HH:MM", end_str "HH:MM", no_dec flag, normalized turno string for grouping.
    If no interpretable time range -> (None,None,no_dec,normalized_text)
    """
    s = "" if turno_raw is None else str(turno_raw)
    s = normalize_spaces(s)
    no_dec = bool(NO_DEC_RE.search(s))

    # Standardize hyphens - prima normalizza i trattini
    s2 = normalize_hyphens(s)
    
    # Gestione punti e punti e virgola: possono essere separatori tra orari o dentro gli orari
    # Pattern tipo "13:30.17:00" o "13;15-16;15" dove punto/punto e virgola separano due orari
    # Convertiamo "HH:MM.HH:MM" o "HH;MM-HH;MM" in "HH:MM-HH:MM"
    s2 = re.sub(r'(\d{1,2}[:;]\d{1,2})[\.;](\d{1,2}[:;]\d{1,2})', r'\1-\2', s2)
    # Poi convertiamo i punti e punti e virgola rimasti in due punti (per gli orari tipo "8.30" -> "8:30" o "13;15" -> "13:15")
    s2 = s2.replace(".", ":")
    s2 = s2.replace(";", ":")

    # Keep original prefixes (A/B/C etc.) for grouping, BUT normalize time range inside
    m = TIME_RANGE_RE.search(s2)
    if not m:
        # Tentativo di gestire turni incompleti tipo "20:25-DEC" (manca orario fine)
        # Assumiamo che finisca a mezzanotte (00:00 del giorno successivo)
        single_time_pattern = re.compile(rf"{TIME_TOKEN}\s*{TIME_SEP_PATTERN}", re.IGNORECASE)
        m_single = single_time_pattern.search(s2)
        if m_single:
            h1, m1 = m_single.group(1), m_single.group(2)
            h1 = int(h1)
            m1 = int(m1) if m1 is not None else 0
            start = f"{h1:02d}:{m1:02d}"
            end = "00:00"  # Mezzanotte del giorno successivo
            # Normalizza il turno
            norm_range = f"{start}-{end}"
            s_norm = s2[:m_single.start()] + norm_range + s2[m_single.end():]
            s_norm = normalize_spaces(s_norm)
            if no_dec:
                s_norm = NO_DEC_RE.sub("NO DEC", s_norm)
            return (start, end, no_dec, s_norm)
        return (None, None, no_dec, s2)

    h1, m1, h2, m2 = m.group(1), m.group(2), m.group(3), m.group(4)
    h1 = int(h1)
    m1 = int(m1) if m1 is not None else 0
    h2 = int(h2)
    m2 = int(m2) if m2 is not None else 0

    start = f"{h1:02d}:{m1:02d}"
    end = f"{h2:02d}:{m2:02d}"

    # Replace the found range with normalized "HH:MM-HH:MM" (single hyphen)
    norm_range = f"{start}-{end}"
    s_norm = s2[:m.start()] + norm_range + s2[m.end():]
    s_norm = normalize_spaces(s_norm)

    # Normalize NO DEC token to "NO DEC" for stable grouping
    if no_dec:
        s_norm = NO_DEC_RE.sub("NO DEC", s_norm)

    return (start, end, no_dec, s_norm)


def to_dt(d: pd.Timestamp, hhmm: str) -> pd.Timestamp:
    hh, mm = map(int, hhmm.split(":"))
    return d + pd.Timedelta(hours=hh, minutes=mm)


def night_minutes(interval_start: pd.Timestamp, interval_end: pd.Timestamp) -> int:
    """
    Minutes overlapping [23:00, 06:00) across relevant nights (Alpitour 2025).
    Including previous night window as needed.
    """
    if interval_end <= interval_start:
        return 0

    total = 0
    base = interval_start.normalize() - pd.Timedelta(days=1)
    for k in range(0, 3):  # prev, same, next
        day = base + pd.Timedelta(days=k)
        n_start = day + pd.Timedelta(hours=23)
        n_end = day + pd.Timedelta(days=1, hours=6)  # Alpitour: fino alle 06:00
        s = max(interval_start, n_start)
        e = min(interval_end, n_end)
        if e > s:
            total += int((e - s).total_seconds() // 60)
    return total


def parse_minutes_from_cell(x) -> Optional[int]:
    """
    For comparison: convert "H:MM", "HH:MM:SS", or integer minutes to minutes.
    """
    if x is None or pd.isna(x):
        return None
    if isinstance(x, (int, float, np.floating)) and not isinstance(x, bool):
        # If it's a fraction of day like Excel time, interpret as hours:minutes
        tv = parse_time_value(x)
        if tv:
            return tv[0] * 60 + tv[1]
        # Otherwise maybe already minutes
        if float(x).is_integer():
            return int(x)
        return None

    s = str(x).strip()
    if not s:
        return None
    s = s.replace(".", ":")
    # hh:mm:ss
    m = re.match(r"^(\d{1,2}):(\d{2})(?::\d{2})?$", s)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    # minutes integer
    if re.match(r"^\d+$", s):
        return int(s)
    return None


def parse_eur(x) -> Optional[float]:
    if x is None or pd.isna(x):
        return None
    if isinstance(x, (int, float, np.floating)) and not isinstance(x, bool):
        return float(x)
    s = str(x).strip()
    if not s:
        return None
    s = s.replace("€", "").replace("EUR", "").strip()
    # Italian number formatting: 1.234,56
    s = s.replace(".", "").replace(",", ".")
    m = re.findall(r"[-+]?\d*\.?\d+", s)
    if not m:
        return None
    try:
        return float(m[0])
    except Exception:
        return None


def is_truthy_festivo(x) -> bool:
    if x is None or pd.isna(x):
        return False
    s = str(x).strip().lower()
    return s in ("1", "true", "t", "si", "sì", "yes", "y", "x")


# -----------------------------
# Column detection
# -----------------------------

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
    Map:
      data, tour_operator, apt, turno, atd, std, importo, ore_extra, notturno, festivo, assistente
    Per Alpitour: la colonna TURNO può essere "TURNO" o "TURNO ASSISTENTE"
    STD è usato come fallback se ATD non è disponibile
    """
    return {
        "data": find_col(df, [r"^DATA$", r"\bDATE\b"]),
        "tour_operator": find_col(df, [r"TOUR\s*OPERATOR", r"^TO$", r"\bOPERATORE\b"]),
        "apt": find_col(df, [r"^APT$", r"\bAEROPORTO\b", r"\bSCALO\b"]),
        "turno": find_col(df, [r"^TURNO$", r"^TURNO\s*ASSISTENTE$", r"\bTURNI\b"]),
        "atd": find_col(df, [r"^ATD$", r"\bORARIO\s*ATD\b"]),
        "std": find_col(df, [r"^STD$", r"\bORARIO\s*STD\b"]),
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
    no_dec: bool
    atd_list: List[pd.Timestamp]
    std_list: List[pd.Timestamp]  # Alpitour: STD come fallback se ATD non disponibile
    festivo_flag: bool
    first_source: SourceRowRef
    assistente: Optional[str] = None
    # optional "provided" values from the first row (for discrepancy sheet)
    provided_importo: Optional[float] = None
    provided_extra_min: Optional[int] = None
    provided_night_min: Optional[int] = None
    errore: Optional[str] = None  # Messaggio di errore se i dati non sono validi


def validate_row_data(row: pd.Series, cols: Dict[str, Optional[str]], cfg: CalcConfig) -> Optional[str]:
    """
    Valida i dati di una riga e restituisce un messaggio di errore se ci sono problemi.
    Restituisce None se i dati sono validi.
    """
    errori = []
    
    # Controllo DATA
    if not cols["data"]:
        errori.append("Colonna DATA mancante")
    else:
        data_val = row.get(cols["data"])
        if pd.isna(data_val) or data_val == "":
            errori.append("DATA mancante o vuota")
        else:
            parsed_date = parse_excel_date(data_val)
            if parsed_date is None:
                errori.append(f"DATA non valida: {data_val}")
    
    # Controllo APT
    if not cols["apt"]:
        errori.append("Colonna APT mancante")
    else:
        apt_val = str(row.get(cols["apt"], "")).strip()
        if not apt_val or apt_val == "" or apt_val.lower() == "nan":
            errori.append("APT mancante o vuoto")
        else:
            # Verifica che APT sia uno dei valori attesi (BGY, VRN, ecc.)
            apt_upper = apt_val.upper()
            if cfg.apt_filter:
                if apt_upper not in [a.upper() for a in cfg.apt_filter]:
                    errori.append(f"APT non riconosciuto: {apt_val} (attesi: {', '.join(cfg.apt_filter)})")
    
    # Controllo TURNO
    if not cols["turno"]:
        errori.append("Colonna TURNO mancante")
    else:
        turno_val = row.get(cols["turno"])
        if pd.isna(turno_val) or str(turno_val).strip() == "":
            # TURNO può essere vuoto se viene forward-filled, quindi non è un errore critico qui
            pass
        else:
            turno_str = str(turno_val).strip()
            parsed = parse_turno(turno_str)
            if parsed[0] is None or parsed[1] is None:
                errori.append(f"TURNO non riconoscibile: {turno_str}")
    
    # Controllo TOUR OPERATOR (se presente)
    if cols["tour_operator"]:
        to_val = str(row.get(cols["tour_operator"], "")).strip()
        if to_val and to_val.lower() != "nan":
            if cfg.to_keyword.lower() not in to_val.lower():
                errori.append(f"TOUR OPERATOR non corrisponde: {to_val} (atteso: {cfg.to_keyword})")
    
    # Controllo ATD/STD (formato orario se presente)
    if cols["atd"]:
        atd_val = row.get(cols["atd"])
        if pd.notna(atd_val) and str(atd_val).strip() != "":
            atd_candidates = extract_atd_candidates(atd_val)
            if not atd_candidates:
                # Non è un errore critico, ma può essere un warning
                pass
    
    if cols["std"]:
        std_val = row.get(cols["std"])
        if pd.notna(std_val) and str(std_val).strip() != "":
            std_candidates = extract_atd_candidates(std_val)
            if not std_candidates:
                # Non è un errore critico, ma può essere un warning
                pass
    
    if errori:
        return "; ".join(errori)
    return None


def extract_atd_candidates(val) -> List[Tuple[int, int]]:
    """
    Extract one or more times from a cell that might contain multiple times.
    """
    if val is None or pd.isna(val):
        return []
    # If it's time-like
    tv = parse_time_value(val)
    if tv:
        return [tv]

    s = str(val).strip()
    if not s:
        return []
    s = s.replace(".", ":")
    # find all tokens like 8, 8:10, 08:10
    tokens = re.findall(r"\b(\d{1,2})(?::(\d{1,2}))?\b", s)
    out = []
    for hh, mm in tokens:
        h = int(hh)
        m = int(mm) if mm else 0
        if 0 <= h <= 47 and 0 <= m <= 59:
            out.append((h % 24, m))
    return out


def compute_turno_eur(durata_min: int, apt: str, cfg: CalcConfig) -> float:
    """
    Calcola il costo del turno secondo Alpitour 2025.
    Usa tariffe fisse per durate intere (3h, 4h, 5h, 6h, 7h, 8h) o calcola pro-rata.
    """
    durata_h = durata_min / 60.0
    rates = cfg.get_turno_rates(apt)
    
    # Se la durata è esattamente una delle tariffe fisse, usa quella
    durata_h_int = int(round(durata_h))
    if durata_h_int in rates and abs(durata_h - durata_h_int) < 0.01:
        return rates[durata_h_int]
    
    # Altrimenti calcola pro-rata: base 3h + ore oltre 3h
    base_3h = rates[3]
    if durata_h <= 3.0:
        return base_3h
    else:
        ore_oltre_3h = durata_h - 3.0
        return base_3h + ore_oltre_3h * cfg.over_3h_rate_per_h


def compute_extra_min(atd_sel: Optional[pd.Timestamp], end_dt: pd.Timestamp, no_dec: bool, cfg: CalcConfig) -> int:
    """
    Calcola i minuti extra secondo Alpitour 2025.
    
    Regola: I 30 minuti post-ATD vanno sempre considerati.
    - Se ATD è DOPO fine turno: extra = (ATD + 30 min) - fine turno
    - Se ATD è PRIMA fine turno: dei 30 minuti post-ATD, solo la parte FUORI dal turno conta come extra
      Esempio: ATD 10:24, fine turno 10:25, 30 min post-ATD = 10:24-10:54
      → 1 min dentro turno (10:24-10:25), 29 min extra (10:25-10:54)
    """
    if no_dec or atd_sel is None:
        return 0
    
    # Alpitour: fine copertura = ATD + 30 minuti
    fine_copertura = atd_sel + pd.Timedelta(minutes=cfg.extra_window_minutes)
    
    # Se ATD è DOPO fine turno: calcolo normale
    if atd_sel > end_dt:
        return int((fine_copertura - end_dt).total_seconds() // 60)
    
    # Se ATD è PRIMA o UGUALE a fine turno: dei 30 minuti post-ATD, solo la parte FUORI conta
    # I 30 minuti vanno da ATD a (ATD + 30 min)
    # Solo la parte dopo fine_turno conta come extra
    if fine_copertura <= end_dt:
        # Tutti i 30 minuti sono dentro il turno
        return 0
    
    # Parte dei 30 minuti è fuori: calcola solo quella parte
    return int((fine_copertura - end_dt).total_seconds() // 60)


def compute_night_eur(night_min: int, cfg: CalcConfig, apt: str = None) -> float:
    """
    Calcola il costo notturno secondo Alpitour 2025.
    BGY: maggiorazione 15% = €3,75/h = €0,0625/minuto (base 75€/3h = 25€/h)
    VRN: maggiorazione 15% = €4,00/h = €0,0667/minuto (base 80€/3h = 26,67€/h)
    La maggiorazione 15% è calcolata come differenza tra tariffa oraria con +15% e tariffa oraria base.
    Per VRN: 80€/3h = 26,67€/h → con +15% = 30,67€/h → differenza = 4,00€/h
    """
    if apt and apt.upper() == "VRN":
        # VRN: tariffa proporzionale alla base VRN
        # Base VRN: 80€ per 3h = 26,67€/ora
        # Maggiorazione 15%: 26,67€/ora × 1.15 = 30,67€/ora
        # Differenza notturna: 30,67€/ora - 26,67€/ora = 4,00€/ora
        vrn_base_h = 80.0 / 3.0  # 26,6667€/h
        vrn_night_h = vrn_base_h * 0.15  # 4,00€/h (differenza notturna)
        vrn_night_per_min = vrn_night_h / 60.0  # 0,0667€/min
        base_eur = night_min * vrn_night_per_min
        # Nessun minimo: calcolo proporzionale puro
        return base_eur
    else:
        # BGY: tariffa standard
        base_eur = night_min * cfg.night_eur_per_min
        return base_eur


def get_italian_holidays_2025() -> set[date]:
    """
    Calcola i festivi italiani per il 2025 secondo le linee guida Alpitour:
    - 1 Gennaio (Capodanno)
    - 6 Gennaio (Epifania)
    - Pasqua e Pasquetta
    - 25 Aprile (Liberazione)
    - 1 Maggio (Festa del Lavoro)
    - 2 Giugno (Festa della Repubblica)
    - 1 Novembre (Ognissanti)
    - 15 Agosto (Ferragosto)
    - 8 Dicembre (Immacolata)
    - 25 Dicembre (Natale)
    - 26 Dicembre (Santo Stefano)
    """
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
    
    # Pasqua e Pasquetta 2025 (calcolate dinamicamente)
    from datetime import timedelta
    easter_2025 = easter(2025)
    holidays.add(easter_2025)              # Pasqua
    holidays.add(easter_2025 + timedelta(days=1))  # Pasquetta
    
    return holidays


def load_holiday_list(path: str) -> set[date]:
    """
    Accepts a text/csv with one date per line: YYYY-MM-DD or DD/MM/YYYY
    """
    out: set[date] = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            # try both formats
            dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
            if pd.isna(dt):
                continue
            out.add(dt.date())
    return out


def validate_file_complete(file_path: str, to_keyword: str = "alpitour", apt_filter: Optional[List[str]] = None) -> Dict:
    """
    Valida completamente il file Excel prima dell'elaborazione.
    Restituisce un dizionario con:
    - colonne_trovate: dict con colonne rilevate
    - colonne_mancanti: lista colonne mancanti
    - righe_totali: numero totale righe
    - righe_con_errori: lista di errori per riga
    - tour_operators_trovati: set di tour operatour rilevati
    - aeroporti_trovati: set di aeroporti rilevati
    - date_trovate: set di date trovate
    - errori_riepilogo: riepilogo errori
    """
    result = {
        "colonne_trovate": {},
        "colonne_mancanti": [],
        "righe_totali": 0,
        "righe_con_errori": [],
        "tour_operators_trovati": set(),
        "aeroporti_trovati": set(),
        "date_trovate": set(),
        "errori_riepilogo": {},
        "fogli_validati": []
    }
    
    # Colonne attese
    colonne_attese = {
        "data": ["DATA", "DATE"],
        "tour_operator": ["TOUR OPERATOR", "TO", "OPERATORE"],
        "apt": ["APT", "AEROPORTO", "SCALO"],
        "turno": ["TURNO", "TURNO ASSISTENTE", "TURNI"],
        "atd": ["ATD", "ORARIO ATD"],
        "std": ["STD", "ORARIO STD"],
        "assistente": ["ASSISTENTE"]
    }
    
    try:
        for sheet_name, sdf0 in iter_excel_sheets(file_path):
            if sdf0 is None or sdf0.empty:
                continue
            
            sdf = normalize_cols(sdf0)
            cols = detect_columns(sdf)
            
            # Raccoglie colonne trovate
            for key, patterns in colonne_attese.items():
                if cols[key]:
                    result["colonne_trovate"][key] = cols[key]
                else:
                    if key not in result["colonne_mancanti"]:
                        result["colonne_mancanti"].append(key)
            
            # Colonne minime richieste
            if not cols["data"] or not cols["apt"] or not cols["turno"]:
                result["errori_riepilogo"][sheet_name] = "Colonne minime mancanti (DATA, APT, TURNO)"
                continue
            
            result["righe_totali"] += len(sdf)
            
            # Rileva tour operatour
            if cols["tour_operator"]:
                unique_to = sdf[cols["tour_operator"]].dropna().astype(str).str.strip()
                unique_to = unique_to[unique_to != ""]
                unique_to = unique_to[unique_to.str.lower() != "nan"]
                result["tour_operators_trovati"].update(unique_to.unique())
            
            # Rileva aeroporti
            if cols["apt"]:
                unique_apt = sdf[cols["apt"]].dropna().astype(str).str.strip()
                unique_apt = unique_apt[unique_apt != ""]
                unique_apt = unique_apt[unique_apt.str.lower() != "nan"]
                result["aeroporti_trovati"].update(unique_apt.unique())
            
            # Filtra per TO se presente
            if cols["tour_operator"]:
                mask_to = sdf[cols["tour_operator"]].astype(str).str.contains(to_keyword, case=False, na=False)
                sdf_filtered = sdf[mask_to].copy()
            else:
                sdf_filtered = sdf.copy()
            
            # Crea una config temporanea per la validazione
            from dataclasses import dataclass
            @dataclass
            class TempConfig:
                to_keyword: str = to_keyword
                apt_filter: Optional[List[str]] = apt_filter
            
            temp_cfg = TempConfig(to_keyword=to_keyword, apt_filter=apt_filter)
            
            # Valida ogni riga
            errori_foglio = []
            for idx, row in sdf_filtered.iterrows():
                errore = validate_row_data(row, cols, temp_cfg)
                if errore:
                    # Parse date per vedere se è valida
                    data_val = None
                    if cols["data"]:
                        data_val = row.get(cols["data"])
                        parsed_date = parse_excel_date(data_val) if pd.notna(data_val) else None
                        if parsed_date:
                            result["date_trovate"].add(parsed_date.date())
                    
                    errori_foglio.append({
                        "foglio": sheet_name,
                        "riga": int(idx) + 2,  # +2 perché Excel inizia da 1 e c'è l'header
                        "data": str(data_val) if data_val is not None else "N/A",
                        "apt": str(row.get(cols["apt"], "")) if cols["apt"] else "N/A",
                        "errore": errore
                    })
            
            if errori_foglio:
                result["righe_con_errori"].extend(errori_foglio)
            
            result["fogli_validati"].append({
                "foglio": sheet_name,
                "righe_totali": len(sdf),
                "righe_filtrate": len(sdf_filtered),
                "righe_con_errori": len(errori_foglio)
            })
    
    except Exception as e:
        result["errori_riepilogo"]["ERRORE_GENERALE"] = str(e)
    
    # Converti set in list per JSON serialization
    result["tour_operators_trovati"] = sorted(list(result["tour_operators_trovati"]))
    result["aeroporti_trovati"] = sorted(list(result["aeroporti_trovati"]))
    result["date_trovate"] = sorted([d.strftime("%Y-%m-%d") for d in result["date_trovate"]])
    
    return result


def iter_excel_sheets(file_path: str) -> Iterable[Tuple[str, pd.DataFrame]]:
    xls = pd.ExcelFile(file_path)
    for sheet in xls.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet)
        yield sheet, df


def process_files(input_files: List[str], cfg: CalcConfig) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
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

            # Filter TO if present
            if cols["tour_operator"]:
                mask_to = sdf[cols["tour_operator"]].astype(str).str.contains(cfg.to_keyword, case=False, na=False)
                sdf = sdf[mask_to].copy()
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

            # Forward-fill TURNO per DATA within the sheet chunk order (already in original read order)
            turno_col = cols["turno"]
            sdf["__turno_raw"] = sdf[turno_col].astype(str)
            ffill_src = sdf[turno_col].replace("", np.nan)
            sdf["__turno_ffill_raw"] = ffill_src.groupby(sdf["__date"]).ffill()

            # Parse turno
            parsed = sdf["__turno_ffill_raw"].apply(parse_turno)
            sdf["__start_str"] = parsed.apply(lambda x: x[0])
            sdf["__end_str"] = parsed.apply(lambda x: x[1])
            sdf["__no_dec"] = parsed.apply(lambda x: x[2])
            sdf["__turno_norm"] = parsed.apply(lambda x: x[3])

            # Exclude non-interpretable TURNO blocks
            sdf = sdf[sdf["__start_str"].notna() & sdf["__end_str"].notna()].copy()
            if sdf.empty:
                continue

            # Build start/end datetime
            sdf["__start_dt"] = sdf.apply(lambda r: to_dt(r["__date"], r["__start_str"]), axis=1)
            sdf["__end_dt"] = sdf.apply(lambda r: to_dt(r["__date"], r["__end_str"]), axis=1)
            overnight = sdf["__end_dt"] < sdf["__start_dt"]
            sdf.loc[overnight, "__end_dt"] = sdf.loc[overnight, "__end_dt"] + pd.Timedelta(days=1)

            # Festivo by column if present
            if cols["festivo"]:
                sdf["__festivo"] = sdf[cols["festivo"]].apply(is_truthy_festivo)
            else:
                sdf["__festivo"] = False

            # Provided values for discrepancy (first row of each block)
            prov_importo_col = cols["importo"]
            prov_extra_col = cols["ore_extra"]
            prov_night_col = cols["notturno"]
            assistente_col = cols["assistente"]

            # Iterate rows and aggregate by block
            for idx, r in sdf.iterrows():
                # Validazione dati riga
                errore_riga = validate_row_data(r, cols, cfg)
                
                d = r["__date"]
                apt = str(r[cols["apt"]]).strip() if cols["apt"] else ""
                turno_norm = str(r["__turno_norm"]).strip() if pd.notna(r.get("__turno_norm")) else ""
                turno_ffill_raw = str(r["__turno_ffill_raw"]).strip() if pd.notna(r.get("__turno_ffill_raw")) else ""
                assistente_val = str(r[assistente_col]).strip() if assistente_col and assistente_col in r.index and pd.notna(r[assistente_col]) else ""

                # Se turno_norm è vuoto, usa un placeholder per la chiave
                if not turno_norm:
                    turno_norm = f"ERRORE_{idx}"

                key = (d, apt, turno_norm)

                # Extract ATD candidates from row
                atd_times: List[Tuple[int, int]] = []
                if cols["atd"]:
                    atd_times.extend(extract_atd_candidates(r[cols["atd"]]))

                # Extract STD candidates from row (Alpitour: fallback se ATD non disponibile)
                std_times: List[Tuple[int, int]] = []
                if cols["std"]:
                    std_times.extend(extract_atd_candidates(r[cols["std"]]))

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

                # Determine first-source reference (first appearance of the block)
                src = SourceRowRef(file=file_path, sheet=sheet_name, row_index=int(r["__sheet_row_order"]), original_order=int(r["__global_order"]))

                if key not in blocks:
                    # Save "provided" values from this first row (for discrepancy sheet)
                    prov_importo = parse_eur(r[prov_importo_col]) if prov_importo_col else None
                    prov_extra_min = parse_minutes_from_cell(r[prov_extra_col]) if prov_extra_col else None
                    prov_night_min = parse_minutes_from_cell(r[prov_night_col]) if prov_night_col else None

                    blocks[key] = BlockAgg(
                        date=d,
                        apt=apt,
                        turno_raw_ffill=turno_ffill_raw,
                        turno_norm=turno_norm,
                        start_dt=r["__start_dt"],
                        end_dt=r["__end_dt"],
                        no_dec=bool(r["__no_dec"]),
                        atd_list=atd_dt_list.copy(),
                        std_list=std_dt_list.copy(),
                        festivo_flag=bool(r["__festivo"]),
                        first_source=src,
                        assistente=assistente_val if assistente_val else None,
                        provided_importo=prov_importo,
                        provided_extra_min=prov_extra_min,
                        provided_night_min=prov_night_min,
                        errore=errore_riga,
                    )
                else:
                    # merge
                    b = blocks[key]
                    b.atd_list.extend(atd_dt_list)
                    b.std_list.extend(std_dt_list)
                    # If any row in block says festivo -> festivo
                    b.festivo_flag = b.festivo_flag or bool(r["__festivo"])
                    # Keep earliest source by global order
                    if src.original_order < b.first_source.original_order:
                        b.first_source = src
                        # update provided values to align with "first row of block"
                        b.provided_importo = parse_eur(r[prov_importo_col]) if prov_importo_col else b.provided_importo
                        b.provided_extra_min = parse_minutes_from_cell(r[prov_extra_col]) if prov_extra_col else b.provided_extra_min
                        b.provided_night_min = parse_minutes_from_cell(r[prov_night_col]) if prov_night_col else b.provided_night_min

    # Apply holiday dates: first try external list, otherwise use Italian holidays 2025
    holiday_dates_to_use = cfg.holiday_dates
    if holiday_dates_to_use is None:
        # Usa automaticamente i festivi italiani 2025
        holiday_dates_to_use = get_italian_holidays_2025()
    
    # Apply holiday flags
    for b in blocks.values():
        if b.date.date() in holiday_dates_to_use:
            b.festivo_flag = True

    # Compute results per block
    rows_detail = []
    rows_discr = []

    for key, b in sorted(blocks.items(), key=lambda kv: (kv[1].date, kv[1].apt, kv[1].first_source.original_order)):
        # Se c'è un errore, metti tutti i valori a zero
        if b.errore:
            rows_detail.append({
                "DATA": b.date.strftime("%d/%m/%Y"),
                "APT": b.apt,
                "ASSISTENTE": b.assistente if b.assistente else "",
                "TURNO_FFILL": b.turno_raw_ffill,
                "TURNO_NORMALIZZATO": b.turno_norm,
                "INIZIO_DT": b.start_dt if pd.notna(b.start_dt) else None,
                "FINE_DT": b.end_dt if pd.notna(b.end_dt) else None,
                "DURATA_TURNO_MIN": 0,
                "NO_DEC": b.no_dec,
                "ATD_SCELTO": None,
                "TURNO_EUR": 0.0,
                "EXTRA_MIN_RAW": 0,
                "EXTRA_MIN": 0,
                "EXTRA_H:MM": "0:00",
                "EXTRA_EUR": 0.0,
                "NOTTE_MIN_RAW": 0,
                "NOTTE_MIN": 0,
                "NOTTE_EUR": 0.0,
                "FESTIVO": b.festivo_flag,
                "TOTALE_BLOCCO_EUR": 0.0,
                "ERRORE": b.errore,
                "SRC_FILE": b.first_source.file,
                "SRC_SHEET": b.first_source.sheet,
                "SRC_ROW0": b.first_source.row_index,
            })
            continue
        
        durata_min = int((b.end_dt - b.start_dt).total_seconds() // 60)

        # Turno €
        turno_eur = compute_turno_eur(durata_min, b.apt, cfg)

        # Alpitour: selezione decollo di riferimento (ultimo ATD disponibile, altrimenti STD)
        # Cerca ATD disponibile (può essere prima o dopo fine turno per la nuova regola)
        # Preferisci ATD dopo fine turno, altrimenti prendi l'ultimo ATD disponibile
        atd_after = [x for x in b.atd_list if x > b.end_dt]
        if atd_after:
            atd_sel = max(atd_after)
        else:
            # Se non ci sono ATD dopo fine turno, prendi l'ultimo ATD disponibile (anche se prima)
            atd_sel = max(b.atd_list) if b.atd_list else None
        
        # Se ATD non disponibile, usa STD come fallback
        if atd_sel is None:
            std_after = [x for x in b.std_list if x > b.end_dt]
            if std_after:
                atd_sel = max(std_after)
            else:
                atd_sel = max(b.std_list) if b.std_list else None

        # Extra minutes (NO arrotondamento)
        extra_min_raw = compute_extra_min(atd_sel, b.end_dt, b.no_dec, cfg)
        extra_min = extra_min_raw  # Nessun arrotondamento

        extra_eur = (extra_min / 60.0) * cfg.rate_extra_per_h

        # Night minutes: on turno + (optional) extra interval
        night_turno = night_minutes(b.start_dt, b.end_dt)

        night_extra = 0
        if extra_min_raw > 0 and (not b.no_dec) and extra_min > 0:
            extra_end = b.end_dt + pd.Timedelta(minutes=extra_min)
            night_extra = night_minutes(b.end_dt, extra_end)

        night_min_raw = night_turno + night_extra
        night_min = night_min_raw  # Nessun arrotondamento
        night_eur = compute_night_eur(night_min, cfg, b.apt)

        # Alpitour 2025: festivi +20% su turno, extra E notturno
        if b.festivo_flag:
            subtotal = (turno_eur + extra_eur + night_eur) * cfg.festivo_multiplier
        else:
            subtotal = turno_eur + extra_eur + night_eur
        totale = subtotal

        # Format H:MM
        def hmm(m: int) -> str:
            return f"{m // 60}:{m % 60:02d}"

        rows_detail.append({
            "DATA": b.date.strftime("%d/%m/%Y"),
            "APT": b.apt,
            "ASSISTENTE": b.assistente if b.assistente else "",
            "TURNO_FFILL": b.turno_raw_ffill,
            "TURNO_NORMALIZZATO": b.turno_norm,
            "INIZIO_DT": b.start_dt,
            "FINE_DT": b.end_dt,
            "DURATA_TURNO_MIN": durata_min,
            "NO_DEC": b.no_dec,
            "ATD_SCELTO": atd_sel,
            "TURNO_EUR": round(turno_eur, 2),
            "EXTRA_MIN_RAW": extra_min_raw,
            "EXTRA_MIN": int(extra_min),
            "EXTRA_H:MM": hmm(int(extra_min)),
            "EXTRA_EUR": round(extra_eur, 2),
            "NOTTE_MIN_RAW": int(night_min_raw),
            "NOTTE_MIN": int(night_min),
            "NOTTE_EUR": round(night_eur, 2),
            "FESTIVO": b.festivo_flag,
            "TOTALE_BLOCCO_EUR": round(totale, 2),
            "ERRORE": "",  # Nessun errore se siamo arrivati qui
            "SRC_FILE": b.first_source.file,
            "SRC_SHEET": b.first_source.sheet,
            "SRC_ROW0": b.first_source.row_index,
        })

        # Discrepancies (only if provided exists)
        prov_imp = b.provided_importo
        prov_ex = b.provided_extra_min
        prov_nt = b.provided_night_min

        # Only include discrepancy row if at least one provided is present
        if (prov_imp is not None) or (prov_ex is not None) or (prov_nt is not None):
            rows_discr.append({
                "DATA": b.date.strftime("%d/%m/%Y"),
                "APT": b.apt,
                "TURNO_NORMALIZZATO": b.turno_norm,
                "EXTRA_MIN_CALC": int(extra_min),
                "EXTRA_MIN_FILE": prov_ex,
                "DELTA_EXTRA_MIN": (int(extra_min) - prov_ex) if prov_ex is not None else None,
                "NOTTE_MIN_CALC": int(night_min),
                "NOTTE_MIN_FILE": prov_nt,
                "DELTA_NOTTE_MIN": (int(night_min) - prov_nt) if prov_nt is not None else None,
                "TOTALE_CALC_EUR": round(totale, 2),
                "TOTALE_FILE_EUR": prov_imp,
                "DELTA_TOTALE_EUR": round((totale - prov_imp), 2) if prov_imp is not None else None,
                "SRC_FILE": b.first_source.file,
                "SRC_SHEET": b.first_source.sheet,
                "SRC_ROW0": b.first_source.row_index,
            })

    detail_df = pd.DataFrame(rows_detail)
    discr_df = pd.DataFrame(rows_discr)

    # Totals by period
    if detail_df.empty:
        totals_df = pd.DataFrame(columns=[
            "PERIODO", "TOT_TURNO_EUR", "TOT_EXTRA_MIN", "TOT_EXTRA_H:MM", "TOT_EXTRA_EUR",
            "TOT_NOTTE_MIN", "TOT_NOTTE_EUR", "TOT_TOTALE_EUR"
        ])
        return detail_df, totals_df, discr_df

    detail_df["__DATE_TS"] = pd.to_datetime(detail_df["DATA"], dayfirst=True)
    detail_df["PERIODO"] = np.where(detail_df["__DATE_TS"].dt.day <= 15, "1–15", "16–31")

    def sum_hmm(minutes: int) -> str:
        minutes = int(minutes)
        return f"{minutes // 60}:{minutes % 60:02d}"

    totals = detail_df.groupby("PERIODO", as_index=False).agg(
        TOT_TURNO_EUR=("TURNO_EUR", "sum"),
        TOT_EXTRA_MIN=("EXTRA_MIN", "sum"),
        TOT_EXTRA_EUR=("EXTRA_EUR", "sum"),
        TOT_NOTTE_MIN=("NOTTE_MIN", "sum"),
        TOT_NOTTE_EUR=("NOTTE_EUR", "sum"),
        TOT_TOTALE_EUR=("TOTALE_BLOCCO_EUR", "sum"),
    )

    totals["TOT_EXTRA_H:MM"] = totals["TOT_EXTRA_MIN"].apply(sum_hmm)
    totals = totals[[
        "PERIODO", "TOT_TURNO_EUR", "TOT_EXTRA_MIN", "TOT_EXTRA_H:MM", "TOT_EXTRA_EUR",
        "TOT_NOTTE_MIN", "TOT_NOTTE_EUR", "TOT_TOTALE_EUR"
    ]]

    month_row = pd.DataFrame([{
        "PERIODO": "MESE",
        "TOT_TURNO_EUR": float(detail_df["TURNO_EUR"].sum()),
        "TOT_EXTRA_MIN": int(detail_df["EXTRA_MIN"].sum()),
        "TOT_EXTRA_H:MM": sum_hmm(int(detail_df["EXTRA_MIN"].sum())),
        "TOT_EXTRA_EUR": float(detail_df["EXTRA_EUR"].sum()),
        "TOT_NOTTE_MIN": int(detail_df["NOTTE_MIN"].sum()),
        "TOT_NOTTE_EUR": float(detail_df["NOTTE_EUR"].sum()),
        "TOT_TOTALE_EUR": float(detail_df["TOTALE_BLOCCO_EUR"].sum()),
    }])

    totals_df = pd.concat([totals, month_row], ignore_index=True)

    # cleanup helper col
    detail_df = detail_df.drop(columns=["__DATE_TS"], errors="ignore")

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
        'Turno': df_apt['TURNO_NORMALIZZATO'],
        'Durata': df_apt['DURATA_H:MM'],
        'Turno (€)': df_apt['TURNO_EUR'].round(2),
        'Extra (h:mm)': df_apt['EXTRA_H:MM'],
        'Extra (€)': df_apt['EXTRA_EUR'].round(2),
        'Notturno (h:mm)': df_apt['NOTTE_H:MM'],
        'Notturno (€)': df_apt['NOTTE_EUR'].round(2),
        'TOTALE (€)': df_apt['TOTALE_BLOCCO_EUR'].round(2),
    }
    
    # Add Assistente column if present (insert after Data)
    if 'ASSISTENTE' in df_apt.columns:
        # Rebuild dict with Assistente in the right position
        new_cols = {'Data': output_cols['Data']}
        new_cols['Assistente'] = df_apt['ASSISTENTE'].fillna('')
        for k, v in output_cols.items():
            if k != 'Data':
                new_cols[k] = v
        output_cols = new_cols
    
    result_df = pd.DataFrame(output_cols)
    
    # Add total row
    total_row_dict = {
        'Data': 'TOTALE',
        'Turno': '',
        'Durata': '',
        'Turno (€)': df_apt['TURNO_EUR'].sum(),
        'Extra (h:mm)': format_minutes_to_hmm(df_apt['EXTRA_MIN'].sum()),
        'Extra (€)': df_apt['EXTRA_EUR'].sum(),
        'Notturno (h:mm)': format_minutes_to_hmm(df_apt['NOTTE_MIN'].sum()),
        'Notturno (€)': df_apt['NOTTE_EUR'].sum(),
        'TOTALE (€)': df_apt['TOTALE_BLOCCO_EUR'].sum(),
    }
    
    # Add empty Assistente in total row if column exists (insert after Data)
    if 'ASSISTENTE' in df_apt.columns:
        new_total_dict = {'Data': total_row_dict['Data']}
        new_total_dict['Assistente'] = ''
        for k, v in total_row_dict.items():
            if k != 'Data':
                new_total_dict[k] = v
        total_row_dict = new_total_dict
    
    total_row = pd.DataFrame([total_row_dict])
    
    result_df = pd.concat([result_df, total_row], ignore_index=True)
    return result_df


def create_total_by_apt_sheet(detail_df: pd.DataFrame) -> pd.DataFrame:
    """Create total sheet grouped by airport"""
    if detail_df.empty:
        return pd.DataFrame(columns=['Aeroporto', 'Blocchi', 'Assistenze', 'Extra', 'Notturno', 'TOTALE'])
    
    # Group by airport
    totals_by_apt = detail_df.groupby('APT').agg({
        'TURNO_EUR': 'sum',
        'EXTRA_EUR': 'sum',
        'EXTRA_MIN': 'sum',
        'NOTTE_EUR': 'sum',
        'NOTTE_MIN': 'sum',
        'TOTALE_BLOCCO_EUR': 'sum'
    }).round(2)
    
    block_counts = detail_df.groupby('APT').size()
    
    # Format function
    def format_eur(value):
        if value >= 1000:
            return f"{value:,.2f}€"
        else:
            return f"{value:.2f}€"
    
    def min_to_hours_decimal(minutes):
        if pd.isna(minutes) or minutes == 0:
            return 0.0
        return round(minutes / 60.0, 2)
    
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
    
    result = pd.DataFrame({
        'Aeroporto': totals_by_apt.index,
        'Blocchi': block_counts.values,
        'Assistenze': totals_by_apt['TURNO_EUR'].values,
        'Extra_min': totals_by_apt['EXTRA_MIN'].values,
        'Extra_eur': totals_by_apt['EXTRA_EUR'].values,
        'Notturno_min': totals_by_apt['NOTTE_MIN'].values,
        'Notturno_eur': totals_by_apt['NOTTE_EUR'].values,
        'TOTALE': totals_by_apt['TOTALE_BLOCCO_EUR'].values,
    })
    
    result['Extra_ore'] = result['Extra_min'].apply(min_to_hours_decimal)
    result['Notturno_ore'] = result['Notturno_min'].apply(min_to_hours_decimal)
    
    # Format columns
    output_df = pd.DataFrame({
        'Aeroporto': result['Aeroporto'],
        'Blocchi': result['Blocchi'],
        'Assistenze': result['Assistenze'].apply(format_eur),
        'Extra': result.apply(lambda x: f"{format_eur(x['Extra_eur'])} ({min_to_hours_minutes_text(x['Extra_min'])})", axis=1),
        'Notturno': result.apply(lambda x: f"{format_eur(x['Notturno_eur'])} ({min_to_hours_minutes_text(x['Notturno_min'])})", axis=1),
        'TOTALE': result['TOTALE'].apply(format_eur),
    })
    
    # Order by airport (VRN, BGY, NAP, VCE)
    order = ['VRN', 'BGY', 'NAP', 'VCE']
    output_df['sort_order'] = output_df['Aeroporto'].apply(lambda x: order.index(x) if x in order else 999)
    output_df = output_df.sort_values('sort_order').drop('sort_order', axis=1)
    
    # Add total row
    total_row = pd.DataFrame([{
        'Aeroporto': 'TOTALE',
        'Blocchi': output_df['Blocchi'].sum(),
        'Assistenze': format_eur(result['Assistenze'].sum()),
        'Extra': f"{format_eur(result['Extra_eur'].sum())} ({min_to_hours_minutes_text(result['Extra_min'].sum())})",
        'Notturno': f"{format_eur(result['Notturno_eur'].sum())} ({min_to_hours_minutes_text(result['Notturno_min'].sum())})",
        'TOTALE': format_eur(result['TOTALE'].sum()),
    }])
    
    output_df = pd.concat([output_df, total_row], ignore_index=True)
    return output_df


# -----------------------------
# Assistenti VRN sheet
# -----------------------------

def create_assistenti_vrn_sheet(detail_df: pd.DataFrame) -> pd.DataFrame:
    """Crea foglio con calcoli per assistenti VRN secondo accordo assistenti (stesso di Veratour)"""
    if detail_df.empty:
        return pd.DataFrame()
    
    # Filtra solo VRN
    df_vrn = detail_df[detail_df['APT'] == 'VRN'].copy()
    
    if df_vrn.empty or 'ASSISTENTE' not in df_vrn.columns:
        return pd.DataFrame()
    
    # Rimuovi righe senza assistente
    df_vrn = df_vrn[df_vrn['ASSISTENTE'].notna() & (df_vrn['ASSISTENTE'] != '')].copy()
    
    if df_vrn.empty:
        return pd.DataFrame()
    
    # Tariffe assistenti (dal documento Accordo_Assistenti_VRN 26_Completo - stesso di Veratour)
    BASE_ASSISTENTE = 58.0  # € per 3h
    EXTRA_ASSISTENTE_PER_H = 12.0  # €/h
    MAGG_NOTTURNA_PERC = 0.15  # +15% proporzionale
    MAGG_FESTIVO_PERC = 0.20  # +20% su tutto
    
    # Festivi (dal documento)
    from datetime import date
    festivi_2025 = {
        date(2025, 12, 25),  # Natale
        date(2025, 12, 26),  # Santo Stefano
        date(2025, 1, 1),    # Capodanno
        date(2025, 1, 6),    # Epifania
        date(2025, 4, 25),   # Liberazione
        date(2025, 5, 1),    # Festa del Lavoro
        date(2025, 6, 2),    # Festa della Repubblica
        date(2025, 8, 15),   # Ferragosto
        date(2025, 11, 1),   # Ognissanti
        date(2025, 12, 8),   # Immacolata
    }
    # Aggiungi Pasqua e Pasquetta 2025
    easter_2025 = easter(2025)
    festivi_2025.add(easter_2025)
    festivi_2025.add(easter_2025 + pd.Timedelta(days=1))
    
    def calcola_turno_assistente(durata_min):
        """Calcola turno assistente: 58€ base + 12€/h oltre 3h"""
        durata_h = durata_min / 60.0
        if durata_h <= 3:
            return BASE_ASSISTENTE
        else:
            return BASE_ASSISTENTE + (durata_h - 3) * EXTRA_ASSISTENTE_PER_H
    
    def calcola_extra_assistente(extra_min):
        """Calcola extra assistente: 12€/h"""
        if extra_min <= 0:
            return 0.0
        return (extra_min / 60.0) * EXTRA_ASSISTENTE_PER_H
    
    def calcola_notturno_assistente(base, minuti_notturni):
        """Calcola notturno proporzionale: (base/3h) * (ore_notturne) * 15%"""
        if minuti_notturni <= 0:
            return 0.0
        valore_orario = base / 3.0  # €/h
        ore_notturne = minuti_notturni / 60.0
        valore_parte_notturna = valore_orario * ore_notturne
        maggiorazione = valore_parte_notturna * MAGG_NOTTURNA_PERC
        return maggiorazione
    
    def is_festivo(data_str):
        """Verifica se la data è festiva"""
        try:
            dt = pd.to_datetime(data_str, dayfirst=True)
            return dt.date() in festivi_2025
        except:
            return False
    
    # Calcola per ogni riga
    rows_assistenti = []
    for _, row in df_vrn.iterrows():
        assistente = row['ASSISTENTE']
        durata_min = int(row['DURATA_TURNO_MIN'])
        extra_min = int(row.get('EXTRA_MIN', 0))
        minuti_notturni = int(row.get('NOTTE_MIN_RAW', row.get('NOTTE_MIN', 0)))  # Usa RAW se disponibile
        data_str = row['DATA']
        
        # Calcoli assistente
        base = calcola_turno_assistente(durata_min)
        extra = calcola_extra_assistente(extra_min)
        notturno = calcola_notturno_assistente(base, minuti_notturni)
        
        # Festivo: +20% su (base + extra + notturno)
        festivo = is_festivo(data_str)
        subtotale = base + extra + notturno
        totale = subtotale * (1 + MAGG_FESTIVO_PERC) if festivo else subtotale
        
        rows_assistenti.append({
            'ASSISTENTE': assistente,
            'BASE_EUR': base,
            'EXTRA_EUR': extra,
            'EXTRA_MIN': extra_min,
            'NOTTE_MIN': minuti_notturni,
            'NOTTE_EUR': notturno,
            'TOTALE_EUR': totale,
        })
    
    df_calc = pd.DataFrame(rows_assistenti)
    
    # Raggruppa per assistente
    assistenti_totals = df_calc.groupby('ASSISTENTE').agg({
        'BASE_EUR': 'sum',
        'EXTRA_EUR': 'sum',
        'EXTRA_MIN': 'sum',
        'NOTTE_EUR': 'sum',
        'NOTTE_MIN': 'sum',
        'TOTALE_EUR': 'sum',
        'ASSISTENTE': 'count'  # Numero di blocchi
    }).round(2)
    
    assistenti_totals.columns = ['Turno (€)', 'Extra (€)', 'Extra (min)', 'Notturno (€)', 'Notturno (min)', 'TOTALE (€)', 'Blocchi']
    assistenti_totals = assistenti_totals.reset_index()
    assistenti_totals.columns = ['Assistente', 'Turno (€)', 'Extra (€)', 'Extra (min)', 'Notturno (€)', 'Notturno (min)', 'TOTALE (€)', 'Blocchi']
    
    # Formatta Extra e Notturno in ore:minuti
    def format_hmm(minutes):
        if pd.isna(minutes) or minutes == 0:
            return "0:00"
        h = int(minutes // 60)
        m = int(minutes % 60)
        return f"{h}:{m:02d}"
    
    assistenti_totals['Extra (h:mm)'] = assistenti_totals['Extra (min)'].apply(format_hmm)
    assistenti_totals['Notturno (h:mm)'] = assistenti_totals['Notturno (min)'].apply(format_hmm)
    
    # Riordina colonne
    result = assistenti_totals[[
        'Assistente', 'Blocchi', 'Turno (€)', 'Extra (h:mm)', 'Extra (€)', 
        'Notturno (h:mm)', 'Notturno (€)', 'TOTALE (€)'
    ]].copy()
    
    # Ordina per totale decrescente
    result = result.sort_values('TOTALE (€)', ascending=False)
    
    # Aggiungi riga totale
    total_row = pd.DataFrame([{
        'Assistente': 'TOTALE',
        'Blocchi': result['Blocchi'].sum(),
        'Turno (€)': result['Turno (€)'].sum(),
        'Extra (h:mm)': format_hmm(assistenti_totals['Extra (min)'].sum()),
        'Extra (€)': result['Extra (€)'].sum(),
        'Notturno (h:mm)': format_hmm(assistenti_totals['Notturno (min)'].sum()),
        'Notturno (€)': result['Notturno (€)'].sum(),
        'TOTALE (€)': result['TOTALE (€)'].sum(),
    }])
    
    result = pd.concat([result, total_row], ignore_index=True)
    return result


# -----------------------------
# Output writer
# -----------------------------

def write_output_excel(output_path: str, detail_df: pd.DataFrame, totals_df: pd.DataFrame, discr_df: pd.DataFrame) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl", datetime_format="YYYY-MM-DD HH:MM") as writer:
        # Order columns for readability
        if not detail_df.empty:
            cols = [
                "DATA", "APT", "ASSISTENTE", "TURNO_FFILL", "TURNO_NORMALIZZATO",
                "INIZIO_DT", "FINE_DT", "DURATA_TURNO_MIN", "NO_DEC",
                "ATD_SCELTO",
                "TURNO_EUR",
                "EXTRA_MIN_RAW", "EXTRA_MIN", "EXTRA_H:MM", "EXTRA_EUR",
                "NOTTE_MIN_RAW", "NOTTE_MIN", "NOTTE_EUR",
                "FESTIVO", "TOTALE_BLOCCO_EUR",
                "ERRORE",  # Colonna per segnalare errori di validazione
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
            pd.DataFrame().to_excel(writer, sheet_name="Discrepanze", index=False)
        
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
        
        # Create Assistenti VRN sheet
        if not detail_df.empty:
            assistenti_sheet = create_assistenti_vrn_sheet(detail_df)
            if not assistenti_sheet.empty:
                assistenti_sheet.to_excel(writer, sheet_name="Assistenti_VRN", index=False)

        # Basic column widths
        for sheet in writer.book.worksheets:
            for col_cells in sheet.columns:
                # openpyxl cell objects
                col_letter = col_cells[0].column_letter
                max_len = 0
                for cell in col_cells[:500]:  # limit scan
                    v = cell.value
                    if v is None:
                        continue
                    max_len = max(max_len, len(str(v)))
                sheet.column_dimensions[col_letter].width = min(max(10, max_len + 2), 55)


# -----------------------------
# CLI
# -----------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Calcolatore Alpitour 2025 (blocchi, extra, notturno, festivi).")
    p.add_argument("-i", "--input", nargs="+", required=False, default=["PianoLavoroOTTOBRE 25 .xlsx"], 
                   help="File Excel in input (default: PianoLavoroOTTOBRE 25 .xlsx).")
    p.add_argument("-o", "--output", required=True, help="File Excel in output (xlsx).")
    p.add_argument("--apt", nargs="*", default=None, help="Filtro APT (es. VRN BGY VCE). Se omesso: tutti.")
    p.add_argument("--holiday-list", default=None, help="File con lista festivi (una data per riga).")

    # Alpitour usa sempre maggiorazione 15% = €0,0625/min, non serve night-mode

    # Rounding options
    p.add_argument("--round-extra", choices=["NONE", "FLOOR", "CEIL", "NEAREST"], default="NONE")
    p.add_argument("--round-extra-step", type=int, default=5)
    p.add_argument("--round-night", choices=["NONE", "FLOOR", "CEIL", "NEAREST"], default="NONE")
    p.add_argument("--round-night-step", type=int, default=5)

    return p.parse_args()


def main() -> None:
    args = parse_args()

    holiday_dates = load_holiday_list(args.holiday_list) if args.holiday_list else None

    cfg = CalcConfig(
        apt_filter=args.apt if args.apt else None,
        rounding_extra=RoundingPolicy(args.round_extra, args.round_extra_step),
        rounding_night=RoundingPolicy(args.round_night, args.round_night_step),
        holiday_dates=holiday_dates,
    )

    detail_df, totals_df, discr_df = process_files(args.input, cfg)
    write_output_excel(args.output, detail_df, totals_df, discr_df)

    print(f"OK ✅ Output creato: {args.output}")
    print(f"Blocchi calcolati: {len(detail_df)}")
    if not discr_df.empty:
        print(f"Discrepanze rilevate: {len(discr_df)} (vedi foglio 'Discrepanze')")


if __name__ == "__main__":
    main()
