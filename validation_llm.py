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

# ATD NON è obbligatoria (tutti i moduli hanno fallback su STD)
COLONNE_OBBLIGATORIE = [
    "DATA", "TOUR OPERATOR", "APT", "STD",
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


def _load_business_rules() -> str:
    """Carica le regole di business dal file business_rules.md."""
    base = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(base, "business_rules.md")
    try:
        with open(rules_path, encoding="utf-8") as f:
            content = f.read()
        # Tronca a 8000 caratteri per non sforare il contesto
        return content[:8000]
    except Exception:
        return ""


# Regole per-TO: cosa serve per calcolare
# formato: {keyword_match: {"descr": ..., "critici": [(col, motivo)], "colonna_filtro": ..., "filtro_keyword": ...}}
TO_REQUISITI = {
    "veratour": {
        "descr": "Veratour (base 3h €75, extra ATD-fine×€18/h, notturno 23-05)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("STD", "usato come fallback se ATD manca, necessario per extra"),
            ("INIZIO TURNO", "orario inizio turno — serve per calcolo base"),
            ("FINE TURNO", "orario fine turno — serve per calcolo extra"),
        ],
        "utili": [("ATD", "orario decollo effettivo — calcola extra")],
    },
    "alpitour": {
        "descr": "Alpitour (base 3h, extra €20/h, notturno 23-06)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("STD", "necessario per calcolo base e extra"),
            ("INIZIO TURNO", "orario inizio turno"),
            ("FINE TURNO", "orario fine turno"),
        ],
        "utili": [("ATD", "orario decollo effettivo")],
    },
    "aliservice": {
        "descr": "Aliservice (agenzia, filtra su colonna AGENZIA, base 3h €55-€130)",
        "colonna_filtro": "AGENZIA",
        "critici": [
            ("INIZIO TURNO", "orario inizio (o CONVOCAZIONE per M&G)"),
            ("FINE TURNO", "orario fine turno"),
            ("STD", "usato come fine blocco se ATD manca"),
        ],
        "utili": [
            ("CONVOCAZIONE", "usata per M&G quando TURNO mancante"),
            ("ATD", "orario decollo effettivo per calcolo extra"),
        ],
    },
    "baobab": {
        "descr": "Baobab/TH (base 2h30, extra €18/h, notturno 22-06, festivo +30%)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("STD", "necessario per calcolo base e extra"),
            ("INIZIO TURNO", "orario inizio turno"),
            ("FINE TURNO", "orario fine turno"),
        ],
        "utili": [("ATD", "orario decollo effettivo per extra")],
    },
    "domina": {
        "descr": "Domina (base 2h30 per APT, extra €18/h, notturno 22-06, festivo +30%)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("APT", "determina la tariffa base: BGY €80, VRN €85, FCO €90, VCE €100"),
            ("STD", "usato come fine se ATD manca"),
            ("INIZIO TURNO", "orario inizio turno"),
            ("FINE TURNO", "orario fine turno"),
        ],
        "utili": [("ATD", "per extra se ritardo")],
    },
    "micheltours": {
        "descr": "MichelTours (base 3h, extra €18/h, notturno 22-06, festivo +30%)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("STD", "necessario"),
            ("INIZIO TURNO", "orario inizio turno"),
            ("FINE TURNO", "orario fine turno"),
        ],
        "utili": [("ATD", "per extra")],
    },
    "sand": {
        "descr": "SAND (fine turno=STD sempre, extra sempre €0, notturno da CONVOCAZIONE a STD)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("STD", "CRITICO: per Sand è la fine del turno (ATD ignorato contrattualmente)"),
            ("CONVOCAZIONE", "CRITICO: per Sand il notturno si calcola da CONVOCAZIONE a STD"),
            ("INIZIO TURNO", "orario inizio"),
        ],
        "utili": [],
    },
    "caboverdetime": {
        "descr": "Caboverdetime (base=CVC→STD, extra=STD→ATD, notturno 22-06)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("CONVOCAZIONE", "CRITICO: la base si calcola da CONVOCAZIONE a STD"),
            ("STD", "CRITICO: serve per base (CVC→STD) e come inizio extra"),
            ("ATD", "serve per il calcolo dell'extra (STD→ATD) — se manca extra=0"),
        ],
        "utili": [],
    },
    "rusconi": {
        "descr": "Rusconi (base fissa per APT: €100-€140, extra €20/h solo se ATD>STD)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("APT", "determina tariffa: BGY €110, FCO €115, VCE €140, altri €100"),
            ("STD", "necessario: extra calcolato solo se ATD>STD"),
            ("INIZIO TURNO", "orario inizio turno"),
            ("FINE TURNO", "orario fine turno"),
        ],
        "utili": [("ATD", "se ATD>STD viene calcolato l'extra €20/h")],
    },
    "iot": {
        "descr": "IOT (base 2h30, extra €18/h, notturno 22-06)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("STD", "necessario"),
            ("INIZIO TURNO", "orario inizio"),
            ("FINE TURNO", "orario fine"),
        ],
        "utili": [("ATD", "per extra")],
    },
    "flyness": {
        "descr": "Flyness (base 2h30, extra €20/h, notturno 22-06)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("STD", "necessario"),
            ("INIZIO TURNO", "orario inizio"),
            ("FINE TURNO", "orario fine"),
        ],
        "utili": [("ATD", "per extra")],
    },
    "rodocanachi": {
        "descr": "Rodocanachi (base=STD-2h30, extra €18/h da STD, notturno 22-06)",
        "colonna_filtro": "TOUR OPERATOR",
        "critici": [
            ("STD", "CRITICO: la base si calcola come STD-2h30"),
            ("APT", "determina tariffa: VCE/FCO €100, altri €90"),
        ],
        "utili": [("ATD", "per extra da STD")],
    },
}


