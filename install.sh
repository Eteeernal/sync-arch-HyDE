#!/bin/bash
# Wrapper simple para install.py
# Permite ejecutar ./install.sh en lugar de ./scripts/install.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PY="$SCRIPT_DIR/scripts/install.py"

# Verificar que el instalador Python existe
if [[ ! -f "$INSTALL_PY" ]]; then
    echo "❌ Error: Instalador no encontrado en $INSTALL_PY"
    exit 1
fi

# Ejecutar instalador Python con todos los argumentos
exec python3 "$INSTALL_PY" "$@"
