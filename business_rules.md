# Regole di Business — Sistema Calcolo Piano di Lavoro SCAY Group
# FONTE: Estratto direttamente dal blocco CalcConfig di ogni consuntivo*.py
# Moduli letti: consuntivoveratour.py, consuntivoalpitour.py, consuntivoaliservice.py,
#               consuntivobaobab.py, consuntivodomina.py, consuntivomicheltours.py,
#               consuntivosand.py, consuntivocaboverdetime.py, consuntivorusconi.py,
#               consuntivoiot.py, consuntivoflyness.py, consuntivordocanachi.py, tour_operators.py

---

## 1. STRUTTURA FILE EXCEL

### Foglio obbligatorio
Tutti i moduli cercano il foglio **"PIANO VOLI"** (strip + upper case). Se non trovato usano il primo foglio.

### Colonne rilevate con regex flessibili (non serve nome esatto)

| Campo interno | Pattern colonne accettate |
|---|---|
| DATA | `DATA`, `DATE` |
| TOUR OPERATOR | `TOUR OPERATOR`, `TO`, `OPERATORE` |
| AGENZIA | `AGENZIA`, `AGENCY` |
| APT | `APT`, `AEROPORTO`, `SCALO` |
| TURNO | `TURNO`, `TURNO ASSISTENTE`, `TURNI` |
| INIZIO TURNO | `INIZIO TURNO`, `INIZIO` |
| FINE TURNO | `FINE TURNO` |
| CONVOCAZIONE | `CONVOCAZIONE`, `CONV.NE`, `CONV`, `CVC` |
| STD | `STD`, `ORARIO STD` |
| ATD | `ATD`, `ORARIO ATD` |
| SERVIZIO | `SERVIZIO`, `SERVIZI` |
| ARRIVI/TRF | `ARRIVI/TRF`, `ARRIVI TRF` (solo Aliservice) |
| VOLO | `VOLO`, `NUMERO VOLO`, `N. VOLO`, `FLIGHT` |
| DEST.NE | `DEST.NE`, `DEST`, `DESTINAZIONE`, `DESTINATION` |
| ASSISTENTE | `ASSISTENTE` |
| NOTE | `NOTE`, `NOTA` |
| PARCHEGGIO | `PARCHEGGIO`, `PARK` (solo Domina, per NAP/BRI) |

---

## 2. CONDIZIONE CRITICA: QUANDO UN FOGLIO VIENE SCARTATO

Codice identico in **tutti** i moduli:
```python
has_orario = (cols["inizio_turno"] and cols["fine_turno"]) or cols["turno"]
if not cols["data"] or not cols["apt"] or not has_orario:
    continue  # foglio saltato silenziosamente
```

**Conclusione per validazione:**
- Colonna DATA assente → **ERRORE CRITICO** (foglio ignorato)
- Colonna APT assente → **ERRORE CRITICO** (foglio ignorato)
- Né TURNO né (INIZIO TURNO + FINE TURNO) presenti → **ERRORE CRITICO** (foglio ignorato)

---

## 3. PARAMETRI ESATTI DA CalcConfig (letti dal codice sorgente)

| TO | to_keyword | durata_base | rate_extra | festivo | notturno |
|---|---|---|---|---|---|
| Veratour | "veratour" | 3h (€75 base) | €18/h | +20% | 23:00-05:00 |
| Alpitour | "alpitour" | 3h | €20/h | +20% | 23:00-06:00 |
| Aliservice | "aliservice" | 3h | — | +20% | 23:00-03:30 |
| Baobab | "baobab" | 2h30 (150 min) | €18/h | **+30%** | 22:00-06:00 |
| Domina | "domina" | 2h30 (150 min) | €18/h | **+30%** | 22:00-06:00 |
| MichelTours | "micheltours" | **3h (180 min)** | €18/h | **+30%** | 22:00-06:00 |
| Sand | "sand" | 2h30 | €18/h | **+30%** | 22:00-03:59 |
| Caboverdetime | "caboverdetime" | **da CVC a STD** | €18/h | **+30%** | 22:00-06:00 |
| Rusconi | "rusconi" | 2h30 | **€20/h** | **+30%** | 22:00-06:00 |
| IOT | "iot" | 2h30 | €18/h | **+30%** | 22:00-06:00 |
| Flyness | "flyness" | 2h30 | **€20/h** | **+30%** | 22:00-06:00 |
| Rodocanachi | "rodocanachi" | 2h30 | €18/h | **+30%** | 22:00-06:00 |