def _analizza_dati_per_to(df: pd.DataFrame, col_map: dict) -> list:
    """
    Per ogni TO trovato nel file, verifica se i dati necessari
    per i suoi calcoli specifici sono presenti e valorizzati.
    Ritorna lista di problemi trovati.
    """
    problemi = []
    cols_upper = {str(c).strip().upper(): c for c in df.columns}

    def get_col(nome):
        return cols_upper.get(nome.upper())

    to_col = get_col("TOUR OPERATOR")
    agenzia_col = get_col("AGENZIA")
    conv_col = get_col("CONVOCAZIONE") or get_col("CONV.NE") or get_col("CONV")
    arrivi_col = get_col("ARRIVI/TRF") or get_col("ARRIVI TRF")

    for to_key, regole in TO_REQUISITI.items():
        # Trova righe di questo TO
        if regole["colonna_filtro"] == "AGENZIA" and agenzia_col:
            mask = df[agenzia_col].astype(str).str.contains(to_key, case=False, na=False)
        elif to_col:
            mask = df[to_col].astype(str).str.contains(to_key, case=False, na=False)
        else:
            continue

        df_to = df[mask]
        if df_to.empty:
            continue

        n_tot = len(df_to)

        # Controlla ogni campo critico
        for col_name, motivo in regole["critici"]:
            col_actual = get_col(col_name)
            if not col_actual:
                # La colonna non esiste nel file
                # Per INIZIO/FINE TURNO: accettabile se c'è TURNO
                turno_col = get_col("TURNO")
                if col_name in ("INIZIO TURNO", "FINE TURNO") and turno_col:
                    continue  # TURNO presente, ok
                problemi.append({
                    "to": to_key.upper(),
                    "tipo": "COLONNA_ASSENTE",
                    "colonna": col_name,
                    "n_righe": n_tot,
                    "n_vuoti": n_tot,
                    "motivo": motivo,
                    "msg": f"{to_key.upper()}: colonna '{col_name}' assente — {motivo}"
                })
            else:
                # La colonna esiste — quante righe sono vuote?
                vuoti = df_to[col_actual].isna().sum()
                # Per INIZIO/FINE TURNO: se c'è TURNO, le righe vuote sono normali (forward-fill)
                if col_name in ("INIZIO TURNO", "FINE TURNO"):
                    turno_col = get_col("TURNO")
                    if turno_col:
                        continue  # TURNO presente, forward-fill funziona
                if vuoti > 0:
                    pct = int(vuoti / n_tot * 100)
                    # Soglie diverse per criticità
                    # Campi CRITICI per calcolo: segnala anche pochi vuoti
                    problemi.append({
                        "to": to_key.upper(),
                        "tipo": "DATI_MANCANTI",
                        "colonna": col_name,
                        "n_righe": int(n_tot),
                        "n_vuoti": int(vuoti),
                        "pct": pct,
                        "motivo": motivo,
                        "msg": f"{to_key.upper()}: {vuoti}/{n_tot} righe ({pct}%) senza '{col_name}' — {motivo}"
                    })

        # Controllo speciale Aliservice M&G senza CONVOCAZIONE
        if to_key == "aliservice" and arrivi_col and conv_col:
            mg_mask = df_to[arrivi_col].astype(str).str.contains(r"M&G|MEET", case=False, na=False)
            df_mg = df_to[mg_mask]
            if not df_mg.empty:
                mg_senza_conv = df_mg[conv_col].isna().sum()
                if mg_senza_conv > 0:
                    problemi.append({
                        "to": "ALISERVICE",
                        "tipo": "MG_SENZA_CONVOCAZIONE",
                        "colonna": "CONVOCAZIONE",
                        "n_righe": len(df_mg),
                        "n_vuoti": int(mg_senza_conv),
                        "motivo": "Per M&G la CONVOCAZIONE è usata come orario inizio turno",
                        "msg": f"ALISERVICE: {mg_senza_conv} righe M&G senza CONVOCAZIONE — l'inizio del servizio non può essere determinato"
                    })

    return problemi


