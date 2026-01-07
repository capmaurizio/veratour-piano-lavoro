# Report Incongruenze - Piano Lavoro Alpitour Ottobre 2025

## Analisi effettuata il: 2025

### Riepilogo Generale

- **Righe totali Alpitour**: 44
- **Righe con tutti i dati completi**: 33 (75%)
- **Righe con problemi minori**: 11 (25%)

---

## 1. TURNO MANCANTE (7 righe)

Queste righe hanno il campo TURNO vuoto o mancante. Il codice gestisce automaticamente questa situazione usando il **forward-fill**: il TURNO viene preso dalla riga precedente con la stessa DATA.

### Dettaglio righe:

| Data | APT | ATD | STD |
|------|-----|-----|-----|
| 2025-10-04 | VRN | 20:09 | 19:30 |
| 2025-10-05 | BGY | 17:01 | 16:05 |
| 2025-10-12 | BGY | 17:20 | 16:05 |
| 2025-10-19 | BGY | 18:47 | 16:05 |
| 2025-10-26 | BGY | 16:12 | 15:05 |
| 2025-10-26 | VRN | 17:22 | 17:30 |
| 2025-10-27 | VRN | 07:56 | 07:30 |

**Impatto**: ✅ Gestito automaticamente dal codice (forward-fill per DATA)

---

## 2. ATD MANCANTE (4 righe)

Queste righe non hanno l'ATD (orario decollo effettivo). Il codice usa automaticamente **STD** (orario decollo programmato) come fallback per il calcolo delle ore extra.

### Dettaglio righe:

| Data | APT | TURNO | STD |
|------|-----|-------|-----|
| 2025-10-15 | VRN | SC1 8:00 - 11:30 | 11:05 |
| 2025-10-29 | VRN | SC1 07:30 - 11:00 | 10:30 |
| 2025-10-30 | VRN | SC1:15:30-19:00 | 18:30 |
| 2025-10-31 | VRN | SC1 05:15 - 09:15 | 09:00 |

**Impatto**: ✅ Gestito automaticamente dal codice (STD come fallback)

---

## 3. Verifica TURNO non parsabili

✅ **Tutti i TURNO presenti sono parsabili correttamente**

Il codice riconosce automaticamente vari formati:
- `SC1 7:10-11:10`
- `SC2: 11-16:30`
- `11.00-16:30`
- `SC1:16-19:30`
- `3-6:30`
- `23:30-02:30`

---

## 4. Altri controlli

✅ **Colonne necessarie**: Tutte presenti
✅ **Date valide**: Tutte le date sono di ottobre 2025
✅ **APT validi**: Solo BGY e VRN (come previsto dall'accordo)
✅ **STD presente**: Tutte le righe hanno STD (100%)

---

## Conclusioni

### Problemi trovati:
1. **7 righe con TURNO mancante** → Gestito con forward-fill automatico
2. **4 righe con ATD mancante** → Gestito con STD come fallback

### Nessun problema critico:
- ✅ Nessuna riga senza ATD e STD entrambi mancanti
- ✅ Nessuna data non valida
- ✅ Nessun APT non previsto
- ✅ Tutti i TURNO sono parsabili

### Raccomandazioni:
- Le righe con TURNO mancante potrebbero essere completate manualmente per maggiore chiarezza
- Le righe con ATD mancante potrebbero essere aggiornate quando disponibile l'orario effettivo
- Nessuna azione urgente richiesta: il codice gestisce tutti i casi automaticamente

---

## Note tecniche

Il codice `consuntivoalpitour.py` gestisce automaticamente:
- **Forward-fill TURNO**: Se una riga non ha TURNO, viene preso dalla riga precedente con stessa DATA
- **STD fallback**: Se ATD non è disponibile, viene usato STD per il calcolo extra
- **Raggruppamento blocchi**: Righe con stessa DATA + APT + TURNO vengono raggruppate in un unico blocco

Tutti i calcoli risultano corretti anche in presenza di questi dati mancanti.


