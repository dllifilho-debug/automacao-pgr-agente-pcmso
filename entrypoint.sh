#!/bin/sh
set -e

python -m agente_medico.superficie.materializar_secrets
exec streamlit run app_matriz.py --server.port="${PORT:-8501}" --server.address=0.0.0.0
