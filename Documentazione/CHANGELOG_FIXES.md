# 🛠️ Changelog Fix e Modifiche al Sistema

Questo file documenta le correzioni e le modifiche significative apportate al sistema di calcolo.

---

## [2026-03-31] Fix Aliservice — Forward-fill TURNO errato per righe senza orario (M&G)

**File modificato**: `Aliservice/consuntivoaliservice.py`  
**Commit**: `0b5c3d7`

### Problema riscontrato

Le righe Aliservice **senza TURNO esplicito** (es. servizi M&G con solo CONV.NE e STD/ATD)
venivano aggregate al blocco sbagliato tramite forward-fill, ereditando l'orario di inizio
della riga precedente. Questo causava un calcolo degli extra completamente errato.

**Caso concreto** — riga del 11/02/2026, BGY, 3D GROUP, M&G:

| Campo | Valore nel file |
|-------|----------------|
| DATA | 11/02/2026 |
| CONV.NE | 17:40 |
| TURNO | *(vuoto)* |
| STD | 18:10 |
| ATD | 18:30 |
| ARRIVI/TRF | M&G |

**Risultato ERRATO (prima del fix):**

| Campo | Valore errato | Perché |
|-------|--------------|--------|
| TURNO_NORMALIZZATO | `07:30-13:00` | Forward-fill dalla riga ALL sopra |
| INIZIO | `07:30` | Preso dal turno fwd-fillato |
| FINE | `18:30` | ATD corretto |
| EXTRA_MIN | **480 min = 8 ore** ❌ | `18:30 − (07:30+3h) = 18:30−10:30` |
| TOTALE | **€185,00** ❌ | `€65 base + €120 extra` |

**Risultato CORRETTO (dopo il fix):**

| Campo | Valore corretto | Perché |
|-------|----------------|--------|
| TURNO_NORMALIZZATO | `17:40-20:40` | Da CONV.NE=17:40 |
| INIZIO | `17:40` | CONV.NE ✅ |
| FINE | `18:30` | ATD ✅ |
| EXTRA_MIN | **0 min** ✅ | ATD 18:30 < fine_base 20:40 |
| TOTALE | **€65,00** ✅ | Solo tariffa M&G base |

### Causa tecnica

Il forward-fill del TURNO (riga `sdf["__turno_ffill"] = ffill_src.ffill()`) veniva eseguito
**prima** del blocco di controllo `mask_no_turno`. Di conseguenza, `__start_str` risultava
già valorizzato con l'orario della riga precedente, rendendo la maschera `mask_no_turno`
sempre `False` e impedendo l'attivazione della logica di fallback su CONV.NE.

### Soluzione applicata

1. **Flag pre-ffill**: aggiunto `sdf["__turno_originale_mancante"] = ffill_src.isna()`
   **prima** del forward-fill, in modo da sapere quali righe non avevano turno originale.

2. **Logica corretta per righe senza turno**: per quelle righe si usa `CONV.NE` come
   orario di inizio (non `CONV.NE - 15min` come in precedenza, ma direttamente CONV.NE).

3. **Chiave blocco univoca**: `__turno_norm` viene resettato a `"HH:MM-HH:MM"` basato su
   CONV.NE, evitando che la riga venga erroneamente aggregata al blocco del forward-fill.

4. **Fine effettiva**: rimane gestita correttamente dall'ATD nell'aggregazione successiva.

### Impatto

- ✅ Tutte le righe Aliservice senza TURNO (M&G, etc.) ora calcolano correttamente
- ✅ Le righe con TURNO esplicito non sono impattate
- ✅ Il forward-fill continua a funzionare per le righe che ne hanno legittimamente bisogno

---

## [2026-03-30] Fix calcolo notturno FCO — Orario inizio/fine nel form assistenti

**File modificati**: `app_assistenti.py`

### Problema

L'app assistenti calcolava i minuti notturni FCO usando un **fallback impreciso**: assumeva
che tutti i minuti notturni ricadessero nel forfait (prime 2h30), con l'eccesso negli extra.
In scenari con servizio misto giorno→notte (es.: 21:30-01:30) questo causava una **sovrastima
di fino €2,08** nel compenso notturno.

**Causa tecnica**: `calculate_tariffa_from_inputs()` chiamava `calcola_tariffa_collaboratore()`
senza passare `inizio_dt` e `fine_dt`, attivando il percorso fallback in `_calcola_noturno_extra_fco`.

