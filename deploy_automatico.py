#!/usr/bin/env python3
"""
Script per deploy automatico su Railway
Richiede: pip install requests
"""

import requests
import json
import sys
import webbrowser
import time

print("🚀 Deploy Automatico - ScayCalcolo")
print("=" * 50)

# Railway richiede autenticazione OAuth, quindi apriamo il browser
print("\n📋 Istruzioni per deploy automatico:")
print("\n1. Apri questo link nel browser:")
print("   https://railway.app/new")
print("\n2. Accedi con GitHub")
print("\n3. Clicca 'Deploy from GitHub repo'")
print("\n4. Seleziona: capmaurizio/veratour-piano-lavoro")
print("\n5. Railway rileva automaticamente Streamlit e fa il deploy")
print("\n6. Rinomina il servizio in 'scaycalcolo' nelle impostazioni")
print("\n" + "=" * 50)

# Apri automaticamente il browser
try:
    webbrowser.open("https://railway.app/new")
    print("\n✅ Browser aperto automaticamente!")
    print("\n⏳ Attendi che Railway completi il deploy...")
    print("   (Di solito richiede 2-3 minuti)")
except Exception as e:
    print(f"\n⚠️  Impossibile aprire il browser automaticamente: {e}")
    print("   Apri manualmente: https://railway.app/new")

print("\n✅ Setup completato!")
print("\n📝 Nota: Railway fa auto-deploy ad ogni push su GitHub")
print("   L'app sarà privata di default e si chiamerà 'scaycalcolo'")