---

## 4. FILTRO PER TOUR OPERATOR — DAL CODICE

| TO | Colonna filtro | Tipo match |
|---|---|---|
| Veratour | TOUR OPERATOR | contains (case-insensitive) |
| Alpitour | TOUR OPERATOR | contains (case-insensitive) |
| **Aliservice** | **AGENZIA** | **contains "aliservice"** |
| Baobab | TOUR OPERATOR | **match ESATTO** (==) |
| Domina | TOUR OPERATOR | contains "domina" |
| MichelTours | TOUR OPERATOR | contains "micheltours" |
| Sand | TOUR OPERATOR | contains "sand" |
| Caboverdetime | TOUR OPERATOR | contains "caboverdetime" |
| Rusconi | TOUR OPERATOR | contains "rusconi" |
| IOT | TOUR OPERATOR | contains "iot" |
| Flyness | TOUR OPERATOR | contains "flyness" |
| Rodocanachi | TOUR OPERATOR | contains "rodocanachi" |

**IMPORTANTE — Aliservice:** filtra su AGENZIA (non TOUR OPERATOR). I TO nella colonna TOUR OPERATOR delle righe Aliservice (es. BRIXIA, FUTURA, ATALANTA, FLYNESS, IOT, GATTINONI MICE) NON sono TO indipendenti — non segnalarli come problema.

---

## 5. GESTIONE ATD MANCANTE

| TO | ATD mancante → comportamento |
|---|---|
| Veratour | Usa STD come decollo garantito minimo |
| Alpitour | Usa STD come fallback |
| Aliservice | Usa STD come fine blocco |
| Baobab | Usa STD come fallback |
| Domina | Usa STD come fallback |
| MichelTours | Usa STD come fallback |
| **Sand** | **Fine turno = sempre STD (ATD ignorato per contratto)** |
| Caboverdetime | Extra = 0 se ATD assente (base rimane CVC→STD) |
| Rusconi | Extra = €0 se ATD ≤ STD (nessun ritardo) |
| IOT/Flyness/Rodocanachi | Usa STD come fallback |

**ATD vuoto non è mai un errore critico.** Segnalare come INFO se molte righe lo hanno vuoto.

---

## 6. TURNO — FORMATI SUPPORTATI

### Vecchio formato (ancora usato)
Colonna TURNO con stringhe: `08-11`, `8:00-11`, `8.00–11.30`, `NO DEC 08-11`, `SC1 08-11`
Il codice fa forward-fill per le righe vuote.

### Nuovo formato 2026
Colonne INIZIO TURNO + FINE TURNO separate.
Forward-fill per gruppo (DATA + TO + APT + ASSISTENTE).

### Righe singole con INIZIO/FINE TURNO vuoti → NORMALE
Il forward-fill riempie automaticamente. **Non segnalare come errore.**

### Aliservice M&G
Righe con ARRIVI/TRF = "M&G": usano CONVOCAZIONE come inizio, non forward-fill.
INIZIO/FINE TURNO vuoti → NORMALE per queste righe.

---

## 7. TARIFFE BASE PER AEROPORTO (da codice sorgente)

### Domina
```
BGY: €80, VRN/BLQ: €85, MXP/NAP/BRI/CTA/PMO/FCO: €90, VCE/PSI: €100
```
Parcheggio: NAP €1/ora, BRI €6 ogni 3h (arrotondato per eccesso)

