# Baobab - Calcolatore Blocchi

Programma per il calcolo dei blocchi di assistenza aeroportuale per il tour operator Baobab.

## Struttura

Il programma `consuntivobaobab.py` legge il file "Piano Lavoro" e calcola:
- Turno base
- Ore extra
- Notturno
- Festivi (se applicabile)

## Stato attuale

**Struttura base implementata** - Il programma è pronto per la lettura del file di input e la generazione dell'output.

**Regole di calcolo** - Da implementare secondo il file delle regole nella cartella Baobab.

## Utilizzo

```bash
python Baobab/consuntivobaobab.py -i "Piano lavoro DICEMBRE 25.xlsx" -o "OUT_BAOBAB.xlsx"
```

## Output

Il programma genera un file Excel con i seguenti fogli:
- **DettaglioBlocchi**: Dettaglio completo di tutti i blocchi
- **TotaliPeriodo**: Totali raggruppati per periodo (1-15, 16-31, MESE)
- **Discrepanze**: Eventuali discrepanze tra valori calcolati e forniti
- **Fogli per aeroporto** (VRN, BGY, ecc.): Dettaglio per ogni aeroporto
- **TOTALE**: Riepilogo totale per aeroporto e tour operator

## Note

- Il programma filtra per TOUR OPERATOR = "Baobab"
- Le regole di calcolo specifiche verranno implementate dopo la lettura del file delle regole

