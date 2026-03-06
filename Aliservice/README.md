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
- ✅ **Filtro Tour Operator**: Filtra automaticamente per "Aliservice"
- ✅ **Filtro Aeroporti**: Opzionale, filtra per aeroporti specifici
- ✅ **Forward-fill TURNO**: Gestisce TURNO vuoti usando forward-fill per DATA
- ✅ **Parse TURNO robusto**: Riconosce vari formati (08-11, 8:00-11, 8.00–11.30, ecc.)
- ✅ **Gestione mezzanotte**: Turni che attraversano mezzanotte gestiti correttamente
- ✅ **Output Excel**: Genera file con DettaglioBlocchi, TotaliPeriodo, Discrepanze

## 📋 Formato Input

Il programma legge file Excel "Piano Lavoro" con le seguenti colonne:

- **DATA**: Data del turno
- **TOUR OPERATOR**: Deve contenere "Aliservice" (case-insensitive)
- **APT**: Codice aeroporto (VRN, BGY, NAP, VCE, ecc.)
- **TURNO**: Orario turno (formati supportati: 08-11, 8:00-11, 8.00–11.30, ecc.)
- **ATD**: Orario decollo effettivo (opzionale)
- **STD**: Orario decollo programmato (opzionale)
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

## 🔧 Calcoli

**⚠️ ATTENZIONE**: I calcoli (TURNO_EUR, EXTRA_EUR, NOTTE_EUR, ecc.) sono attualmente impostati a 0.

Le regole di calcolo per Aliservice devono essere ancora implementate secondo le specifiche fornite.

## 📝 Note

- Il programma è compatibile con la struttura del file "Piano Lavoro" usata da Veratour e Alpitour
- Supporta file con più fogli
- Gestisce automaticamente forward-fill del TURNO per DATA
- Rileva automaticamente le colonne anche se i nomi variano leggermente

---

**Status**: ✅ Lettura file implementata | ⏳ Calcoli da implementare

