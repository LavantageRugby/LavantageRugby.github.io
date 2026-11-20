# Registro público verificable — Rugby (foco Pro D2)

Registro **honesto y a prueba de trucos** de selecciones de rugby **prepartido**,
centrado en **Pro D2** (2ª división francesa). El objetivo no es vender humo: es
**demostrar, con pruebas que cualquiera puede comprobar**, si hay o no una ventaja real.

## Cómo funciona (anti-truco)

Cada pick se **sella ANTES del saque** con un esquema *commit-reveal*:

1. **Al sellar** (`herramientas/sellar.py`) se publica solo: `id`, **hora de sello**,
   partido, liga, mercado y un **hash SHA-256**. El pick real (lado, línea, cuota) queda
   **en secreto** hasta después del partido. Así nadie puede copiarlo ni mover la línea,
   y queda probado que existía antes del saque.
2. **Tras el partido** (`herramientas/revelar.py`) se revela el pick completo + marcador +
   acierto/fallo + la **cuota de cierre de Pinnacle** (para el CLV). El hash **no cambia**.
3. **Cualquiera** puede ejecutar `python3 herramientas/verificar.py` y comprobar que:
   - cada pick revelado **coincide exactamente** con el hash sellado (imposible retocarlo),
   - la **hora de sello es anterior al saque**,
   - y ver el balance y el **CLV medio** (si batimos la línea de cierre de Pinnacle).

## Qué se mide

- **Balance** (aciertos/fallos, neto en unidades): cuánto se ganó en esta muestra.
- **CLV (valor de línea de cierre)**: si las selecciones **baten el cierre de Pinnacle**.
  Es lo que separa **ventaja real** de **suerte**. Perseguimos los dos.

## Dos trampas que NO se pueden hacer aquí

- **Esconder los perdidos:** los sellos van **encadenados** (cada uno lleva el hash del anterior) y
  **todo pick sellado cuyo partido ya se jugó tiene que estar revelado**. No se puede publicar diez y
  revelar solo los que ganan: `verificar.py` lo caza.
- **Falsear la hora:** la fecha del commit de git no cuenta (la pone el autor). Cada pick se **sella
  con OpenTimestamps**, anclado a **Bitcoin**: una prueba de hora permanente que cualquiera comprueba
  para siempre (`ots verify anclas_ots/<id>.sha256.ots`), sin fiarse de nadie. La hora de push de
  GitHub sirve de apoyo inmediato (pero caduca ~90 días). Regla: sellar y empujar **antes del saque**.
  Detalle en [METODOLOGIA.md](METODOLOGIA.md).

## Honestidad (lo que esto NO es)

- **No es consejo de inversión** ni una promesa de ganancias. El rugby tiene **varianza alta**.
- Una muestra pequeña puede engañar: hace falta **volumen (50+ picks)** antes de concluir nada.
- Las unidades son **simuladas**, para medir rendimiento; no representan dinero apostado.
- Se publican **aciertos y fallos por igual**. Nada se borra. Esa es toda la gracia.

Ver [METODOLOGIA.md](METODOLOGIA.md) para las reglas de sellado y cálculo.
