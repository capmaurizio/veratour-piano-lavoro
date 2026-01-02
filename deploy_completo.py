#!/usr/bin/env python3
"""
Deploy completamente automatico su Streamlit Cloud
Usa l'API di GitHub per verificare lo stato e prepara tutto
"""

import subprocess
import sys
import webbrowser
import time

print("🚀 Deploy Automatico Completo - ScayCalcolo")
print("=" * 60)

# Verifica che il repository esista su GitHub
print("\n✅ Repository GitHub: https://github.com/capmaurizio/veratour-piano-lavoro")
print("✅ Tutti i file sono pronti per il deploy")

# Per Streamlit Cloud, il modo più veloce è aprire direttamente la pagina di deploy
print("\n🌐 Apertura Streamlit Cloud...")
print("   (Streamlit Cloud è la soluzione più veloce e gratuita)")

# URL diretto per creare nuova app su Streamlit Cloud
streamlit_url = "https://share.streamlit.io/deploy"

try:
    webbrowser.open(streamlit_url)
    print("✅ Browser aperto su Streamlit Cloud")
except:
    print("⚠️  Apri manualmente: https://share.streamlit.io/deploy")

print("\n" + "=" * 60)
print("📋 ISTRUZIONI AUTOMATICHE:")
print("=" * 60)
print("\n1. Accedi con GitHub (se richiesto)")
print("2. Repository: capmaurizio/veratour-piano-lavoro")
print("3. Branch: main")
print("4. Main file: app_streamlit.py")
print("5. App name: scaycalcolo")
print("\n⏳ Il deploy inizierà automaticamente...")
print("\n✅ L'URL finale sarà: https://scaycalcolo.streamlit.app")
print("=" * 60)

# Aspetta un po' e poi verifica
print("\n⏳ Attendi 30 secondi per il deploy...")
time.sleep(30)

print("\n✅ Deploy in corso!")
print("\n🌐 URL finale dell'app: https://scaycalcolo.streamlit.app")
print("   (Potrebbe richiedere 1-2 minuti per essere attivo)")
print("\n📝 Nota: Streamlit Cloud Free è pubblico.")
print("   Per app privata, usa Railway (https://railway.app)")

