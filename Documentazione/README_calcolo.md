# 📋 Documentazione Completa - Metodo di Calcolo Veratour 2025

**Programma**: `consuntivoveratour.py`  
**Data creazione**: 2025  
**Ultimo aggiornamento**: 2025

---

## 📊 Panoramica

Il programma calcola i consuntivi per Veratour 2025 elaborando file Excel contenenti i dati dei turni, estraendo blocchi unici e calcolando:
- **Assistenze (Turni)**: Tariffa base + eventuali ore oltre le 3h
- **Extra**: Ore lavorate oltre la fine del turno
- **Notturno**: Maggiorazione per ore lavorate tra 23:00 e 05:00
- **Festivi**: Maggiorazione del 20% sui giorni festivi

---

## 🎯 Definizione di Blocco

Un **blocco** è definito dalla combinazione unica di:
- **DATA**: Data del turno
- **APT**: Aeroporto (es: VRN, BGY, NAP, VCE)
- **TURNO_NORMALIZZATO**: Turno normalizzato (es: "AV 03:00-07:00 DEC")

### Forward-Fill TURNO

Il campo TURNO viene propagato in avanti (forward-fill) per tutte le righe della stessa DATA:
- L'ordine di elaborazione è: **file → foglio → righe**
- Se una riga non ha TURNO, viene ereditato dalla riga precedente della stessa DATA
- Ogni blocco aggregherà tutti gli ATD delle righe che appartengono allo stesso blocco

---

## 💰 Calcolo Assistenze (Turni)

### Formula Base

```
Turno (€) = 75€ + max(0, durata_h - 3) × 15€/h
```

Dove:
- **75€**: Tariffa base per le prime 3 ore
- **15€/h**: Tariffa oraria per ogni ora oltre le 3 ore iniziali
- **durata_h**: Durata del turno in ore (calcolata al minuto)

### Esempi

| Turno | Durata | Calcolo | Importo |
|-------|--------|---------|---------|
| 03:00-07:00 | 4h 0min | 75 + (4-3) × 15 = 75 + 15 | **90.00€** |
| 10:30-13:30 | 3h 0min | 75 + (3-3) × 15 = 75 + 0 | **75.00€** |
| 13:30-16:30 | 3h 0min | 75 + (3-3) × 15 = 75 + 0 | **75.00€** |
| 13:30-17:00 | 3h 30min | 75 + (3.5-3) × 15 = 75 + 7.5 | **82.50€** |
| 10:20-17:20 | 7h 0min | 75 + (7-3) × 15 = 75 + 60 | **135.00€** |

**Nota**: Il calcolo è pro-rata al minuto. Per esempio, un turno di 3h 30min (3.5h) = 75 + 0.5 × 15 = 82.50€

---

## ⏱️ Calcolo Extra

### Regole

1. **Selezione ATD**:
   - Vengono considerati solo gli ATD **strettamente maggiori** della fine del turno
   - Viene selezionato l'**ATD massimo** tra quelli validi
   - Se l'ATD è minore dell'inizio turno, viene considerato come appartenente al giorno successivo (+1 giorno)

2. **Calcolo minuti extra**:
   ```
   extra_min = (ATD_max - fine_turno) in minuti
   ```

3. **NO DEC**:
   - Se nel TURNO è presente "NO DEC", gli extra sono sempre **0**
   - Questo vale anche se ci sono ATD dopo la fine del turno

4. **Calcolo importo extra**:
   ```
   Extra (€) = (extra_min / 60) × 18€/h
   ```
   - **18€/h**: Tariffa oraria per le ore extra

### Esempi

| Turno | Fine Turno | ATD Max | Extra Min | Calcolo | Importo |
|-------|------------|---------|-----------|---------|---------|
| 13:30-17:00 DEC | 17:00 | 17:03 | 3 min | (3/60) × 18 | **0.90€** |
| 13:30-17:00 DEC | 17:00 | 17:42 | 42 min | (42/60) × 18 | **12.60€** |
| 03:00-07:00 NO DEC | 07:00 | 07:30 | 0 min | NO DEC → 0 | **0.00€** |

---

## 🌙 Calcolo Notturno

### Finestra Notturna

La finestra notturna è definita come: **23:00 - 05:00**

### Calcolo Minuti Notturni

I minuti notturni vengono calcolati:
1. **Sul turno**: Minuti del turno che cadono nella finestra 23:00-05:00
2. **Sugli extra** (se presenti e non NO DEC): Minuti degli extra che cadono nella finestra 23:00-05:00

### Formula

