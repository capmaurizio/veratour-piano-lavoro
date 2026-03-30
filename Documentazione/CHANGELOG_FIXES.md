# 🛠️ Changelog Fix e Modifiche al Sistema

Questo file documenta le correzioni e le modifiche significative apportate al sistema di calcolo.

---

## [2026-03-30] Diagnostica struttura file Excel — Avvisi a video prima dell'elaborazione

**File modificato**: `app_streamlit.py`  
**Commit**: `5b307af`

### Problema riscontrato
Quando veniva caricato un file Excel con struttura non standard (es. foglio chiamato
`"Foglio1"` invece di `"PIANO VOLI"`, o colonna `"H"` invece di `"DATA"`), il sistema
procedeva silenziosamente all'elaborazione producendo un **file di output vuoto** senza
alcuna spiegazione all'utente.

Esempio: il file `P.L. MARZO 2026.xlsx` aveva:
- Foglio: `"Foglio1"` (invece di `"PIANO VOLI"`)
- Colonna data: `"H"` (invece di `"DATA"`)
- Colonna convocazione: `"CONV.NE"` (invece di `"STD"`)

### Soluzione applicata

Aggiunta la funzione `validate_file_structure()` in `app_streamlit.py` che viene
eseguita subito dopo il caricamento del file e **prima** del pulsante "Esegui elaborazione".

| Controllo | Comportamento |
|-----------|---------------|
| Foglio `"PIANO VOLI"` assente | 🟡 Warning con elenco fogli trovati |
| Colonna standard assente ma nome alternativo rilevato | ⚠️ Warning col nome trovato |
| Colonna obbligatoria completamente mancante | 🔴 Errore con nomi accettati |
| Foglio senza dati | 🔴 Errore "Il foglio non contiene dati" |
| Todo ok | Nessun messaggio, elaborazione diretta |

### Colonne verificate

| Colonna attesa | Nomi alternativi accettati |
|----------------|---------------------------|
| `DATA` | `H`, `DATA VOLO`, `DATA/ORA` |
| `APT` | `AEROPORTO`, `AIRPORT` |
| `TURNO` | `NOTE E TURNI`, `TURNI` |
| `STD` | `CONV.NE`, `CONVOCAZIONE`, `STD (ORA DEP)` |
| `ATD` | `ATD REALE`, `PARTENZA REALE` |
| `TOUR OPERATOR` | `OPERATORE`, `TO` |

### Come risolvere file non standard
Il messaggio in app suggerisce all'utente di rinominare il foglio in `PIANO VOLI`
e di assicurarsi che le colonne abbiano i nomi standard. È comunque possibile
tentare l'elaborazione anche in presenza di warning.

---

## [2026-03-28] Fix formula Excel ore extra NAP — Collaboratori/Fattura

**File modificati**:
- `genera_file_calcolo_assistente.py`
- `genera_template_assistente.py`

### Problema riscontrato
La formula Excel generata per il calcolo degli **importi extra** nel foglio fattura/riepilogo assistente usava **sempre €8/h** (hardcoded `=8/60*minuti`) indipendentemente dall'aeroporto.

Per **NAP (Napoli)** le tariffe corrette sono:
- **Senior**: €12/h per ore extra
- **Junior**: €10/h per ore extra

Questo causava un **errore sistematico** nel calcolo della colonna "Importo netto extra" (colonna O del template):
- Esempio: 30 minuti extra a NAP Senior = `30/60 × 12 = €6.00` (corretto) vs `30/60 × 8 = €4.00` (sbagliato con bug)

### Soluzione applicata

| Fix | Dettaglio |
|-----|-----------|
| **`genera_formula_excel_extra()`** | Aggiunto parametro `tariffa_extra_per_h` (default €12) — non più hardcoded €8 |
| **`TARIFFE_EXTRA_PER_APT`** | Aggiunto dizionario con tariffe orarie extra per aeroporto (NAP=12, FCO=12, BGY=8, …) |
| **Template genera** | Formula ora usa la tariffa corretta dell'aeroporto del turno specifico |
| **NAP Standard** | Aggiunto ramo `elif apt_upper == 'NAP'` nel file calcolo generato (prima andava in default €58 errato) |

