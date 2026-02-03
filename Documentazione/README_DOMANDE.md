# Domande e Risposte - Calcolo Veratour 2025

Questo documento contiene tutte le domande relative al calcolo dei consuntivi Veratour e le relative risposte. Serve come traccia storica per capire le decisioni prese.

**Data creazione**: 2025-01-XX  
**Ultimo aggiornamento**: 2025-01-XX

---

## 📊 Situazione Attuale

### Valori Attesi vs Calcolati (Novembre 2025 - VRN)

| Voce | Atteso | Calcolato | Differenza | Stato |
|------|--------|-----------|------------|-------|
| **Assistenze/Turni** | **3,529.50 €** | **3,327.00 €** | **-202.50 €** | ❌ Da correggere |
| Extra (5 ore) | 90.00 € | 92.40 € | -2.40 € | ⚠️ Piccola differenza |
| Notturno (24.20h) | 123.66 € | 124.11 € | -0.45 € | ✅ Quasi corretto |
| **TOTALE** | **3,743.16 €** | **3,545.72 €** | **-197.44 €** | ❌ Da correggere |

---

## ❓ DOMANDE DA CHIARIRE

### 1. MAGGIORAZIONE NOTTURNA DEL 20% - Come applicarla?

**Contesto**:  
Dalla Proposta Veratour: *"Le convocazioni previste dalle 23:00 alle 05:00 del mattino saranno riconosciute con una maggiorazione oraria del 20%."*

**Domanda**: Come deve essere applicata questa maggiorazione del 20%?

**Opzioni possibili:**

#### Opzione A (Implementazione attuale):
- Turno calcolato normalmente (€75 base + €15/ora oltre 3h)
- Notturno come voce separata calcolata come maggiorazione differenziale (5.10€/ora)
- Totale = Turno + Extra + Notturno

#### Opzione B (Ipotetica):
- Turno calcolato normalmente
- Maggiorazione 20% applicata **direttamente al turno** per le ore notturne
- Il notturno potrebbe essere incluso nell'importo turno stesso
- Totale = Turno (con magg. notturna) + Extra + Notturno (solo extra?)

#### Opzione C (Alternativa):
- Turno base senza maggiorazioni
- Maggiorazione notturna 20% sulle ore notturne del turno come aggiunta
- Maggiorazione festiva 20% su tutto (turno + extra + notturno) se festivo
- Totale = (Turno + Magg.Notturna + Extra + Notturno) × 1.20 se festivo

**✅ RISPOSTA**:  
**OPZIONE A** - Usa questo:
- Turno calcolato normalmente
- Notturno come voce separata (5.10€/ora)
- Totale = Turno + Extra + Notturno

**📝 NOTE**:  
La maggiorazione notturna è una voce separata, NON inclusa nel calcolo del turno. L'implementazione attuale è corretta per questo punto.

---

### 2. FESTIVI - Il notturno ha +20% nei festivi?

**Contesto**:  
Dalla Proposta Veratour: *"Durante le festività... la tariffa dell'assistenza e delle ore extra sarà maggiorata del 20%"*

**Domanda**: Il notturno ha anche +20% nei giorni festivi, o solo turno ed extra?

**Opzioni:**

#### Opzione A:
- ✅ Turno: +20% nei festivi
- ✅ Extra: +20% nei festivi  
- ❌ Notturno: NO maggiorazione nei festivi (solo tariffa base notturna)

#### Opzione B:
- ✅ Turno: +20% nei festivi
- ✅ Extra: +20% nei festivi
- ✅ Notturno: +20% anche nei festivi (notturno_festivo = notturno × 1.20)

**✅ RISPOSTA**:  
**SÌ, anche il notturno va maggiorato con il festivo**
- Opzione B: Turno, Extra E Notturno hanno tutti +20% nei festivi

**📝 NOTE**:  
**DA CORREGGERE**: Attualmente il codice applica il moltiplicatore 1.20 solo al subtotale (turno + extra + notturno), quindi in teoria già include il notturno. Ma devo verificare che sia corretto. Se il notturno nei festivi dovesse essere calcolato separatamente come notturno * 1.20, potrebbe cambiare qualcosa.

