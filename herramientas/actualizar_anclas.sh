#!/usr/bin/env bash
# Actualiza (upgrade) las pruebas OpenTimestamps: horas despues de sellar, cuando
# Bitcoin ha confirmado, esto incrusta el anclaje definitivo en los .ots. Correr cada
# dia (o antes de mandar el registro a un sindicato) y volver a commit+push.
#
#   bash herramientas/actualizar_anclas.sh
#
set -e
OTS="${OTS:-$HOME/.venv_ots/bin/ots}"
DIR="$(cd "$(dirname "$0")/.." && pwd)/anclas_ots"
if [ ! -x "$OTS" ]; then echo "No encuentro 'ots' en $OTS (instala opentimestamps-client)"; exit 1; fi
shopt -s nullglob
n=0
for f in "$DIR"/*.sha256.ots; do
  "$OTS" upgrade "$f" 2>&1 | sed "s#^#  $(basename "$f"): #" || true
  n=$((n+1))
done
echo "Procesadas $n pruebas. Si alguna quedo 'upgraded', haz: git add -A && git commit -m 'OTS: anclaje Bitcoin' && git push"
