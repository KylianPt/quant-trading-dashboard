#!/bin/bash

# Démarrer cron en arrière-plan
service cron start

# Démarrer l'application Streamlit
streamlit run src/app_dashboard.py --server.port=8501 --server.address=0.0.0.0