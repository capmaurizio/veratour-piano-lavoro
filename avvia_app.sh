#!/bin/bash
# Script per avviare l'app Streamlit

cd "$(dirname "$0")"
echo "🚀 Avvio applicazione Streamlit..."
echo "📂 Directory: $(pwd)"
echo ""
echo "L'applicazione sarà disponibile su:"
echo "👉 http://localhost:8501"
echo ""
echo "Premi CTRL+C per fermare l'applicazione"
echo ""

streamlit run app_streamlit.py --server.port 8501

