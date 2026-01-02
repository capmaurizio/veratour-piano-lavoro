#!/usr/bin/env python3
"""
Script per creare app 'scaycalcolo' su Render automaticamente
Richiede: pip install requests
"""

import requests
import json
import sys

# Ottieni API key da: https://dashboard.render.com/account/api-keys
API_KEY = "YOUR_RENDER_API_KEY"  # Sostituisci con la tua API key
SERVICE_NAME = "scaycalcolo"
REPO_URL = "https://github.com/capmaurizio/veratour-piano-lavoro"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

data = {
    "type": "web_service",
    "name": SERVICE_NAME,
    "repo": REPO_URL,
    "branch": "main",
    "buildCommand": "pip install -r requirements.txt",
    "startCommand": "streamlit run app_streamlit.py --server.port $PORT --server.address 0.0.0.0",
    "env": "python",
    "planId": "starter"  # Per app privata
}

try:
    response = requests.post(
        "https://api.render.com/v1/services",
        headers=headers,
        json=data
    )

    if response.status_code == 201:
        result = response.json()
        service = result.get('service', {})
        url = service.get('serviceDetails', {}).get('url', 'N/A')
        print(f"✅ App '{SERVICE_NAME}' creata con successo!")
        print(f"🌐 URL: {url}")
        print(f"🔒 App privata: Sì")
    else:
        print(f"❌ Errore: {response.status_code}")
        print(response.text)
        sys.exit(1)
except Exception as e:
    print(f"❌ Errore durante la creazione: {e}")
    sys.exit(1)
