# Regole di Calcolo — Manuela Gregori (Accordo 2026)

> Fonte: `accordo 2026 Manuela Gregori.pdf` + testo accordo

## Dati Collaboratore

| Parametro | Valore |
|-----------|--------|
| **Nome** | Manuela Gregori |
| **Categoria** | Senior |
| **Regime** | Partita IVA |
| **Aeroporto** | MXP (Malpensa) |

## Tariffe

| Voce | Importo | Note |
|------|---------|------|
| **Assistenza base** | €60.00 | Per 3 ore |
| **Tariffa oraria base** | €20.00/h | = €60 / 3h |
| **Extra** | €12.00/h | Per ritardi oltre STD |
| **Notturno** | +20% | Fascia 23:00 – 06:00 |
| **Festivo** | +20% | Su tutto il totale |
| **INPS** | +4% | Maggiorazione finale |

## Regole di Calcolo

### 1. Conteggio delle 3 ore di assistenza

Il turno base si calcola così:

```
START = CONVOCAZIONE − 30 minuti
END_BASE = STD (orario schedulato)

Durata base = START → STD
```

- Il turno parte **mezz'ora prima della convocazione**
- Finisce all'orario **schedulato (STD)**
- I ritardi (ATD > STD) sono conteggiati come **ore extra**

### 2. Calcolo Extra (ritardi)

```
Ritardo = ATD − STD (solo se ATD > STD)
Extra (€) = Ritardo_ore × €12.00/h
```

Le frazioni orarie si calcolano proporzionalmente al minuto.

### 3. Maggiorazione Notturna

```
Fascia notturna: 23:00 – 06:00
Maggiorazione: +20% sulla tariffa oraria base

Notturno (€) = Ore_in_fascia × €20/h × 20%
             = Ore_in_fascia × €4/h
```

La maggiorazione viene applicata **solo alle ore** che ricadono nella fascia 23:00–06:00, indipendentemente dall'orario del decollo.

### 4. Maggiorazione Festiva

Nei giorni festivi (festività italiane), si applica una maggiorazione del **+20%** sul subtotale (base + extra + notturno).

### 5. INPS (+4%)

Come da accordo, al totale va aggiunta la **maggiorazione INPS del 4%**.

```
INPS (€) = Subtotale × 4%
```

### 6. Formula Completa

```
START    = CONVOCAZIONE − 30 min
Ritardo  = MAX(0, ATD − STD)
Notte    = minuti in fascia 23:00–06:00 tra START e ATD

BASE        = €60.00
EXTRA       = (Ritardo_min / 60) × €12.00
NOTTURNO    = (Notte_min / 60) × €20.00 × 20%
SUBTOTALE   = BASE + EXTRA + NOTTURNO
se FESTIVO:   SUBTOTALE × 1.20
INPS        = SUBTOTALE × 4%

TOTALE      = SUBTOTALE + INPS
```

## Esempio Completo

> Convocazione alle 03:30, STD 06:00, ATD 06:32

```
START   = 03:30 − 30min = 03:00
Ritardo = 06:32 − 06:00 = 32 min
Notte   = 03:00 → 06:00 = 180 min (tutto in fascia 23-06)

BASE      = €60.00
EXTRA     = 32/60 × €12 = €6.40
NOTTURNO  = (180/60) × €20 × 20% = 3h × €4 = €12.00
SUBTOTALE = €78.40
INPS +4%  = €3.14
TOTALE    = €81.54
```
