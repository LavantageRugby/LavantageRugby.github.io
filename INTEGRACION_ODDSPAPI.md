# Integración con OddsPapi (sesión de cuotas → sello público)

La **sesión de cuotas** (Deportivo/Rugby) saca la referencia externa con
`~/analisis_deportivo/analisis/sello_op.py`; aquí se sella y se publica. **Nada se sella ni se
publica sin el OK explícito del CEO cada vez.**

## Flujo para sellar un pick (cuando el CEO lo autoriza)

1. **Sesión de cuotas** — buscar el partido y hacer la foto de Pinnacle al sellar:
   ```
   cd ~/analisis_deportivo
   python3 analisis/sello_op.py buscar "Leinster" "Munster"          # da el fixtureId
   python3 analisis/sello_op.py foto --fixture OP999 --mercado handicap --linea -7.5 --lado 1 --casa pinnacle > /tmp/foto.json
   ```
   `foto.json` trae: `fixture_id, market_id, outcome_id, sello.cuota (Pinnacle), contrario.cuota,
   sello.limite, crudo (fichero .json.gz), crudo_sha256, justo_sin_margen`.

2. **Aquí** — sellar pasando esa foto + el PICK REAL (la cuota/casa donde se apuesta de verdad, que
   normalmente NO es Pinnacle sino una casa blanda):
   ```
   python3 herramientas/sellar.py \
     --partido "Leinster-Munster" --liga "URC" --estrategia BLANDA-T30 \
     --mercado handicap --seleccion "Local -7.5" --linea -7.5 \
     --cuota 1.83 --casa 1xbet --confianza baja --saque 2026-12-12T20:00:00+01:00 \
     --op_foto /tmp/foto.json \
     --op_crudo ~/analisis_deportivo/datos/sellos_op/OP999_pinnacle_sello_XXXX.json.gz
   ```
   `--op_foto` rellena fixture/market/outcome + **pin_sello/pin_contrario/limite** (solo si la foto es
   de Pinnacle). `--op_crudo` descomprime el crudo, lo guarda como `snapshots/<id>.json` y comprueba
   que su sha256 **casa** con `crudo_sha256` (si no, no sella). Los flags explícitos siempre mandan.

3. **Publicar** (solo con OK del CEO): `git add -A && git commit && git push` ANTES del saque. La hora
   del push de GitHub + el sello OTS fijan el "antes del saque".

## Al revelar, tras el partido

1. **Sesión de cuotas** — cierre de los dos lados a la misma línea:
   ```
   python3 analisis/sello_op.py cierre --fixture OP999 --mercado handicap --linea -7.5 --lado 1 > /tmp/cierre.json
   ```
   Da `cierre.cuota` (nuestro lado) y `contrario.cuota` al cierre.
2. **Aquí**:
   ```
   python3 herramientas/revelar.py --id 0001-Leinster-Munster-handicap \
     --marcador "24-20" --resultado acierto \
     --cierre_pin <cierre.cuota> --cierre_contrario <contrario.cuota>
   ```
   El CLV sale **sin margen** (de-vig con el lado contrario) y a la misma línea.

## Mapa de campos (sello_op foto → sellar.py)

| sello_op.py `foto` | sellar.py |
|---|---|
| `fixture_id` | `--fixture_id` |
| `market_id` / `outcome_id` | `--market_id` / `--outcome_id` |
| `sello.cuota` (casa=pinnacle) | `--pin_sello` |
| `contrario.cuota` | `--pin_contrario` |
| `sello.limite` | `--limite` |
| `crudo` (.json.gz) + `crudo_sha256` | `--op_crudo` → `snapshots/<id>.json` + `snapshot_sha256` |

La **cuota/casa reales del pick** (`--cuota`, `--casa`) NO salen de la foto de Pinnacle: son donde se
apuesta de verdad (casa blanda). Pinnacle solo es la referencia para el CLV.

> Nota: si Pinnacle no tiene histórico de un partido menor (OddsPapi `404`), la sesión de cuotas usa
> `--casa 1xbet|22bet|bet365`; entonces esa foto NO rellena pin_sello/pin_contrario (no es Pinnacle) y
> el CLV de ese pick queda sin medir contra el cierre (se reporta aparte).
