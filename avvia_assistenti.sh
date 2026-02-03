#!/bin/bash
# Script per avviare l'applicazione Streamlit per Assistenti

cd "$(dirname "$0")"
streamlit run app_assistenti.py --server.port 8502
