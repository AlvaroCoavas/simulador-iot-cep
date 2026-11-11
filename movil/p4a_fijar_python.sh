#!/bin/sh
# ============================================================================
#  Fija la version de Python que usa python-for-android para compilar el APK.
#
#  POR QUE:
#  python-for-android (rama master) compila el APK con CPython 3.14.2, pero
#  las ruedas de pyjnius y Kivy para Android no se publican (todavia) para
#  cp314, asi que el build falla al buscar la rueda:
#
#      ERROR: No matching distribution found for pyjnius==1.7.0
#
#  Python 3.11 si tiene ruedas de todo (Kivy cp311, pyjnius cp311) y es una
#  version que python-for-android soporta sin problemas. Cambiando el
#  `version` de las recetas `python3` y `hostpython3` (que deben coincidir),
#  el APK se compila con Python 3.11.
#
#  USO:  sh movil/p4a_fijar_python.sh [3.11.13]
# ============================================================================
set -e

VERSION_DESTINO="${1:-3.11.13}"

# --- Localiza el paquete pythonforandroid ------------------------------------
RECETAS=""
if python -c "import pythonforandroid" >/dev/null 2>&1; then
    RECETAS=$(python -c "import os, pythonforandroid; print(os.path.join(os.path.dirname(pythonforandroid.__file__), 'recipes'))")
else
    # p4a todavia no esta instalado: se busca en las rutas habituales.
    for base in \
        "$HOME/.local/lib"/python*/site-packages \
        "$HOME/.venv/lib"/python*/site-packages \
        /usr/local/lib/python*/site-packages \
        /usr/lib/python*/site-packages
    do
        if [ -d "$base/pythonforandroid/recipes" ]; then
            RECETAS="$base/pythonforandroid/recipes"
            break
        fi
    done
fi

if [ -z "$RECETAS" ]; then
    echo "  AVISO: no se encuentra python-for-android; se deja como esta."
    exit 0
fi

echo "  recetas de p4a: $RECETAS"

for r in python3 hostpython3; do
    f="$RECETAS/$r/__init__.py"
    if [ ! -f "$f" ]; then
        echo "  (no se encuentra la receta $r, se omite)"
        continue
    fi
    sed -i -E "s/^version = .[0-9]+\.[0-9]+\.[0-9]+./version = '$VERSION_DESTINO'/" "$f"
    echo "  $r -> $(grep -m1 '^version' "$f")"
done

echo "  Python fijado a $VERSION_DESTINO"
