#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entry point per Streamlit Cloud
Importa e avvia l'app Veratour dalla sottocartella
"""

import sys
import os

# Aggiungi la cartella Veratour al path Python
veratour_dir = os.path.join(os.path.dirname(__file__), 'Veratour')
if os.path.exists(veratour_dir):
    sys.path.insert(0, veratour_dir)

# Importa direttamente il modulo
import importlib.util

# Carica il modulo app_streamlit da Veratour
app_path = os.path.join(veratour_dir, 'app_streamlit.py')
spec = importlib.util.spec_from_file_location("app_streamlit_veratour", app_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)

# Esegui il codice dell'app (tutto il codice in app_streamlit.py viene eseguito all'import)
# Non serve fare altro, Streamlit eseguirà automaticamente il codice
