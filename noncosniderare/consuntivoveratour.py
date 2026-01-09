#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Veratour 2025 — Calcolatore blocchi (Scay/Veratour rules)

Cosa fa:
- Legge 1+ file Excel (anche con più fogli)
- Filtra TO=Veratour e APT richiesto (opzionale)
- Forward-fill TURNO per DATA rispettando l'ordine: file -> foglio -> righe
- Blocco = (DATA, APT, TURNO_ffill_normalizzato)
- Dedup blocchi anche cross-fogli/cross-file unendo gli ATD
- Parse TURNO robusto (08–11, 8:00-11, 8.00–11.30, ecc.; -, –, —)
- Gestisce mezzanotte (fine < inizio => +1 giorno)
- Regola ATD => EXTRA: prende ATD massimo strettamente > fine_turno (ATD < inizio => +1 giorno)
- "NO DEC" nel TURNO => extra = 0 (ma notturno dentro turno resta)
- Turno € = 75 + max(0, durata_h - 3) * 15 (pro-rata al minuto)
- Extra € = extra_min/60 * 18
- Notturno (23:00–05:00) su turno + extra:
    - default: night_eur = night_min * 0.083333 (maggiorazione differenziale €5/h = €25/h × 20%)
    - opzionale: night_mode=FULL30 => night_eur = night_min * 0.5 (tariffa piena €30/h)
- Festivi: se colonna festivo (1/true/si) oppure lista date => (turno+extra+night)*1.20
- Output Excel: DettaglioBlocchi, TotaliPeriodo, Discrepanze

Requisiti:
  pip install pandas openpyxl python-dateutil

