# 🚀 Come Avviare l'Applicazione

## Metodo 1: Terminale (Consigliato)

1. Apri il **Terminale** (applicazione "Terminale" su macOS)

2. Copia e incolla questo comando:

```bash
cd /Users/mauriziocapitanio/Documents/scay/CalcoloPianoLavoro && streamlit run app_streamlit.py --server.port 8501
```

3. Premi **Invio**

4. Aspetta che appaia questo messaggio:
   ```
   You can now view your Streamlit app in your browser.
   Local URL: http://localhost:8501
   ```

5. Apri il browser e vai a: **http://localhost:8501**

---

## Metodo 2: Script Bash

1. Apri il **Terminale**

2. Esegui:
```bash
cd /Users/mauriziocapitanio/Documents/scay/CalcoloPianoLavoro
./avvia_app.sh
```

---

## Se Vedi Errori

### Errore: "ModuleNotFoundError"
Installa le dipendenze:
```bash
cd /Users/mauriziocapitanio/Documents/scay/CalcoloPianoLavoro
pip install -r requirements.txt
```

### Errore: "Port already in use"
Usa una porta diversa:
```bash
streamlit run app_streamlit.py --server.port 8502
```

### Errore: "Permission denied"
Dai i permessi allo script:
```bash
chmod +x avvia_app.sh
```

---

## Verifica che Funzioni

Dopo l'avvio, dovresti vedere:
- ✅ Interfaccia web con titolo "Calcolo Piano Lavoro - Multi-Tour Operatour"
- ✅ Sezione per caricare file Excel
- ✅ Sidebar con opzioni di calcolo

---

## Fermare l'Applicazione

Nel terminale dove è in esecuzione, premi: **CTRL + C**