```
Notturno (€) = notte_min × 0.083333€/min
```

Dove:
- **0.083333€/min** = **5€/h** = maggiorazione differenziale
- La maggiorazione è calcolata come: **25€/h (base) × 20% = 5€/h**

### Esempi

| Turno | Minuti Notturni | Calcolo | Importo |
|-------|-----------------|---------|---------|
| 03:00-07:00 | 120 min (03:00-05:00) | 120 × 0.083333 | **10.00€** |
| 23:30-02:00 | 150 min (tutto il turno) | 150 × 0.083333 | **12.50€** |
| 13:30-17:00 | 0 min | 0 × 0.083333 | **0.00€** |

**Nota**: Se un turno inizia alle 23:00 e finisce alle 02:00 del giorno successivo, i minuti notturni sono calcolati su tutta la durata del turno.

---

## 🎉 Calcolo Festivi

### Festivi Italiani 2025

I festivi vengono riconosciuti **automaticamente** dal programma. Se non viene specificato il parametro `--holiday-list`, il programma utilizza automaticamente la lista dei festivi italiani 2025 che include:

| Data | Festività |
|------|-----------|
| 1 Gennaio | Capodanno |
| 6 Gennaio | Epifania |
| Pasqua 2025 | Pasqua (calcolata dinamicamente) |
| Pasqua + 1 | Pasquetta |
| 25 Aprile | Festa della Liberazione |
| 1 Maggio | Festa del Lavoro |
| 2 Giugno | Festa della Repubblica |
| 15 Agosto | Ferragosto |
| 1 Novembre | Ognissanti |
| 8 Dicembre | Immacolata Concezione |
| 25 Dicembre | Natale |
| 26 Dicembre | Santo Stefano |

### Formula

Se il giorno è festivo:
```
Totale (€) = (Turno + Extra + Notturno) × 1.20
```

**Maggiorazione**: +20% su tutto (turno + extra + notturno)

### Esempi

| Turno | Extra | Notturno | Festivo | Calcolo | Importo |
|-------|-------|----------|---------|---------|---------|
| 75€ | 0€ | 10€ | Sì | (75+0+10) × 1.20 | **102.00€** |
| 90€ | 5€ | 7.50€ | Sì | (90+5+7.50) × 1.20 | **123.00€** |
| 75€ | 0€ | 0€ | No | 75+0+0 | **75.00€** |

---

## 📝 Parsing TURNO

### Formati Supportati

Il parser riconosce vari formati di orari:

| Formato Input | Formato Normalizzato | Esempio |
|---------------|----------------------|---------|
| `08:00-11:00` | `08:00-11:00` | Standard |
| `8:00-11:00` | `08:00-11:00` | Ora senza zero |
| `08-11` | `08:00-11:00` | Senza minuti |
| `8.00-11.30` | `08:00-11:30` | Punto invece di due punti |
| `13:30.17:00` | `13:30-17:00` | Punto come separatore tra orari |
| `08:00–11:00` | `08:00-11:00` | Trattino lungo (en-dash) |
| `08:00—11:00` | `08:00-11:00` | Trattino molto lungo (em-dash) |

### Prefissi

Il parser mantiene i prefissi del turno (A, B, AV, BV, ecc.) per il raggruppamento:
- `AV 03:00-07:00 DEC` → Prefisso: "AV"
- `BV 13:30-17:00 DEC` → Prefisso: "BV"

### NO DEC

Se nel TURNO compare "NO DEC" (case-insensitive), viene impostato il flag `no_dec = True`, che azzera gli extra.

### Turni Overnight

Se la fine del turno è minore dell'inizio (es: 23:00-02:00), viene automaticamente aggiunto 1 giorno alla fine:
- `23:00-02:00` → Fine: giorno successivo alle 02:00

---

## 🔢 Esempio Completo di Calcolo

### Blocco: VRN, 01/11/2025, "AV 03:00-07:00 DEC"

**Dati**:
- Turno: 03:00-07:00 (4h 0min)
- ATD max: 07:05
- Festivo: Sì (1 Novembre = Ognissanti)

**Calcoli**:

1. **Turno**:
   - Durata: 4h = 240 minuti
   - Importo: 75 + (4-3) × 15 = **90.00€**

2. **Extra**:
   - Fine turno: 07:00
   - ATD max: 07:05
   - Extra minuti: 5 minuti
   - Importo: (5/60) × 18 = **1.50€**