### Tariffe corrette (Accordo 2026)

| Aeroporto | Senior Extra | Junior Extra |
|-----------|-------------|-------------|
| NAP | €12/h | €10/h |
| FCO Standard | €12/h | €12/h |
| FCO Incentive | €15/h | €15/h |
| VRN | €12/h | €12/h |
| BGY | €10/h | €8/h |

---

## [2026-03-11] Fix calcolo extra NAP — Veratour

**File modificato**: `Veratour/consuntivoveratour.py`

### Problema riscontrato
Il sistema non calcolava gli extra per i voli di Napoli (NAP) nelle seguenti situazioni:

1. **Filtro APT silenziosamente azzerato**: con `apt_filter=['NAP']` il sistema restituiva 0 blocchi a causa di un bug nel pattern regex (`\b(NAP)\b` con gruppo cattura causava un comportamento errato in pandas `str.contains()`).

2. **ATD anomali inquinavano i blocchi**: righe con TURNO vuoto e STD diversa (es. riga NO 7939 con ATD=`13:02` e STD=`17:00` — evidente errore di inserimento) venivano aggiunte al blocco sbagliato abbassando l'ATD massimo sotto la fine turno → extra = 0.

3. **Voli multipli nello stesso turno non gestiti**: un turno (es. `11:40-16:40 DEC`) può coprire più voli nella stessa giornata (es. W46925 STD=14:40 e NO 7939 STD=17:00). Solo il primo volo veniva considerato per il calcolo dell'ATD, ignorando il decollo del volo successivo (NO 7939 ATD=17:12 > fine turno 16:40 → 32 min di extra).

4. **Colonna STD non rilevata**: `detect_columns()` non mappava la colonna `std` del file Excel.

### Soluzione applicata

| Fix | Dettaglio |
|-----|-----------|
| **Filtro APT** | Sostituito `str.contains(regex)` con `.isin()` — semplice e senza warning |
| **Colonna STD** | Aggiunta a `detect_columns()` con pattern `r"^std$"` |
| **STD come fallback ATD** | Per ogni riga, la STD viene aggiunta ai candidati ATD. Se l'ATD reale non è disponibile o è anomalo, si usa STD come "decollo minimo garantito" |
| **Filtraggio ATD anomali** | Un ATD viene scartato se è **più di 2 ore prima della STD** (segno chiaro di errore di inserimento nel foglio) |
| **ffill TURNO** | Mantiene `groupby(DATA)` per propagare il turno a tutti i voli dello stesso giorno/apt, permettendo l'aggregazione corretta di più voli nello stesso blocco |

### Logica di selezione ATD (aggiornata)
Per ogni blocco `(DATA, APT, TURNO)`:
1. Raccoglie tutti gli ATD validi + STD di ogni riga del blocco (dopo filtraggio anomali)
2. Candidati = ATD strettamente > fine turno
3. ATD scelto = **massimo** tra i candidati

### Esempio concreto (22/02/2026 NAP, turno `11:40-16:40 DEC`)

| Volo | STD | ATD | Candidati ATD |
|------|-----|-----|---------------|
| W46925 | 14:40 | 14:48 | 14:48, 14:40 (< 16:40, non candidati) |
| NO 7939 | 17:00 | **17:14** | **17:14 > 16:40 → EXTRA = 34 min = €10,20** |

> ⚠️ **Nota sui dati**: verificare sempre che l'ATD nel foglio Excel sia corretto. In particolare, valori ATD che precedono di molto la STD sono errori di inserimento (il sistema li scarta automaticamente ma vanno corretti nel file sorgente).

---

## Come aggiungere nuovi fix

Quando si corregge un bug o si modifica una regola di calcolo:

1. Modifica il file Python corrispondente
2. Aggiungi una sezione in questo file con:
   - Data
   - File modificato
   - Problema riscontrato
   - Soluzione applicata
   - Esempio concreto (se possibile)
3. Aggiorna il `README.md` del tour operator interessato
4. Fa il push su GitHub: `git add <file> && git commit -m "..." && git push`