def _build_file_summary(file_path: str) -> dict:
    """
    Estrae un riassunto compatto del file Excel per il prompt LLM.
    Include analisi per-TO dei campi necessari ai calcoli specifici.
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
        "analisi_per_to": [],
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

        # Colonne obbligatorie mancanti (solo quelle che causano skip del foglio)
        colonne_skip = ["DATA", "APT"]
        result["colonne_mancanti"] = [c for c in colonne_skip if c not in df.columns]
        # Verifica has_orario: serve almeno (INIZIO TURNO + FINE TURNO) o TURNO
        has_orario = ("INIZIO TURNO" in df.columns and "FINE TURNO" in df.columns) or "TURNO" in df.columns
        if not has_orario:
            result["colonne_mancanti"].append("TURNO o (INIZIO TURNO + FINE TURNO)")

        # Campione: prime 8 righe non vuote
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

        # Anomalie generali
        anomalie = []

        # Date in formato testo
        if "DATA" in df.columns:
            date_series = df["DATA"].dropna().astype(str)
            testo_dates = date_series[
                date_series.str.contains(r'[a-zA-Z\u00e0-\u00f9]', regex=True, na=False)
            ]
            if not testo_dates.empty:
                anomalie.append({
                    "tipo": "DATA_FORMATO_TESTO",
                    "n": len(testo_dates),
                    "esempi": testo_dates.head(3).tolist(),
                    "msg": f"{len(testo_dates)} righe con DATA in formato testo (es. '{testo_dates.iloc[0]}') — il programma le gestisce ma è meglio usare formato data Excel"
                })

        result["anomalie"] = anomalie

        # ── Analisi per-TO: controlla dati specifici per ogni calcolo ──────────
        result["analisi_per_to"] = _analizza_dati_per_to(df, {})

    except Exception as e:
        result["errore_lettura"] = str(e)

    return result


def _build_prompt(summary: dict, business_rules: str = "") -> str:
    """Costruisce il prompt da inviare a Claude, includendo le regole di business reali."""
    rules_section = ""
    if business_rules:
        rules_section = f"""
