# 📊 Aliservice - Calcolatore Piano di Lavoro

Sistema per il calcolo automatico dei consuntivi piano di lavoro per Aliservice.

## 🚀 Quick Start

```bash
# Installa dipendenze
pip install pandas openpyxl python-dateutil

# Esegui calcolo
python3 consuntivoaliservice.py -i "Piano lavoro DICEMBRE 25.xlsx" -o "OUT_ALISERVICE.xlsx"

# Filtra per aeroporto
python3 consuntivoaliservice.py -i "Piano lavoro DICEMBRE 25.xlsx" -o "OUT_ALISERVICE.xlsx" --apt VRN
```

## ✨ Funzionalità

- ✅ **Lettura file Piano Lavoro**: Legge file Excel con più fogli
- ✅ **Filtro Agenzia**: Filtra per colonna `AGENZIA` = "Aliservice" (non TOUR OPERATOR)
- ✅ **Filtro Aeroporti**: Opzionale, filtra per aeroporti specifici
- ✅ **Forward-fill TURNO** (con gestione righe senza orario):
  - Se la riga ha un TURNO esplicito → usa quello (o forward-fill dalla riga precedente)
  - Se la riga **non ha TURNO** (es. M&G con solo CONV.NE) → usa `CONV.NE` come orario di inizio, `CONV.NE + 3h` come fine base
- ✅ **Parse TURNO robusto**: Riconosce vari formati (08-11, 8:00-11, 8.00–11.30, ecc.)
- ✅ **Meet & Greet (M&G)**: Rilevato dalla colonna `ARRIVI/TRF`, tariffa base €65
- ✅ **Gestione mezzanotte**: Turni che attraversano mezzanotte gestiti correttamente
- ✅ **Calcoli tariffe**: TURNO_EUR, EXTRA_EUR, NOTTE_EUR, FESTIVO (+20%), TOTALE
- ✅ **Output Excel**: Genera file con DettaglioBlocchi, TotaliPeriodo, Discrepanze, fogli per aeroporto

## 📋 Formato Input

Il programma legge file Excel "Piano Lavoro" con le seguenti colonne:

- **DATA**: Data del turno
- **AGENZIA**: Deve contenere "Aliservice" (case-insensitive) — colonna di filtro principale
- **TOUR OPERATOR**: Nome del tour operator gestito dall'agenzia (es. 3D GROUP, BRIXIA, FUTURA)
- **APT**: Codice aeroporto (VRN, BGY, NAP, VCE, ecc.)
- **CONV.NE**: Orario di convocazione (usato come inizio turno per righe senza TURNO esplicito)
- **TURNO**: Orario turno (formati supportati: 08-11, 8:00-11, 8.00–11.30, ecc.) — opzionale
- **ARRIVI/TRF**: Tipo servizio speciale (es. `M&G` = Meet & Greet, tariffa €65)
- **ATD**: Orario decollo effettivo (determina la fine reale del blocco)
- **STD**: Orario decollo programmato (usato come fallback se ATD manca)
- **ASSISTENTE**: Nome assistente (opzionale)
- **VOLO**: Numero di volo (opzionale)
- **DEST.NE**: Destinazione (opzionale)

## 📊 Output

Il file Excel generato contiene:

1. **DettaglioBlocchi**: Dettaglio di ogni blocco con:
   - DATA, APT, ASSISTENTE, VOLO, DEST.NE
   - TURNO_FFILL, TURNO_NORMALIZZATO
   - INIZIO_DT, FINE_DT, DURATA_TURNO_MIN
   - ATD_SCELTO, STD_SCELTO
   - TURNO_EUR, EXTRA_MIN, EXTRA_EUR, NOTTE_MIN, NOTTE_EUR
   - FESTIVO, TOTALE_BLOCCO_EUR
   - ERRORE (se presente)
   - SRC_FILE, SRC_SHEET, SRC_ROW0 (riferimenti sorgente)

2. **TotaliPeriodo**: Riepilogo per periodo e aeroporto

3. **Discrepanze**: Eventuali problemi rilevati nei dati

## 🔧 Calcoli e Tariffe

| Tipo servizio | Base EUR | Extra EUR/h |
|---------------|----------|-------------|
| Tour Operator | €55 | €15 |
| MICE | €65 | €15 |
| Viaggi Studio | €55 | €15 |
| VIP Service | €110 | €15 |
| VIP Gate | €130 | €15 |
| **Meet & Greet (M&G)** | **€65** | €15 |

- **Extra**: calcolato come `ATD − (inizio + 3h)`, arrotondato per eccesso a 5 min
- **Notturno**: minuti nella fascia `23:00-03:30`, tariffa €0,031/min
- **Festivo**: +20% sull'intera tariffa (turno + extra + notturno)

## ⚠️ Comportamenti da conoscere

### Righe senza TURNO esplicito (es. M&G)
Se una riga ha `TURNO = vuoto` ma ha `CONV.NE` valorizzata:
- L'inizio del blocco viene impostato all'orario di **CONV.NE** (non forward-fill)
- La fine base = `CONV.NE + 3h`
- La fine effettiva = ATD (se ATD < fine base → EXTRA = 0)
- Il `TURNO_NORMALIZZATO` nel dettaglio sarà `"HH:MM-HH:MM"` calcolato da CONV.NE

> **Esempio**: CONV.NE=17:40, ATD=18:30 → blocco 17:40-18:30, EXTRA=0, TOTALE=€65

### Forward-fill del TURNO
Il forward-fill si applica **solo** alle righe che hanno un turno originale.  
Le righe senza turno usano CONV.NE come descritto sopra, **non** il turno della riga precedente.

## 📝 Storico Fix Principali

| Data | Commit | Fix |
|------|--------|-----|
| 2026-03-31 | `0b5c3d7` | Bug forward-fill TURNO per righe M&G senza orario (8h extra errate) |

Documentazione completa: `Documentazione/CHANGELOG_FIXES.md`

---

**Status**: ✅ Operativo — calcoli e tariffe implementati
