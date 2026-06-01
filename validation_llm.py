#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modulo di validazione LLM (Claude) per i file Excel del piano di lavoro.
Analizza struttura e contenuto e segnala problemi di formato/dati.
"""

import os
import json
import re
import pandas as pd
from typing import Optional
import streamlit as st


# ── Colonne attese nel formato 2026 ─────────────────────────────────────────
COLONNE_ATTESE = [
    "DATA", "CONVOCAZIONE", "AGENZIA", "TOUR OPERATOR",
    "SERVIZIO", "APT", "VOLO", "DEST.NE",
    "STA", "ATA", "STD", "ATD",
    "INIZIO TURNO", "FINE TURNO", "ASSISTENTE",
]

COLONNE_OBBLIGATORIE = [
    "DATA", "TOUR OPERATOR", "APT", "STD", "ATD",
]


def _get_api_key() -> Optional[str]:
    """Recupera la API key da Streamlit secrets o variabile d'ambiente."""
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


def _build_file_summary(file_path: str) -> dict:
    """
    Estrae un riassunto compatto del file Excel per il prompt LLM.
    Ritorna un dizionario con:
      - fogli, colonne, n_righe, campione dati, anomalie rilevate
    """
    result = {
        "fogli": [],
        "foglio_analizzato": None,
        "colonne": [],
        "n_righe": 0,
        "colonne_mancanti": [],
        "campione": [],
        "anomalie": [],
        "valori_unici": {},
    }

    try:
        xls = pd.ExcelFile(file_path)
        result["fogli"] = xls.sheet_names

        # Cerca foglio PIANO VOLI
        target = next(
            (s for s in xls.sheet_names if s.strip().upper() == "PIANO VOLI"),
            xls.sheet_names[0]
        )
        result["foglio_analizzato"] = target

        df = pd.read_excel(file_path, sheet_name=target)
        df.columns = [str(c).strip().upper() for c in df.columns]
        df = df.dropna(how="all")

        result["colonne"] = list(df.columns)
        result["n_righe"] = len(df)

        # Colonne mancanti
        result["colonne_mancanti"] = [
            c for c in COLONNE_OBBLIGATORIE if c not in df.columns
        ]

        # Campione: prime 8 righe non vuote (solo colonne chiave disponibili)
        key_cols = [c for c in COLONNE_ATTESE if c in df.columns][:10]
        sample_df = df[key_cols].head(8)
        result["campione"] = sample_df.astype(str).values.tolist()
        result["campione_header"] = key_cols

        # Valori unici per colonne categoriche
        for col in ["TOUR OPERATOR", "AGENZIA", "APT", "SERVIZIO"]:
            if col in df.columns:
                vals = df[col].dropna().astype(str).str.strip()
                vals = vals[~vals.str.lower().isin(["nan", "none", ""])]
                result["valori_unici"][col] = sorted(vals.unique().tolist())

        # Rilevazione anomalie pre-LLM (alimentano il prompt)
        anomalie = []

        # Date in formato testo (es. "venerdì 29 maggio 2026")
        if "DATA" in df.columns:
            date_series = df["DATA"].dropna().astype(str)
            testo_dates = date_series[
                date_series.str.contains(r'[a-zA-Zà-ù]', regex=True, na=False)
            ]
            if not testo_dates.empty:
                anomalie.append({
                    "tipo": "DATA_FORMATO_TESTO",
                    "n": len(testo_dates),
                    "esempi": testo_dates.head(3).tolist(),
                    "msg": f"{len(testo_dates)} righe con DATA in formato testo invece di data Excel"
                })

        # ATD mancante
        if "ATD" in df.columns:
            missing_atd = df["ATD"].isna().sum()
            if missing_atd > 0:
                anomalie.append({
                    "tipo": "ATD_MANCANTE",
                    "n": int(missing_atd),
                    "msg": f"{missing_atd} righe senza ATD valorizzato"
                })

        # INIZIO/FINE TURNO mancanti
        for col in ["INIZIO TURNO", "FINE TURNO"]:
            if col in df.columns:
                missing = df[col].isna().sum()
                if missing > 0:
                    anomalie.append({
                        "tipo": f"{col.replace(' ','_')}_MANCANTE",
                        "n": int(missing),
                        "msg": f"{missing} righe senza {col} valorizzato"
                    })

        # CONVOCAZIONE mancante
        if "CONVOCAZIONE" in df.columns:
            missing_conv = df["CONVOCAZIONE"].isna().sum()
            if missing_conv > 0:
                anomalie.append({
                    "tipo": "CONVOCAZIONE_MANCANTE",
                    "n": int(missing_conv),
                    "msg": f"{missing_conv} righe senza CONVOCAZIONE"
                })

        # ASSISTENTE mancante
        if "ASSISTENTE" in df.columns:
            missing_ass = df["ASSISTENTE"].isna().sum()
            if missing_ass > 0:
                anomalie.append({
                    "tipo": "ASSISTENTE_MANCANTE",
                    "n": int(missing_ass),
                    "msg": f"{missing_ass} righe senza ASSISTENTE"
                })

        result["anomalie"] = anomalie

    except Exception as e:
        result["errore_lettura"] = str(e)

    return result


