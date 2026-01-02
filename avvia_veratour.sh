#!/bin/bash
# Script per avviare l'applicazione Veratour su una porta pulita

echo "🛑 Chiudendo eventuali processi sulla porta 8501..."
lsof -ti:8501 | xargs kill -9 2>/dev/null
lsof -ti:8503 | xargs kill -9 2>/dev/null
sleep 2

echo ""
echo "🚀 Avvio applicazione Veratour 2025..."
echo ""
echo "L'applicazione si aprirà automaticamente nel browser."
echo "Se non si apre, vai su: http://localhost:8503"
echo ""
echo "Per fermare l'applicazione, premi Ctrl+C"
echo ""

cd "$(dirname "$0")"
streamlit run app_streamlit.py --server.port 8503