3. **Notturno**:
   - Minuti notturni nel turno: 03:00-05:00 = 120 minuti
   - Minuti notturni negli extra: 0 (extra 07:00-07:05 non è notturno)
   - Totale minuti notturni: 120
   - Importo: 120 × 0.083333 = **10.00€**

4. **Festivo**:
   - Subtotale: 90.00 + 1.50 + 10.00 = 101.50€
   - Maggiorazione festiva: 101.50 × 1.20 = **121.80€**

**TOTALE BLOCCO**: **121.80€**

---

## 📊 Totali per Voce

### Assistenze Totali

Le "Assistenze" sono calcolate come:
```
Assistenze = Σ(Turno base) + Σ(Turno base festivi × 0.20)
```

Non includono extra e notturno, solo i turni base (con maggiorazione festiva se presente).

### Extra Totali

```
Extra Totali = Σ(Extra minuti / 60 × 18€/h)
```

### Notturno Totali

```
Notturno Totali = Σ(Minuti notturni × 0.083333€/min)
```

**Nota**: Il notturno include anche la maggiorazione festiva se applicata (calcolata insieme a turno ed extra).

---

## 🛠️ Configurazione Tariffe

Le tariffe sono configurate nel codice con i seguenti valori:

| Voce | Valore | Note |
|------|--------|------|
| **Base 3h** | 75.00€ | Tariffa base per i primi 3h |
| **Tariffa oltre 3h** | 15.00€/h | Pro-rata al minuto |
| **Tariffa Extra** | 18.00€/h | Per ore lavorate oltre il turno |
| **Maggiorazione Notturna** | 5.00€/h = 0.083333€/min | Differenziale (25€/h × 20%) |
| **Maggiorazione Festiva** | +20% | Su tutto (turno + extra + notturno) |

---

## 📤 Output del Programma

Il programma genera un file Excel con 3 fogli:

### 1. DettaglioBlocchi

Contiene ogni blocco con:
- DATA, APT, VOLO, DEST.NE, TURNO_NORMALIZZATO
- DURATA_TURNO_MIN, TURNO_EUR
- EXTRA_MIN, EXTRA_EUR
- NOTTE_MIN, NOTTE_EUR
- FESTIVO, TOTALE_BLOCCO_EUR

### 2. TotaliPeriodo

Contiene i totali aggregati:
- Per periodo (1-15, 16-31, Mese)
- Turno, Extra, Notturno, Totale

### 3. Discrepanze

Confronta i valori calcolati con quelli presenti nel file originale (se disponibili):
- Delta per Extra, Notturno, Totale
- Aiuta a identificare discrepanze

---

## ✅ Verifica Calcoli - Esempio Reale

### Novembre 2025 - VRN (Verona)

| Voce | Valore Calcolato | Note |
|------|------------------|------|
| **Assistenze** | **3,529.50€** | Turni base + maggiorazione festiva (1 Novembre) |
| **Extra** | **94.80€** | 316 minuti = 5.27h × 18€/h |
| **Notturno** | **121.67€** | 1,460 minuti = 24.33h × 5€/h |
| **TOTALE** | **3,748.15€** | Include tutto con maggiorazione festiva |

**Giorno festivo**: 01/11/2025 (Ognissanti)

---

## 🔍 Note Importanti

1. **Arrotondamenti**: Di default non vengono applicati arrotondamenti. I calcoli sono precisi al centesimo.

2. **Forward-Fill**: Il TURNO viene propagato solo per la stessa DATA, non tra date diverse.

3. **Aggregazione ATD**: Se più righe appartengono allo stesso blocco, vengono aggregati tutti gli ATD e viene preso il massimo per il calcolo extra.

4. **Turni Overnight**: Il parser gestisce automaticamente i turni che attraversano la mezzanotte.

5. **NO DEC**: Se presente nel TURNO, gli extra sono sempre 0, anche se ci sono ATD dopo la fine del turno.

6. **Festivi**: La maggiorazione festiva viene applicata automaticamente se il giorno è nella lista dei festivi italiani 2025 (se non viene specificato `--holiday-list`), oppure se è presente nella colonna "festivo" del file, oppure se viene fornita una lista personalizzata con `--holiday-list`.

---

## 📚 Riferimenti

- File principale: `consuntivoveratour.py`
- Documento domande: `README_DOMANDE.md`
- Proposta tariffaria: `Proposta Veratour - Scay_2025.docx`
- Istruzioni dettagliate: `ISTRUZIONI CHAT veratour 16-11 .docx`

---

**Ultimo aggiornamento**: 2025  
**Versione calcolo**: Basata su calcoli reali di Novembre 2025

