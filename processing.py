#!/usr/bin/env python3
"""Processing — logica di calcolo + generazione output Excel."""

import io
import os
import re
import tempfile
import streamlit as st
import pandas as pd
from typing import Tuple, Dict, Set

from tour_operators import (
    detect_tour_operators,
    find_tour_operator_folder,
    get_tour_operator_module_name,
    get_tour_operator_processors,
    load_holiday_list,
    write_output_excel_veratour,
    write_output_excel_alpitour,
    ALPITOUR_AVAILABLE,
)


def run_calculation(
    tmp_path: str,
    uploaded_file_name: str,
    apt_filter,
    night_mode: str,
    round_extra_mode: str,
    round_extra_step: int,
    round_night_mode: str,
    round_night_step: int,
    holiday_file,
) -> dict:
    """
    Esegue l'elaborazione completa.
    Restituisce dict con chiavi:
      output_buffer, output_filename, detail_df, totals_df, discr_df,
      processed_count, errors
    Esattamente come nell'originale funzionante da git main.
    """
    # Carica festivi se presente
    holiday_dates = None
    if holiday_file is not None:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt") as tmp_holiday:
            tmp_holiday.write(holiday_file.getvalue().decode('utf-8'))
            tmp_holiday_path = tmp_holiday.name
        try:
            holiday_dates = load_holiday_list(tmp_holiday_path)
        finally:
            os.unlink(tmp_holiday_path)

    # Rileva tour operator
    tour_operators, aliservice_managed = detect_tour_operators(tmp_path)

    # Verifica se Aliservice è presente
    aliservice_found = False
    aliservice_folder = find_tour_operator_folder("Aliservice")
    if aliservice_managed and aliservice_folder:
        from tour_operators import ALISERVICE_AVAILABLE
        if ALISERVICE_AVAILABLE:
            aliservice_found = True

    # Filtra TO gestiti da Aliservice dalla lista principale
    tour_operators_to_check = tour_operators - aliservice_managed

    # Mappa i tour operator trovati ai loro nomi normalizzati
    found_tour_operators: Dict[str, dict] = {}
    for to_name in tour_operators_to_check:
        folder_path = find_tour_operator_folder(to_name)
        if folder_path:
            module_name = get_tour_operator_module_name(to_name)
            if module_name:
                found_tour_operators[module_name] = {
                    'original_name': to_name,
                    'folder': folder_path,
                }

    all_detail_dfs = []
    all_totals_dfs = []
    all_discr_dfs = []

    # Dizionario processori
    tour_operator_processors = get_tour_operator_processors(
        apt_filter, night_mode, round_extra_mode, round_extra_step,
        round_night_mode, round_night_step, holiday_dates,
    )

    # Prepara lista tour operator da elaborare
    tour_operators_to_process = []
    warnings_list = []

    for module_name, to_info in found_tour_operators.items():
        if module_name in tour_operator_processors:
            processor = tour_operator_processors[module_name]
            if processor['available'] and processor['config_class'] and processor['process_func']:
                tour_operators_to_process.append({
                    'name': to_info['original_name'],
                    'module_name': module_name,
                    'processor': processor,
                    'is_aliservice': False,
                })
            else:
                warnings_list.append(
                    f"{to_info['original_name']} rilevato ma modulo non disponibile."
                )

    # Aggiungi Aliservice se presente
    if aliservice_found and 'aliservice' in tour_operator_processors:
        processor = tour_operator_processors['aliservice']
        if processor['available'] and processor['config_class'] and processor['process_func']:
            tour_operators_to_process.append({
                'name': 'Aliservice',
                'module_name': 'aliservice',
                'processor': processor,
                'is_aliservice': True,
            })
        else:
            warnings_list.append("Aliservice rilevato ma modulo non disponibile.")

    # Mostra warning
    for w in warnings_list:
        st.warning(w)

    # Mostra i TO che verranno elaborati
    if tour_operators_to_process:
        num_cols = min(len(tour_operators_to_process), 4)
        cols = st.columns(num_cols)
        for idx, to_info in enumerate(tour_operators_to_process):
            with cols[idx % num_cols]:
                st.info(f"Elaborazione {to_info['name']}...")

    # Elabora tutti i tour operator
    processed_count = 0
    errors = []

    for to_info in tour_operators_to_process:
        processor = to_info['processor']
        try:
            cfg = processor['config_class'](**processor['config_kwargs']())
            detail, totals, discr = processor['process_func']([tmp_path], cfg)
            all_detail_dfs.append(detail)
            all_totals_dfs.append(totals)
            all_discr_dfs.append(discr)
            processed_count += 1
        except Exception as e:
            errors.append(f"{to_info['name']}: {str(e)}")

    # Mostra errori
    for error in errors:
        st.error(f"Errore durante l'elaborazione: {error}")

    if processed_count == 0:
        st.error("Nessun tour operatour con calcolo disponibile trovato nel file.")
        return None

    # Combina risultati
    if all_detail_dfs:
        detail_df = pd.concat(all_detail_dfs, ignore_index=True)
        totals_df = pd.concat(all_totals_dfs, ignore_index=True)
        discr_list = [d for d in all_discr_dfs if d is not None and not d.empty]
        discr_df = pd.concat(discr_list, ignore_index=True) if discr_list else pd.DataFrame()
    else:
        detail_df = pd.DataFrame()
        totals_df = pd.DataFrame()
        discr_df = pd.DataFrame()

    # Genera output Excel
    output_buffer = io.BytesIO()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_output:
        output_path = tmp_output.name

    # Usa la funzione di scrittura appropriata
    if processed_count > 1 and ALPITOUR_AVAILABLE and write_output_excel_alpitour:
        write_output_excel_alpitour(output_path, detail_df, totals_df, discr_df)
    elif processed_count > 0:
        first_processed = list(found_tour_operators.keys())[0] if found_tour_operators else None
        if aliservice_found and 'aliservice' in tour_operator_processors:
            processor = tour_operator_processors['aliservice']
            if processor.get('write_func'):
                processor['write_func'](output_path, detail_df, totals_df, discr_df)
            elif ALPITOUR_AVAILABLE and write_output_excel_alpitour:
                write_output_excel_alpitour(output_path, detail_df, totals_df, discr_df)
            else:
                write_output_excel_veratour(output_path, detail_df, totals_df, discr_df)
        elif first_processed and first_processed in tour_operator_processors:
            processor = tour_operator_processors[first_processed]
            if processor.get('write_func'):
                processor['write_func'](output_path, detail_df, totals_df, discr_df)
            elif ALPITOUR_AVAILABLE and write_output_excel_alpitour:
                write_output_excel_alpitour(output_path, detail_df, totals_df, discr_df)
            else:
                write_output_excel_veratour(output_path, detail_df, totals_df, discr_df)
        else:
            if ALPITOUR_AVAILABLE and write_output_excel_alpitour:
                write_output_excel_alpitour(output_path, detail_df, totals_df, discr_df)
            else:
                write_output_excel_veratour(output_path, detail_df, totals_df, discr_df)
    else:
        write_output_excel_veratour(output_path, detail_df, totals_df, discr_df)

    # Aggiungi foglio TourOperatourRilevati
    _add_tour_operator_sheet(
        output_path, detail_df, tour_operators, aliservice_managed,
        aliservice_found, found_tour_operators, tour_operator_processors,
    )

    # Leggi il file generato
    with open(output_path, 'rb') as f:
        output_buffer.write(f.read())
    output_buffer.seek(0)

    # Cleanup
    if os.path.exists(output_path):
        os.unlink(output_path)

    return {
        'output_buffer': output_buffer.getvalue(),
        'output_filename': f"OUT_{uploaded_file_name}",
        'detail_df': detail_df,
        'totals_df': totals_df,
        'discr_df': discr_df,
        'processed_count': processed_count,
        'errors': errors,
    }