def _build_prompt(summary: dict) -> str:
    """Costruisce il prompt da inviare a Claude."""
    return f"""Sei un validatore esperto di file Excel per la gestione dei piani di lavoro aeroportuali di agenzie assistenti.

Analizza il seguente sommario di un file Excel e produci una lista di segnalazioni in italiano.

## Contesto del formato atteso
Il file deve contenere un foglio "PIANO VOLI" con queste colonne:
- DATA: data del servizio (formato data Excel o GG/MM/AAAA, NON testo come "lunedì 1 maggio")
- CONVOCAZIONE: orario di convocazione (HH:MM)
- INIZIO TURNO: orario inizio turno (HH:MM)
- FINE TURNO: orario fine turno (HH:MM)
- TOUR OPERATOR: nome del tour operator (es. VERATOUR, ALPITOUR, FUTURA...)
- AGENZIA: nome agenzia (es. SCAYGROUP, ALISERVICE)
- SERVIZIO: tipo servizio (PARTENZA, ARRIVO, MEET&GREET...)
- APT: codice aeroporto (es. BGY, MXP, LIN)
- VOLO: codice volo
- STD: orario schedulato partenza (HH:MM)
- ATD: orario effettivo partenza (HH:MM)
- ASSISTENTE: nome dell'assistente

## Sommario del file ricevuto
- Fogli presenti: {summary.get('fogli', [])}
- Foglio analizzato: {summary.get('foglio_analizzato')}
- Colonne presenti: {summary.get('colonne', [])}
- Numero righe dati: {summary.get('n_righe', 0)}
- Colonne obbligatorie mancanti: {summary.get('colonne_mancanti', [])}

## Valori unici rilevati
{json.dumps(summary.get('valori_unici', {}), ensure_ascii=False, indent=2)}

## Anomalie pre-rilevate
{json.dumps(summary.get('anomalie', []), ensure_ascii=False, indent=2)}

## Campione dati (prime righe)
Intestazioni: {summary.get('campione_header', [])}
Righe:
{json.dumps(summary.get('campione', []), ensure_ascii=False, indent=2)}

## Istruzioni
Rispondi SOLO con un JSON valido con questa struttura:
{{
  "stato": "ok" | "attenzione" | "errore",
  "sommario": "frase breve che descrive lo stato generale del file",
  "segnalazioni": [
    {{
      "gravita": "errore" | "avviso" | "info",
      "colonna": "nome colonna o null",
      "messaggio": "descrizione chiara del problema in italiano",
      "suggerimento": "come correggerlo"
    }}
  ]
}}

Sii conciso e diretto. Segnala solo problemi reali, non inventare problemi se il file sembra ok.
Se una colonna è assente ma ci sono anomalie rilevate, segnala entrambe.
Non includere spiegazioni fuori dal JSON.
"""


def valida_file_con_llm(file_path: str) -> Optional[dict]:
    """
    Valida il file Excel con Claude.
    Ritorna un dict con: stato, sommario, segnalazioni
    O None se l'API non è disponibile.
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    try:
        import anthropic

        summary = _build_file_summary(file_path)
        prompt = _build_prompt(summary)

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()

        # Estrai JSON dalla risposta
        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None

    except Exception as e:
        return {"stato": "errore", "sommario": f"Errore validazione LLM: {str(e)}", "segnalazioni": []}


def render_validazione_llm(file_path: str, key_prefix: str = ""):
    """
    Componente Streamlit: mostra il pannello di validazione LLM.
    key_prefix: per evitare conflitti di chiave tra chiamate multiple.
    """
    api_key = _get_api_key()
    if not api_key:
        return  # Nessuna chiave, nessun pannello

    cache_key = f"_llm_validation_{file_path}_{key_prefix}"

    # Usa cache nel session_state per non richiamare ogni render
    if cache_key not in st.session_state:
        with st.spinner("🤖 Analisi intelligente del file in corso..."):
            result = valida_file_con_llm(file_path)
            st.session_state[cache_key] = result

    result = st.session_state.get(cache_key)
    if result is None:
        return

    stato = result.get("stato", "ok")
    sommario = result.get("sommario", "")
    segnalazioni = result.get("segnalazioni", [])

    # Header con colore per stato
    if stato == "errore":
        st.error(f"🤖 **Analisi AI** — {sommario}")
    elif stato == "attenzione":
        st.warning(f"🤖 **Analisi AI** — {sommario}")
    else:
        st.success(f"🤖 **Analisi AI** — {sommario}")

    if segnalazioni:
        for s in segnalazioni:
            gravita = s.get("gravita", "info")
            col_name = s.get("colonna")
            msg = s.get("messaggio", "")
            sug = s.get("suggerimento", "")

            col_label = f" `{col_name}`" if col_name else ""
            testo = f"**{col_label}** {msg}"
            if sug:
                testo += f"\n\n💡 *{sug}*"

            if gravita == "errore":
                st.error(testo)
            elif gravita == "avviso":
                st.warning(testo)
            else:
                st.info(testo)

    # Pulsante per rieseguire la validazione
    btn_key = f"riesegui_llm_{key_prefix}"
    if st.button("🔄 Riesegui analisi AI", key=btn_key, type="secondary"):
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        st.rerun()
