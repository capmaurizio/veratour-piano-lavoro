#!/usr/bin/env python3
"""Tour Operators — import moduli, detection, processor dictionary."""

import os
import sys
import re
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional, Tuple, Set

# ═══════════════════════════════════════════════════════════════════════════════
# Aggiungi path per import di ciascun modulo tour operator
# ═══════════════════════════════════════════════════════════════════════════════
_BASE = os.path.dirname(os.path.abspath(__file__))

_TO_DIRS = [
    'Veratour', 'Alpitour', 'Aliservice', 'Baobab',
    'Domina', 'MICHELTOURS', ' Sand', 'Caboverdetime', 'Rusconi',
]
for d in _TO_DIRS:
    p = os.path.join(_BASE, d)
    if p not in sys.path:
        sys.path.insert(0, p)

# ═══════════════════════════════════════════════════════════════════════════════
# Import moduli tour operator (esattamente come nell'originale funzionante)
# ═══════════════════════════════════════════════════════════════════════════════
from consuntivoveratour import (
    CalcConfig as VeratourCalcConfig,
    RoundingPolicy,
    process_files as process_files_veratour,
    write_output_excel as write_output_excel_veratour,
    load_holiday_list,
)

try:
    from consuntivoalpitour import (
        CalcConfig as AlpitourCalcConfig,
        process_files as process_files_alpitour,
        write_output_excel as write_output_excel_alpitour,
        validate_file_complete as validate_file_alpitour,
    )
    ALPITOUR_AVAILABLE = True
except ImportError:
    ALPITOUR_AVAILABLE = False
    AlpitourCalcConfig = None
    process_files_alpitour = None
    write_output_excel_alpitour = None
    validate_file_alpitour = None

try:
    from consuntivoaliservice import (
        CalcConfig as AliserviceCalcConfig,
        process_files as process_files_aliservice,
        write_output_excel as write_output_excel_aliservice,
    )
    ALISERVICE_AVAILABLE = True
except ImportError:
    ALISERVICE_AVAILABLE = False
    AliserviceCalcConfig = None
    process_files_aliservice = None
    write_output_excel_aliservice = None

try:
    from consuntivobaobab import (
        CalcConfig as BaobabCalcConfig,
        process_files as process_files_baobab,
        write_output_excel as write_output_excel_baobab,
    )
    BAOBAB_AVAILABLE = True
except ImportError:
    BAOBAB_AVAILABLE = False
    BaobabCalcConfig = None
    process_files_baobab = None
    write_output_excel_baobab = None

try:
    from consuntivodomina import (
        CalcConfig as DominaCalcConfig,
        process_files as process_files_domina,
        write_output_excel as write_output_excel_domina,
    )
    DOMINA_AVAILABLE = True
except ImportError:
    DOMINA_AVAILABLE = False
    DominaCalcConfig = None
    process_files_domina = None
    write_output_excel_domina = None

try:
    from consuntivocaboverdetime import (
        CalcConfig as CaboverdetimeCalcConfig,
        process_files as process_files_caboverdetime,
        write_output_excel as write_output_excel_caboverdetime,
    )
    CABOVERDETIME_AVAILABLE = True
except ImportError:
    CABOVERDETIME_AVAILABLE = False
    CaboverdetimeCalcConfig = None
    process_files_caboverdetime = None
    write_output_excel_caboverdetime = None

try:
    from consuntivorusconi import (
        CalcConfig as RusconiCalcConfig,
        process_files as process_files_rusconi,
        write_output_excel as write_output_excel_rusconi,
    )
    RUSCONI_AVAILABLE = True
except ImportError:
    RUSCONI_AVAILABLE = False
    RusconiCalcConfig = None
    process_files_rusconi = None
    write_output_excel_rusconi = None

try:
    from consuntivomicheltours import (
        CalcConfig as MichelToursCalcConfig,
        process_files as process_files_micheltours,
        write_output_excel as write_output_excel_micheltours,
    )
    MICHELTOURS_AVAILABLE = True
except ImportError:
    MICHELTOURS_AVAILABLE = False
    MichelToursCalcConfig = None
    process_files_micheltours = None
    write_output_excel_micheltours = None

try:
    from consuntivosand import (
        CalcConfig as SandCalcConfig,
        process_files as process_files_sand,
        write_output_excel as write_output_excel_sand,
    )
    SAND_AVAILABLE = True
except ImportError:
    SAND_AVAILABLE = False
    SandCalcConfig = None
    process_files_sand = None
    write_output_excel_sand = None


# ═══════════════════════════════════════════════════════════════════════════════
# Funzioni di utilità
# ═══════════════════════════════════════════════════════════════════════════════