### MichelTours
```
BGY: €85, MXP/VCE: €90
```

### Sand
```
BGY: €65, VRN/BLQ/NAP: €70, VCE: €75, FCO: €77
Extra: sempre €0 per contratto — fine turno = STD
Notturno: fascia 22:00-03:59 (da CONVOCAZIONE a STD)
```

### Rusconi
```
BGY: €110, FCO: €115, VCE: €140, altri: €100
Extra: €20/h solo se ATD > STD
```

### Rodocanachi (header dice "IOT Viaggi")
```
VCE/FCO/PSA: €100, altri: €90
Base: convocazione = STD-2h30, extra da STD
```

---

## 8. CONVOCAZIONE — QUANDO È CRITICA

| TO | Importanza CONVOCAZIONE |
|---|---|
| Aliservice | Usata per M&G come inizio turno |
| **Caboverdetime** | **Base = da CVC a STD — se manca non si può calcolare la base** |
| **Sand** | **Notturno da CVC a STD — se manca il notturno non viene calcolato** |
| Tutti gli altri | Opzionale |

---

## 9. COLONNE SEMPRE OPZIONALI

- **ASSISTENTE**: nessun modulo lo richiede per il calcolo
- **ATD**: sempre con fallback su STD
- **CONVOCAZIONE**: opzionale tranne Caboverdetime e Sand (vedi sopra)
- **AGENZIA**: vuota per tutti i TO non-Aliservice → NORMALE
- **VOLO, DEST.NE, NOTE**: opzionali in tutti i moduli
- **PARCHEGGIO**: solo Domina, calcolato automaticamente se assente
- **SERVIZIO/SERVIZI**: usato solo da Aliservice per M&G
- **IMPORTO, ORE EXTRA, NOTTURNO, FESTIVO**: colonne di verifica opzionali

---

## 10. DATE IN FORMATO TESTO — GESTITE DAL CODICE

`parse_excel_date()` in tutti i moduli usa `pd.to_datetime(x, dayfirst=True)` che gestisce
anche testo italiano tipo "venerdì 1 maggio 2026".
→ **Segnalare come AVVISO** (non errore critico), con suggerimento di usare formato data Excel.

---

## 11. TO SENZA MODULO — NON È ERRORE DEL FILE

Se un TO appare in TOUR OPERATOR ma non ha cartella/modulo → elaborazione saltata (non è colpa del file).
Segnalare come **INFO**, non come errore.

TO tipicamente senza modulo:
- ATALANTA, FLRCHARTER, PROMOBERG, SILVESTRO, TRUE BLUE ITALY, TRAVEL DESIGN STUDIO
- NEW BEETLE, ACENTRO GRUPPI, LEARN&TRAVEL, LAGUNA TRAVEL, JTI EVENTS, INTERSTUDIO
- BRIXIA, FUTURA (gestiti da Aliservice) — non segnalare

---

## 12. TABELLA GRAVITÀ SEGNALAZIONI

| Situazione | Gravità |
|---|---|
| Colonna DATA assente | 🔴 ERRORE CRITICO |
| Colonna APT assente | 🔴 ERRORE CRITICO |
| Né TURNO né INIZIO/FINE TURNO nel foglio | 🔴 ERRORE CRITICO |
| Date in formato testo italiano | 🟡 AVVISO |
| CONVOCAZIONE vuota per Caboverdetime o Sand | 🟡 AVVISO |
| ATD vuoto su molte righe (>50%) | ℹ️ INFO |
| ASSISTENTE vuoto | ℹ️ INFO (normale) |
| CONVOCAZIONE vuota per altri TO | ℹ️ INFO |
| TO nel file senza modulo | ℹ️ INFO |
| Righe singole con INIZIO/FINE TURNO vuoti | ✅ NON segnalare |
| AGENZIA vuota per righe non-Aliservice | ✅ NON segnalare |
| TO Aliservice (BRIXIA, FUTURA ecc.) in TOUR OPERATOR | ✅ NON segnalare |