Esempi:
  python veratour_calc.py -i "Riepilogo Veratour ottobre 25.xlsx" -o "OUT_VRN.xlsx" --apt VRN
  python veratour_calc.py -i file1.xlsx file2.xlsx --apt VRN --round-extra CEIL --round-extra-step 5 --round-night CEIL --round-night-step 5
  python veratour_calc.py -i *.xlsx --holiday-list festivi.txt
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
    to_keyword: str = "veratour"
    rate_extra_per_h: float = 18.0
    base_3h_eur: float = 75.0
    over_3h_rate_per_h: float = 15.0
    night_mode: str = "DIFF5"  # DIFF5 -> 0.083333/min (5€/h = 25€/h × 20%); FULL30 -> 0.5/min
    night_diff_eur_per_min: float = 0.083333  # 5€/ora = 25€/ora × 20% = 0.083333€/min
    night_full_eur_per_min: float = 0.5
    rounding_extra: RoundingPolicy = RoundingPolicy("NONE", 5)
    rounding_night: RoundingPolicy = RoundingPolicy("NONE", 5)
    festivo_multiplier: float = 1.20
    holiday_dates: Optional[set[date]] = None  # optional external list


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
    
    # Gestione punti: possono essere separatori tra orari o dentro gli orari
    # Pattern tipo "13:30.17:00" dove il punto separa due orari
    # Convertiamo "HH:MM.HH:MM" in "HH:MM-HH:MM"
    s2 = re.sub(r'(\d{1,2}:\d{1,2})\.(\d{1,2}:\d{1,2})', r'\1-\2', s2)
    # Poi convertiamo i punti rimasti in due punti (per gli orari tipo "8.30" -> "8:30")
    s2 = s2.replace(".", ":")

    # Keep original prefixes (A/B/C etc.) for grouping, BUT normalize time range inside
    m = TIME_RANGE_RE.search(s2)
    if not m:
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
    Minutes overlapping [23:00, 05:00) across relevant nights,
    including previous night window as needed.
    """
    if interval_end <= interval_start:
        return 0

    total = 0
    base = interval_start.normalize() - pd.Timedelta(days=1)
    for k in range(0, 3):  # prev, same, next
        day = base + pd.Timedelta(days=k)
        n_start = day + pd.Timedelta(hours=23)
        n_end = day + pd.Timedelta(days=1, hours=5)
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
    df.columns = [normalize_spaces(str(c)).lower() for c in df.columns]
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
      data, tour_operator, apt, turno, atd, importo, ore_extra, notturno, festivo
    """
    return {
        "data": find_col(df, [r"^data$", r"\bdate\b"]),
        "tour_operator": find_col(df, [r"tour\s*operator", r"^to$", r"\boperatore\b"]),
        "apt": find_col(df, [r"^apt$", r"\baeroporto\b", r"\bscalo\b"]),
        "turno": find_col(df, [r"^turno$", r"\bturni\b"]),
        "atd": find_col(df, [r"^atd$", r"\borario\s*atd\b"]),
        "importo": find_col(df, [r"^importo$", r"\btotale\b", r"\bimporto\b"]),
        "ore_extra": find_col(df, [r"\bore\s*extra\b", r"^extra$", r"\bextra\s*(min|ore)\b"]),
        "notturno": find_col(df, [r"^notturno$", r"\bnight\b"]),
        "festivo": find_col(df, [r"^festivo$", r"\bholiday\b"]),
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
    festivo_flag: bool
    first_source: SourceRowRef
    # optional "provided" values from the first row (for discrepancy sheet)
    provided_importo: Optional[float] = None
    provided_extra_min: Optional[int] = None
    provided_night_min: Optional[int] = None


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


def compute_turno_eur(durata_min: int, cfg: CalcConfig) -> float:
    durata_h = durata_min / 60.0
    return cfg.base_3h_eur + max(0.0, durata_h - 3.0) * cfg.over_3h_rate_per_h


def compute_extra_min(atd_sel: Optional[pd.Timestamp], end_dt: pd.Timestamp, no_dec: bool) -> int:
    if no_dec or atd_sel is None:
        return 0
    if atd_sel <= end_dt:
        return 0
    return int((atd_sel - end_dt).total_seconds() // 60)


def compute_night_eur(night_min: int, cfg: CalcConfig) -> float:
    if cfg.night_mode.upper() == "FULL30":
        return night_min * cfg.night_full_eur_per_min
    # default differential 5€/h = 25€/h × 20% = 0.083333€/min
    return night_min * cfg.night_diff_eur_per_min


def get_italian_holidays_2025() -> set[date]:
    """
    Calcola i festivi italiani per il 2025 secondo la proposta Veratour:
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

            # Iterate rows and aggregate by block
            for idx, r in sdf.iterrows():
                d = r["__date"]
                apt = str(r[cols["apt"]]).strip()
                turno_norm = str(r["__turno_norm"]).strip()
                turno_ffill_raw = str(r["__turno_ffill_raw"]).strip()

                key = (d, apt, turno_norm)

                # Extract ATD candidates from row
                atd_times: List[Tuple[int, int]] = []
                if cols["atd"]:
                    atd_times.extend(extract_atd_candidates(r[cols["atd"]]))

                # Anchor ATDs to date; if ATD < start_dt => +1 day
                atd_dt_list: List[pd.Timestamp] = []
                for hh, mm in atd_times:
                    tdt = d + pd.Timedelta(hours=hh, minutes=mm)
                    if tdt < r["__start_dt"]:
                        tdt = tdt + pd.Timedelta(days=1)
                    atd_dt_list.append(tdt)

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
                        festivo_flag=bool(r["__festivo"]),
                        first_source=src,
                        provided_importo=prov_importo,
                        provided_extra_min=prov_extra_min,
                        provided_night_min=prov_night_min,
                    )
                else:
                    # merge
                    b = blocks[key]
                    b.atd_list.extend(atd_dt_list)
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
        durata_min = int((b.end_dt - b.start_dt).total_seconds() // 60)

        # Turno €
        turno_eur = compute_turno_eur(durata_min, cfg)

        # ATD selection: candidates strictly > end_dt; choose MAX
        candidates = [x for x in b.atd_list if x > b.end_dt]
        atd_sel = max(candidates) if candidates else None

        # Extra minutes (raw) then rounding policy (optional)
        extra_min_raw = compute_extra_min(atd_sel, b.end_dt, b.no_dec)
        extra_min = cfg.rounding_extra.apply(extra_min_raw)

        extra_eur = (extra_min / 60.0) * cfg.rate_extra_per_h

        # Night minutes: on turno + (optional) extra interval
        night_turno = night_minutes(b.start_dt, b.end_dt)

        night_extra = 0
        if extra_min_raw > 0 and (not b.no_dec) and extra_min > 0:
            extra_end = b.end_dt + pd.Timedelta(minutes=extra_min)
            night_extra = night_minutes(b.end_dt, extra_end)

        night_min_raw = night_turno + night_extra
        night_min = cfg.rounding_night.apply(night_min_raw)
        night_eur = compute_night_eur(night_min, cfg)

        subtotal = turno_eur + extra_eur + night_eur
        totale = subtotal * (cfg.festivo_multiplier if b.festivo_flag else 1.0)

        # Format H:MM
        def hmm(m: int) -> str:
            return f"{m // 60}:{m % 60:02d}"

        rows_detail.append({
            "DATA": b.date.strftime("%d/%m/%Y"),
            "APT": b.apt,
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
# Output writer
# -----------------------------

def write_output_excel(output_path: str, detail_df: pd.DataFrame, totals_df: pd.DataFrame, discr_df: pd.DataFrame) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl", datetime_format="YYYY-MM-DD HH:MM") as writer:
        # Order columns for readability
        if not detail_df.empty:
            cols = [
                "DATA", "APT", "TURNO_FFILL", "TURNO_NORMALIZZATO",
                "INIZIO_DT", "FINE_DT", "DURATA_TURNO_MIN", "NO_DEC",
                "ATD_SCELTO",
                "TURNO_EUR",
                "EXTRA_MIN_RAW", "EXTRA_MIN", "EXTRA_H:MM", "EXTRA_EUR",
                "NOTTE_MIN_RAW", "NOTTE_MIN", "NOTTE_EUR",
                "FESTIVO", "TOTALE_BLOCCO_EUR",
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
    p = argparse.ArgumentParser(description="Calcolatore Veratour 2025 (blocchi, extra, notturno, festivi).")
    p.add_argument("-i", "--input", nargs="+", required=True, help="File Excel in input (uno o più).")
    p.add_argument("-o", "--output", required=True, help="File Excel in output (xlsx).")
    p.add_argument("--apt", nargs="*", default=None, help="Filtro APT (es. VRN BGY VCE). Se omesso: tutti.")
    p.add_argument("--holiday-list", default=None, help="File con lista festivi (una data per riga).")

    p.add_argument("--night-mode", choices=["DIFF5", "FULL30"], default="DIFF5",
                   help="DIFF5=0.0833€/min (maggiorazione). FULL30=0.5€/min (30€/h pieno).")

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
        night_mode=args.night_mode,
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
