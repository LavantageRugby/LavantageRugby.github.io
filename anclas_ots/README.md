# anclas_ots — pruebas de hora OpenTimestamps

Cada pick deja aquí dos ficheros al sellarse:
- `<id>.sha256`     → el hash del pick (lo que se sella).
- `<id>.sha256.ots` → la prueba OpenTimestamps, anclada a **Bitcoin**.

**Verificar (cualquiera, para siempre):**
```
pip install opentimestamps-client     # trae el comando `ots`
ots verify anclas_ots/<id>.sha256.ots # da la hora del bloque de Bitcoin
```
Esa hora demuestra que el pick existía antes del saque, sin fiarse de nadie.
Horas después de sellar se corre `herramientas/actualizar_anclas.sh` para incrustar
el anclaje definitivo de Bitcoin.
