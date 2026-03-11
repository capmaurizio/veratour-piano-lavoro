# 🛠️ Changelog Fix e Modifiche al Sistema

Questo file documenta le correzioni e le modifiche significative apportate al sistema di calcolo.

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