def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizza i nomi delle colonne (UPPER)."""
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df


def find_col(df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
    """Trova una colonna che corrisponde a uno dei pattern."""
    cols = [str(c).upper() for c in df.columns]
    for pat in patterns:
        rx = re.compile(pat, re.IGNORECASE)
        for c in cols:
            if rx.search(c):
                return c
    return None


def detect_tour_operators(file_path: str) -> Tuple[Set[str], Set[str]]:
    """
    Rileva tutti i tour operator dal file Excel.
    Returns: (tour_operators, aliservice_managed_tour_operators)
    """
    tour_operators: Set[str] = set()
    aliservice_managed: Set[str] = set()

    try:
        xls = pd.ExcelFile(file_path)
        target_sheet = None
        for sheet_name in xls.sheet_names:
            if sheet_name.upper().strip() == "PIANO VOLI":
                target_sheet = sheet_name
                break

        sheets_to_process = [target_sheet] if target_sheet else xls.sheet_names

        for sheet_name in sheets_to_process:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            if df is None or df.empty:
                continue

            df = normalize_cols(df)

            to_col = find_col(df, [r"TOUR\s*OPERATOR", r"^TO$", r"OPERATORE"])
            if to_col:
                unique_values = df[to_col].dropna().astype(str).str.strip()
                unique_values = unique_values[unique_values != ""]
                unique_values = unique_values[unique_values.str.lower() != "nan"]
                unique_values = unique_values[unique_values.str.lower() != "none"]
                tour_operators.update(unique_values.unique())

            agenzia_col = find_col(df, [r"^AGENZIA$", r"\bAGENCY\b"])
            if agenzia_col and to_col:
                mask_aliservice = df[agenzia_col].astype(str).str.contains(r"aliservice", case=False, na=False)
                if mask_aliservice.any():
                    aliservice_rows = df[mask_aliservice]
                    if to_col in aliservice_rows.columns:
                        managed_tos = aliservice_rows[to_col].dropna().astype(str).str.strip()
                        managed_tos = managed_tos[managed_tos != ""]
                        managed_tos = managed_tos[managed_tos.str.lower() != "nan"]
                        managed_tos = managed_tos[managed_tos.str.lower() != "none"]
                        aliservice_managed.update(managed_tos.unique())
    except Exception as e:
        st.warning(f"Errore nel rilevare tour operatour: {str(e)}")

    return tour_operators, aliservice_managed


# Alias noti: varianti ortografiche del TO nel file → nome cartella normalizzato
# Es: "CAPOVERDE TIME" → clean="capoverdetime" ma cartella si chiama "Caboverdetime"
_FOLDER_ALIASES: Dict[str, str] = {
    'capoverdetime': 'caboverdetime',
    'capoverde':     'caboverdetime',
}


def find_tour_operator_folder(to_name: str, base_path: str = ".") -> Optional[str]:
    """Cerca la cartella del tour operator con file consuntivo*.py."""
    to_clean = re.sub(r'[^a-zA-Z]', '', to_name).lower()
    # Risolvi alias noti (es. capoverdetime → caboverdetime)
    to_clean_resolved = _FOLDER_ALIASES.get(to_clean, to_clean)

    if os.path.exists(base_path):
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path):
                item_clean = re.sub(r'[^a-zA-Z]', '', item).lower()
                match = (
                    item_clean == to_clean or to_clean in item_clean or item_clean in to_clean
                    or item_clean == to_clean_resolved
                    or to_clean_resolved in item_clean
                    or item_clean in to_clean_resolved
                )
                if match:
                    if os.path.exists(item_path):
                        for file in os.listdir(item_path):
                            if file.startswith('consuntivo') and file.endswith('.py'):
                                return item_path

    return None


def get_tour_operator_module_name(to_name: str) -> Optional[str]:
    """Restituisce il nome normalizzato del tour operator."""
    to_clean = re.sub(r'[^a-zA-Z]', '', to_name).lower()

    if 'baobab' in to_clean or to_clean == 'th':
        return 'baobab'
    elif 'micheltour' in to_clean:          # fix: cattura sia MICHELTOUR che MICHELTOURS
        return 'micheltours'
    elif 'aliservice' in to_clean:
        return 'aliservice'
    elif 'caboverdetime' in to_clean or 'capoverde' in to_clean:  # fix: CAPOVERDE TIME
        return 'caboverdetime'
    elif 'sand' in to_clean:
        return 'sand'
    elif 'rusconi' in to_clean:
        return 'rusconi'
    elif 'domina' in to_clean:
        return 'domina'
    elif 'alpitour' in to_clean:
        return 'alpitour'
    elif 'veratour' in to_clean:
        return 'veratour'

    return to_clean


def get_tour_operator_processors(apt_filter, night_mode, round_extra_mode,
                                  round_extra_step, round_night_mode,
                                  round_night_step, holiday_dates) -> dict:
    """
    Restituisce il dizionario dei processori per tutti i tour operator supportati.
    Esattamente come nell'originale funzionante da git main.
    """
    return {
        'veratour': {
            'available': True,
            'config_class': VeratourCalcConfig,
            'process_func': process_files_veratour,
            'write_func': write_output_excel_veratour,
            'config_kwargs': lambda: {
                'apt_filter': apt_filter if apt_filter else None,
                'night_mode': night_mode,
                'rounding_extra': RoundingPolicy(round_extra_mode, round_extra_step),
                'rounding_night': RoundingPolicy(round_night_mode, round_night_step),
                'holiday_dates': holiday_dates,
            }
        },
        'alpitour': {
            'available': ALPITOUR_AVAILABLE,
            'config_class': AlpitourCalcConfig,
            'process_func': process_files_alpitour,
            'write_func': write_output_excel_alpitour,
            'config_kwargs': lambda: {
                'apt_filter': apt_filter if apt_filter else None,
                'rounding_extra': RoundingPolicy("NONE", 5),
                'rounding_night': RoundingPolicy("NONE", 5),
                'holiday_dates': holiday_dates,
            }
        },
        'aliservice': {
            'available': ALISERVICE_AVAILABLE,
            'config_class': AliserviceCalcConfig,
            'process_func': process_files_aliservice,
            'write_func': write_output_excel_aliservice,
            'config_kwargs': lambda: {
                'apt_filter': apt_filter if apt_filter else None,
                'rounding_extra': RoundingPolicy("NONE", 5),
                'rounding_night': RoundingPolicy("NONE", 5),
                'holiday_dates': holiday_dates,
            }
        },
        'baobab': {
            'available': BAOBAB_AVAILABLE,
            'config_class': BaobabCalcConfig,
            'process_func': process_files_baobab,
            'write_func': write_output_excel_baobab,
            'config_kwargs': lambda: {
                'apt_filter': apt_filter if apt_filter else None,
                'rounding_extra': RoundingPolicy("NONE", 5),
                'rounding_night': RoundingPolicy("NONE", 5),
                'holiday_dates': holiday_dates,
            }
        },
        'domina': {
            'available': DOMINA_AVAILABLE,
            'config_class': DominaCalcConfig,
            'process_func': process_files_domina,
            'write_func': write_output_excel_domina,
            'config_kwargs': lambda: {
                'apt_filter': apt_filter if apt_filter else None,
                'rounding_extra': RoundingPolicy("NONE", 5),
                'rounding_night': RoundingPolicy("NONE", 5),
                'holiday_dates': holiday_dates,
            }
        },
        'micheltours': {
            'available': MICHELTOURS_AVAILABLE,
            'config_class': MichelToursCalcConfig,
            'process_func': process_files_micheltours,
            'write_func': write_output_excel_micheltours,
            'config_kwargs': lambda: {
                'apt_filter': apt_filter if apt_filter else None,
                'rounding_extra': RoundingPolicy("NONE", 5),
                'rounding_night': RoundingPolicy("NONE", 5),
                'holiday_dates': holiday_dates,
            }
        },
        'sand': {
            'available': SAND_AVAILABLE,
            'config_class': SandCalcConfig,
            'process_func': process_files_sand,
            'write_func': write_output_excel_sand,
            'config_kwargs': lambda: {
                'apt_filter': apt_filter if apt_filter else None,
                'rounding_extra': RoundingPolicy("NONE", 5),
                'rounding_night': RoundingPolicy("NONE", 5),
                'holiday_dates': holiday_dates,
            }
        },
        'caboverdetime': {
            'available': CABOVERDETIME_AVAILABLE,
            'config_class': CaboverdetimeCalcConfig,
            'process_func': process_files_caboverdetime,
            'write_func': write_output_excel_caboverdetime,
            'config_kwargs': lambda: {
                'apt_filter': apt_filter if apt_filter else None,
                'rounding_extra': RoundingPolicy("NONE", 5),
                'rounding_night': RoundingPolicy("NONE", 5),
                'holiday_dates': holiday_dates,
            }
        },
        'rusconi': {
            'available': RUSCONI_AVAILABLE,
            'config_class': RusconiCalcConfig,
            'process_func': process_files_rusconi,
            'write_func': write_output_excel_rusconi,
            'config_kwargs': lambda: {
                'apt_filter': apt_filter if apt_filter else None,
                'rounding_extra': RoundingPolicy("NONE", 5),
                'rounding_night': RoundingPolicy("NONE", 5),
                'holiday_dates': holiday_dates,
            }
        },
    }
