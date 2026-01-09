#!/bin/bash

# Start the cron service in the background
service cron start

# Run the Streamlit app
# --server.port=8080: Matches the internal_port in fly.toml
# --server.address=0.0.0.0: Allows external connections (required for Docker/Fly)
python3 -m streamlit run src/app_dashboard.py --server.port=8080 --server.address=0.0.0.0