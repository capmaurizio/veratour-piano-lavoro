# Regole Turni Multi-TO — Scay

> Documento di riferimento operativo per la compilazione del Piano Lavoro e il calcolo compensi collaboratori.
> Fonte: comunicazione interna Silvia (silvia@scay.eu) — 11 maggio 2026.

---

## 1. Regola identificazione risorse e gestione voli multipli

### Veratour – Alta stagione

In alta stagione, nella stessa giornata possono essere impiegate **più risorse operative** sullo stesso aeroporto.  
Ogni risorsa può gestire, all'interno dello stesso turno, **più voli Veratour**.

In questi casi, il turno viene identificato con una **sigla composta da due lettere**:

- **1ª lettera** = risorsa (A, B, C, D, ...)
- **2ª lettera** = aeroporto (B=Bergamo, V=Verona, N=Napoli)

| Sigla | Significato |
|---|---|
| AB | 1ª risorsa su Bergamo |
| BB | 2ª risorsa su Bergamo |
| CB | 3ª risorsa su Bergamo |
| AV | 1ª risorsa su Verona |
| BV | 2ª risorsa su Verona |
| AN | 1ª risorsa su Napoli |
| BN | 2ª risorsa su Napoli |

> **Caso singolo:** se nella giornata è presente **un solo volo, un solo turno e una sola risorsa**, la numerazione della risorsa **non viene applicata** (campo TIPO TURNO lasciato vuoto).

---

### Alpitour – Identificazione turni

Alpitour opera solo su **Bergamo** e **Verona**.

In presenza di più turni nella stessa giornata, la numerazione è progressiva con sigla:

| Sigla | Significato |
|---|---|
| SC1 | 1° turno/risorsa Scay |
| SC2 | 2° turno/risorsa Scay |
| SC3 | 3° turno/risorsa Scay |

> SC = Scay, numero = turno progressivo. Stessa logica sia per Bergamo che per Verona.

---

## 2. Gestione multi Tour Operator nello stesso turno (solo Bergamo, alta stagione)

In alta stagione a Bergamo, una stessa risorsa assegnata a un TO principale (es. Veratour) può gestire contemporaneamente voli di **altri Tour Operator**.

### Regola lato fatturazione clienti

La fatturazione è **separata per competenza**:
- Ogni TO riceve l'addebito relativo ai **propri** voli/servizi
- La presenza di attività condivise nello stesso turno **non modifica** la rendicontazione commerciale

### Regola lato compenso collaboratore

Il compenso è **unico e invariato**:
- Calcolato esclusivamente sul **turno effettivamente svolto**
- Le ore non vengono suddivise per TO
- Nessuna duplicazione economica, nessun conteggio separato

> **Principio:** una singola risorsa operativa = **un unico calcolo economico del turno**, indipendentemente dal numero di Tour Operator o voli gestiti contemporaneamente.

Le ore extra sono sempre calcolate sull'**ATD più alto** tra tutti i voli del blocco operativo (ATD successivo alla fine turno).

---

## 3. Come compilare il file Excel — esempi pratici

### Caso A — Volo singolo, risorsa singola, un solo TO
Nessun TIPO TURNO.

| TO | TIPO TURNO | INIZIO | FINE | VOLO |
|---|---|---|---|---|
| FUTURA | *(vuoto)* | 11:10 | 14:10 | SM832 |

---

### Caso B — Più voli, stessa risorsa, stesso TO
Stesso TIPO TURNO su riga principale. Righe satellite senza INIZIO/FINE TURNO.

| TO | TIPO TURNO | INIZIO | FINE | VOLO |
|---|---|---|---|---|
| VERATOUR | AV | 03:30 | 11:00 | NO4357 |
| VERATOUR | AV | *(vuoto)* | *(vuoto)* | NO4723 |

→ **1 sola paga** per la risorsa AV.

---

### Caso C — Più voli, stessa risorsa, TO diversi (caso Bergamo alta stagione)
Stesso TIPO TURNO su tutte le righe della sessione, anche quelle di TO diversi.

| TO | TIPO TURNO | INIZIO | FINE | VOLO |
|---|---|---|---|---|
| VERATOUR | AB | 04:30 | 12:00 | NO6952 |
| RUSCONI | AB | *(vuoto)* | *(vuoto)* | FR5108 |
| VERATOUR | AB | *(vuoto)* | *(vuoto)* | PC1212 |

→ Fatturazione separata Veratour + Rusconi. **1 sola paga** per la risorsa AB.

---

### Caso D — Due risorse diverse, stesso TO, stessa giornata

| TO | TIPO TURNO | ASSISTENTE | INIZIO | FINE | VOLO |
|---|---|---|---|---|---|
| VERATOUR | AB | Ludovica | 04:30 | 12:00 | NO6952 |
| VERATOUR | BB | Filippo | 05:00 | 09:00 | NO6953 |

→ **2 paghe distinte** (AB ≠ BB = risorse diverse).

---

### Caso E — Due turni separati nel tempo, stesso assistente

| TO | TIPO TURNO | INIZIO | FINE | VOLO |
|---|---|---|---|---|
| ALPITOUR | SC1 | 04:00 | 08:00 | NO6952 |
| VERATOUR | AB | 15:30 | 20:30 | NO6954 |

→ **2 paghe distinte** (SC1 ≠ AB, turni non sovrapposti).

---

## 4. Chiave di raggruppamento per il calcolo paga collaboratore

La sessione collaboratore è identificata da:

```
(DATA, APT, TIPO TURNO)
```

- Stessa chiave → **1 paga**, ATD = max tra tutti i voli del gruppo
- Chiave diversa → **paghe separate**
- TIPO TURNO vuoto → caso singolo, nessun rischio di duplicazione

---

## 5. Gap attuale del sistema

Il sistema attualmente raggruppa i blocchi **dentro ogni modulo TO** correttamente.  
La deduplicazione **cross-modulo** (es. Veratour + Rusconi con stesso TIPO TURNO) è **da implementare** in `create_collaboratori_sheet`.

Con i dati attuali di aprile 2026: **0 casi di doppio conteggio** (le righe satellite multi-TO non hanno ancora INIZIO/FINE TURNO).  
Il problema si presenterà quando le righe satellite di TO diversi verranno completate con orari.