**Esempio di errore (scenario misto 21:30-01:30 con 60 min extra)**:

| | notte_forfait | notte_extra | totale_notte |
|---|---|---|---|
| Fallback (sbagliato) | 150 min | 0 min | **€11,20** |
| Con timestamp (corretto) | 90 min | 60 min | **€9,12** |
| **Differenza** | | | **-€2,08** |

### Soluzione applicata

1. **Nuovo form di compilazione turni** (expander per ogni turno) in `app_assistenti.py`:
   - Campo `🕐 Orario inizio servizio` (`st.time_input`)
   - Campo `🕐 Orario fine effettivo` (`st.time_input`)
   - Campo `⏱️ Extra ritardo ATD (min)` (`st.number_input`)
   - Gestione automatica del cambio giorno (es.: inizio 23:00, fine 01:30)
   - Display anteprima: durata totale, min notturni, min extra
   - Per FCO: mostra separazione **notte forfait / notte extra** in real-time
   - Calcolo completo €base/extra/notte/totale con aggiornamento live
   - Tasto **💾 Salva turno** → salva in JSON con tutti i campi (inclusi notte_forfait_min, notte_extra_min)

2. **Firma estesa** di `calculate_tariffa_from_inputs()`:
   - Aggiunti parametri `inizio_dt: Optional[datetime]` e `fine_dt: Optional[datetime]`
   - Passati a `calcola_tariffa_collaboratore()` per abilitare il calcolo esatto

3. **Calcolo notte esatto** via `_calcola_noturno_extra_fco()` con timestamp reali:
   - Minuto per minuto, rispetta la fascia TO (SAND vs altri)
   - Split preciso forfait/extra senza approssimazioni

---

## [2026-03-30] Verifica e documentazione regole FCO — Calcolo compensi e maggiorazione notturna

**File modificato**: `tariffe_collaboratori.py`

### Verifica regole ufficiali

Ricevuto documento ufficiale **"Calcolo compensi e maggiorazione notturna - FCO"**.
Effettuata verifica completa della corrispondenza tra regole e codice.

**Risultato: implementazione già conforme alle regole ufficiali** ✅

| Voce | Regola ufficiale | Codice | Verifica |
|------|-----------------|--------|----------|
| Forfait base | €56,00 / 2h30' | `base_eur=56.0, durata_base_h=2.5` | ✅ |
| Tariffa oraria forfait | €22,40/h (=56/2.5) | `val_orario_base = base / durata_base_h` | ✅ |
| Tariffa extra | €12,00/h | `extra_eur_per_h = 12.0` | ✅ |
| Magg. notturna | +20% | `notturno_perc = 0.20` | ✅ |
| Notte forfait | €22,40 × 20% = €4,48/h | `val_orario_base × (min/60) × 0.20` | ✅ |
| Notte extra | €12,00 × 20% = €2,40/h | `extra_eur_per_h × (min/60) × 0.20` | ✅ |
| Fascia SAND | 23:00-03:30 | `h==3 and curr.minute < 30` | ✅ |
| Fascia altri TO | 23:00-06:00 | `h==23 or (0<=h<6)` | ✅ |
| Festivo FCO | +20% + 29/6 incluso | `festivo_perc=0.20 + get_fco_holidays()` | ✅ |

### Esempio ufficiale verificato (test automatico)

```
Caso: 01/02/2026 — Baobab/TH — turno 03:10-06:33
  Forfait:          03:10 → 05:40  (2h30)
  Extra:            05:40 → 06:33  (53 min)
  Notturno forfait: 03:10 → 06:00  → 150 min nel forfait → €11,20
  Notturno extra:   05:40 → 06:00  → 20 min negli extra  → €0,80
  Extra (53 min):   53/60 × €12    → €10,60
  TOTALE:           56,00 + 10,60 + 12,00 = €78,60 ✅
```

### Modifiche effettate al codice

Solo aggiornamento commenti/documentazione interna — **nessuna modifica alla logica di calcolo**:

- Aggiunta docstring completa a `_calcola_noturno_extra_fco()` con riferimento alla Regola B
- Commenti allineati alla terminologia ufficiale (forfait/extra, €22.40/h, €4.48/h, €2.40/h)
- Aggiunto commento con esempio numerico nel blocco FCO Standard (riga ~1418)

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
