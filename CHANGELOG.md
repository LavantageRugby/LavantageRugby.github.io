# Changelog del registro

## 2026-11-21 — Plazo de revelado (ventana de 5 h)

Regla nueva, **anunciada aquí antes de aplicarla**. Un pick sellado cuyo partido ya empezó tiene **5 horas
desde el saque** para revelarse. Durante ese plazo, `verificar.py` lo muestra como **"EN JUEGO / pendiente
de revelar"** (amarillo), ni como fallo ni como verde. Pasadas las 5 h sin revelar, salta la alerta roja
**"posible perdido escondido"** (integridad NO fiable).

**Motivo:** antes, el verificador marcaba "INTEGRIDAD: NO fiable" en cuanto un pick pasaba su saque, aunque
el partido siguiera jugándose y aún no se pudiera revelar (hace falta el resultado final y el cierre de
Pinnacle). Era un **falso positivo** durante ~2 h cada tarde de partidos. El plazo lo elimina **sin debilitar
la prueba**: la cadena (`seq`/`prev_hash`), los hashes y el estado sellado público siguen impidiendo borrar o
esconder un perdido; solo se da un margen razonable para revelar.

**Condiciones (fijas):** 5 h desde el saque, **igual para todos los deportes**, **no retroactivo**, y **no se
cambia caso a caso**.

## 2026-11-19

19/11/2026: corregidos los metadatos de 3 commits (picks #1 y #2). Los sha256 y las anclas en Bitcoin de los picks no cambian.
