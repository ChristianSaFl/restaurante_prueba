#!/bin/sh
set -e

echo ">>> Inicializando base de datos..."
python -c "
from src.main.python.web.app import initialize_database
initialize_database()
print('>>> BD lista.')
"

echo ">>> Iniciando servidor..."
exec gunicorn \
    --workers 3 \
    --bind 0.0.0.0:8083 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    "src.main.python.web.app:app"