## REGOLE DI BUSINESS DEL PROGRAMMA (estratte dal codice sorgente reale)
QUESTE REGOLE SONO FONDAMENTALI: usale per evitare falsi allarmi.
{business_rules}
"""

    return f"""Sei un validatore esperto di file Excel per la gestione dei piani di lavoro aeroportuali di agenzie assistenti.

Analizza il seguente sommario di un file Excel e produci segnalazioni CONTESTUALI in italiano.
Devi conoscere bene le regole del programma per non segnalare cose che sono normali.
{rules_section}
## Sommario del file ricevuto
- Fogli presenti: {summary.get('fogli', [])}
- Foglio analizzato: {summary.get('foglio_analizzato')}
- Colonne presenti: {summary.get('colonne', [])}
- Numero righe dati: {summary.get('n_righe', 0)}
- Colonne obbligatorie mancanti: {summary.get('colonne_mancanti', [])}

## Tour Operator e Agenzie presenti nel file
{json.dumps(summary.get('valori_unici', {}), ensure_ascii=False, indent=2)}

## Anomalie rilevate automaticamente
{json.dumps(summary.get('anomalie', []), ensure_ascii=False, indent=2)}

## ANALISI PER TOUR OPERATOR — dati necessari per i calcoli
Questi sono i problemi concreti trovati analizzando riga per riga i dati necessari
per ogni specifico calcolo. OGNI problema qui è rilevante perché impatta il calcolo reale:
{json.dumps(summary.get('analisi_per_to', []), ensure_ascii=False, indent=2)}

## Campione dati (prime righe)
Intestazioni: {summary.get('campione_header', [])}
Righe:
{json.dumps(summary.get('campione', []), ensure_ascii=False, indent=2)}

## Istruzioni critiche
- I problemi in "ANALISI PER TOUR OPERATOR" sono GIÀ filtrati correttamente: segnalali tutti
- Ogni problema lì riportato significa che quel calcolo NON può essere eseguito o sarà impreciso
- ATD vuoto per TO che NON siano Caboverdetime: NON è un errore critico (fallback su STD)
- Caboverdetime senza ATD: AVVISO (extra non calcolabile)
- Righe singole con INIZIO/FINE TURNO vuoti: NON è un errore (forward-fill automatico)
- AGENZIA vuota per righe non-Aliservice: NON è un errore
- ASSISTENTE vuoto: NON è un errore
- TO gestiti da Aliservice (BRIXIA, FUTURA, ecc.): NON segnalare come problema
- TO senza modulo di calcolo: segnala solo come INFO

Rispondi SOLO con JSON valido:
{{
  "stato": "ok" | "attenzione" | "errore",
  "sommario": "frase breve sullo stato generale",
  "segnalazioni": [
    {{
      "gravita": "errore" | "avviso" | "info",
      "colonna": "nome colonna o null",
      "messaggio": "problema specifico in italiano",
      "suggerimento": "come correggerlo"
    }}
  ]
}}

Segnala SOLO problemi reali e rilevanti. Non includere nulla fuori dal JSON."""


def valida_file_con_llm(file_path: str) -> Optional[dict]:
    """
    Valida il file Excel con Claude.
    Inietta le regole di business dal codice sorgente reale nel prompt.
    Ritorna un dict con: stato, sommario, segnalazioni
    O None se l'API non è disponibile.
    """
    api_key = _get_api_key()
    if not api_key:
        return None

    try:
        import anthropic

        summary = _build_file_summary(file_path)
        business_rules = _load_business_rules()
        prompt = _build_prompt(summary, business_rules)

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
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