def _add_tour_operator_sheet(
    output_path: str,
    detail_df: pd.DataFrame,
    tour_operators: Set[str],
    aliservice_managed: Set[str],
    aliservice_found: bool,
    found_tour_operators: dict,
    tour_operator_processors: dict,
):
    """Aggiunge il foglio TourOperatourRilevati all'Excel di output."""
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill

    wb = load_workbook(output_path)

    if "TourOperatourRilevati" in wb.sheetnames:
        wb.remove(wb["TourOperatourRilevati"])
    if "TourOperatourNonElaborati" in wb.sheetnames:
        wb.remove(wb["TourOperatourNonElaborati"])

    ws = wb.create_sheet("TourOperatourRilevati", 0)

    elaborated_tour_operators: Set[str] = set()
    if not detail_df.empty and 'TOUR OPERATOR' in detail_df.columns:
        elaborated_tour_operators = set(detail_df['TOUR OPERATOR'].dropna().astype(str).unique())

    tour_operators_for_list = tour_operators - aliservice_managed
    if aliservice_found:
        tour_operators_for_list.add("ALISERVICE")

    tour_operator_list = []
    for to_name in sorted(tour_operators_for_list):
        to_clean = re.sub(r'[^a-zA-Z]', '', to_name).lower()
        is_supported = False
        status = "Non codificato"

        if to_name.upper() == "ALISERVICE" and aliservice_found:
            if not detail_df.empty:
                if 'AGENZIA' in detail_df.columns:
                    if detail_df['AGENZIA'].astype(str).str.contains('aliservice', case=False, na=False).any():
                        is_supported = True
                        status = "Codificato - Elaborato"
                elif 'TOUR OPERATOR' in detail_df.columns:
                    for elaborated_to in elaborated_tour_operators:
                        if 'aliservice' in str(elaborated_to).lower():
                            is_supported = True
                            status = "Codificato - Elaborato"
                            break

            if not is_supported:
                is_supported = True
                status = "Codificato - Rilevato ma senza dati elaborati"
        else:
            if not detail_df.empty and 'TOUR OPERATOR' in detail_df.columns:
                for elaborated_to in elaborated_tour_operators:
                    elaborated_clean = re.sub(r'[^a-zA-Z]', '', str(elaborated_to)).lower()
                    if to_clean == elaborated_clean or to_clean in elaborated_clean or elaborated_clean in to_clean:
                        is_supported = True
                        status = "Codificato - Elaborato"
                        break

            if not is_supported:
                module_name = get_tour_operator_module_name(to_name)
                if module_name and module_name in found_tour_operators:
                    is_supported = True
                    status = "Codificato - Rilevato ma senza dati elaborati"
                elif module_name and module_name in tour_operator_processors:
                    processor = tour_operator_processors[module_name]
                    if processor['available'] and processor['config_class']:
                        is_supported = True
                        status = "Codificato - Rilevato ma senza dati elaborati"

        if not is_supported:
            folder_path = find_tour_operator_folder(to_name)
            if folder_path:
                status = "Modulo presente ma non rilevato nel file"
            else:
                status = "Non codificato"

        note = (
            "Calcolo tariffe disponibile e applicato" if status == "Codificato - Elaborato" else
            "Calcolo tariffe disponibile ma nessun dato da elaborare" if "Codificato" in status else
            "Calcolo tariffe non disponibile - da codificare"
        )

        tour_operator_list.append({
            "Tour Operatour": to_name,
            "Status": status,
            "Note": note,
        })

    # Scrivi header
    ws.cell(row=1, column=1, value="Tour Operatour")
    ws.cell(row=1, column=2, value="Status")
    ws.cell(row=1, column=3, value="Note")

    for idx, to_info in enumerate(tour_operator_list, 2):
        ws.cell(row=idx, column=1, value=to_info["Tour Operatour"])
        ws.cell(row=idx, column=2, value=to_info["Status"])
        ws.cell(row=idx, column=3, value=to_info["Note"])

    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    for col in range(1, 4):
        cell = ws.cell(row=1, column=col)
        cell.fill = header_fill
        cell.font = header_font

    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 60

    wb.save(output_path)