---

### 3. PRECISIONE ORE EXTRA - Serve arrotondamento?

**Situazione attuale:**
- **Attese**: 5.00 ore = 300 minuti
- **Calcolate**: 5.13 ore = 308 minuti  
- **Differenza**: 8 minuti = 2.40€

**Domande:**
1. Le ore extra devono essere arrotondate?
2. Se sì, come? (per difetto, per eccesso, al multiplo di 5 minuti più vicino?)
3. La differenza di 8 minuti è accettabile o deve essere corretta?

**✅ RISPOSTA**:  
**NO arrotondamento necessario**

**📝 NOTE**:  
Il calcolo attuale è preciso al minuto basato sull'ATD. La piccola differenza di 8 minuti (2.40€) è accettabile e potrebbe essere dovuta a:
- Metodo di calcolo leggermente diverso nel file originale
- Errori nei dati originali
- Precisione nel calcolo dell'ATD

---

### 4. PRECISIONE ORE NOTTURNE - Serve arrotondamento?

**Situazione attuale:**
- **Attese**: 24.20 ore = 1452 minuti
- **Calcolate**: 24.33 ore = 1460 minuti
- **Differenza**: 8 minuti = 0.45€

**Domande:**
1. Le ore notturne devono essere arrotondate?
2. Se sì, come? (per difetto, per eccesso, al multiplo di 5 minuti più vicino?)
3. La differenza di 8 minuti è accettabile o deve essere corretta?

**✅ RISPOSTA**:  
**NO arrotondamento necessario**

**📝 NOTE**:  
La differenza è minima (0.45€, 8 minuti) ed è accettabile. Potrebbe essere dovuta a:
- Metodo di calcolo leggermente diverso
- Precisione nel calcolo delle fasce orarie notturne (23:00-05:00)
- Piccole differenze nell'interpretazione degli orari

---

### 5. COMPOSIZIONE "ASSISTENZE 3,529.50 €"

**Contesto**:  
L'utente ha indicato che per novembre VRN ci dovrebbero essere:
- **3,529.50 €** per "assistenze senza straordinario"
- 90 € per 5 ore extra
- 123.66 € per 24.20 ore notturno

**Domanda**: Cosa include esattamente la voce "assistenze 3,529.50 €"?

**Opzioni possibili:**

#### Opzione A:
- Solo turni base (senza maggiorazioni)
- Esclusi: festivi, notturno, extra
- Calcolo attuale turni base: **3,292.50 €** ❌ (mancano 237€)

#### Opzione B:
- Turni base + maggiorazione festiva (+20%)
- Esclusi: notturno, extra
- Calcolo attuale: **3,327.00 €** ❌ (mancano 202.50€)

#### Opzione C:
- Turni base + maggiorazione festiva + maggiorazione notturna sul turno
- Esclusi: extra, notturno come voce separata
- Calcolo ipotetico: ~**3,435.63 €** ❌ (mancano ancora ~94€)

#### Opzione D:
- Qualcosa d'altro?

**✅ RISPOSTA**:  
**OPZIONE B: Turni + maggiorazione festiva**
- "Assistenze" = Solo turni base + maggiorazione festiva (+20% sui turni festivi)
- NON include: notturno, extra
- Calcolo atteso: Turni non festivi + (Turni festivi × 1.20)

**📝 NOTE**:  
**PROBLEMA DA RISOLVERE**: 
- Calcolo attuale: 3,327.00€ (turni con +20% festivi) ✅ Corretto
- Valore atteso: 3,529.50€ ❌ Mancano 202.50€

**POSSIBILI CAUSE**:
1. Alcuni blocchi non vengono contati come festivi quando dovrebbero
2. Metodo di calcolo turni diverso per alcuni blocchi
3. Altri costi inclusi in "assistenze" che non sto considerando
4. Errori nei dati di riferimento

---

### 6. LOGICA NO DEC

**Contesto**:  
Quando nel TURNO è presente "NO DEC", le ore extra devono essere = 0.

**Domanda**: 
1. Il notturno calcolato sulle ore extra deve essere escluso se NO DEC?
2. Il notturno calcolato sul turno resta sempre, anche con NO DEC?
3. Ci sono altri effetti di NO DEC sul calcolo?

**❓ RISPOSTA**:  
_[Attendo risposta]_

**📝 NOTE**:  
Attualmente: se NO DEC → extra = 0, ma il notturno dentro il turno resta calcolato.

---

### 7. ALTRE REGOLE O ECCEZIONI

**Domanda**: Ci sono altre regole, eccezioni o casi particolari da considerare nel calcolo che non sono state ancora menzionate?

**Esempi potenziali:**
- Tariffe diverse per certi giorni
- Regole speciali per certi aeroporti
- Modifiche a certe tariffe in base a condizioni particolari
- Altro?

**❓ RISPOSTA**:  
_[Attendo risposta]_

---

## 📝 STORIA DELLE MODIFICHE

### 2025-01-XX - Creazione documento
- Rilevate discrepanze nel calcolo novembre VRN
- Identificate 7 domande chiave da chiarire
- Implementazione attuale: festivi automatici, notturno 5.10€/ora

### 2025-01-XX - Risposte ricevute
1. ✅ Maggiorazione notturna: OPZIONE A (notturno separato) - già corretta
2. ✅ Festivi: SÌ, anche notturno ha +20% - **VERIFICATO: già corretto nel codice**
3. ✅ Arrotondamento extra: NO
4. ✅ Arrotondamento notturno: NO
5. ⚠️ Assistenze: Turni + festivi, ma mancano ancora 202.50€ da spiegare

**Stato attuale:**
- ✅ Notturno nei festivi: corretto (tutto moltiplicato per 1.20)
- ❌ Assistenze: calcolo 3,327.00€ vs atteso 3,529.50€ (-202.50€)

### Modifiche già applicate:
1. ✅ Riconoscimento automatico festivi italiani 2025 (incluso Pasqua/Pasquetta)
2. ✅ Tariffa notturna corretta: 5.10€/ora (0.085€/min) invece di 5.00€/ora
3. ✅ Festivi applicati automaticamente senza bisogno di lista esterna

### Modifiche in attesa di risposte:
- [ ] Definire metodo corretto per maggiorazione notturna
- [ ] Chiarire se notturno ha +20% nei festivi
- [ ] Eventuali arrotondamenti per extra e notturno
- [ ] Chiarire composizione "assistenze"
- [ ] Verificare logica NO DEC
- [ ] Altre regole/eccezioni

---

## 📋 CHECKLIST IMPLEMENTAZIONE

- [x] Festivi italiani 2025 riconosciuti automaticamente
- [x] Tariffa notturna corretta (5.10€/ora)
- [ ] Metodo corretto per maggiorazione notturna 20%
- [ ] Gestione notturno nei festivi
- [ ] Arrotondamenti extra (se necessari)
- [ ] Arrotondamenti notturno (se necessari)
- [ ] Composizione "assistenze" corretta
- [ ] Verifica logica NO DEC
- [ ] Altre regole/eccezioni

---

## 🔍 REFERENCE

### Documenti consultati:
1. `Proposta Veratour - Scay_2025.docx` - Tariffe e condizioni
2. `ISTRUZIONI CHAT veratour 16-11 .docx` - Metodologie di calcolo dettagliate
3. `Riepilogo Veratour novembre 25.xlsx` - File Excel originale con valori

### File codice:
- `consuntivoveratour.py` - Script Python principale

---

**IMPORTANTE**: Questo documento viene aggiornato man mano che arrivano le risposte. Mantenere una traccia storica aiuta a:
- Evitare contraddizioni
- Capire l'evoluzione delle decisioni
- Identificare eventuali errori nelle risposte
- Avere un riferimento per il futuro

