# Metodología y reglas de sellado

Reglas **declaradas de antemano y fijas** (la consistencia es parte de la honestidad).

## Cuándo se sella cada pick

- **Hándicaps**: se sellan **en cuanto salen las alineaciones** — ~**24 h** antes en Pro D2 /
  clubes, hasta ~**48 h** en selecciones. Cuanto antes del cierre, **más fuerte la prueba**
  (más recorrido de línea por batir).
- **Totales**: se sellan **cuando la casa los publica** (normalmente por la mañana del día del
  partido). No hace falta dar todo junto: **cada pick se sella por separado, con su propia hora.**
- **Una vez sellado, el pick queda BLOQUEADO.** Aunque haya un cambio de última hora (lesión,
  alineación tardía), no se toca. Clavarlo con antelación es precisamente el mérito; los cambios
  tardíos son parte de la varianza que se intenta batir.

## Garantías de integridad (para el escéptico)

Un registro así tiene dos agujeros clásicos. Los dos están tapados y **`verificar.py` falla si se
incumplen**:

1. **No se puede esconder un perdido ("cherry-picking").** Los sellos van **encadenados**: cada pick
   incluye el hash del anterior (`prev_hash`) y un número de orden (`seq`). No se puede borrar,
   insertar ni reordenar ningún pick sin romper la cadena. Y **todo pick sellado cuyo partido ya se
   jugó TIENE que estar revelado**: si uno queda "sellado para siempre" después de su saque, el
   verificador lo marca como posible perdido escondido. → Si se sella, se revela. Siempre.

2. **La prueba de la HORA no es la fecha del commit de git** (esa la pone el autor y se puede
   falsear). La hora se prueba en **dos capas**:
   - **Permanente (la que vale para auditar): OpenTimestamps.** Al sellar, el hash del pick se
     **sella con OpenTimestamps** y queda anclado en la **cadena de Bitcoin**. La prueba vive en
     `anclas_ots/<id>.sha256.ots` y **cualquiera** la comprueba para siempre, sin fiarse de nadie:
     `ots verify anclas_ots/<id>.sha256.ots` → da la hora del bloque de Bitcoin, que demuestra que
     el pick existía antes del saque. (Horas después de sellar se corre
     `herramientas/actualizar_anclas.sh` para incrustar el anclaje definitivo de Bitcoin.)
   - **Inmediata (apoyo): la hora de PUSH de GitHub** (no reescribible, pero la API de eventos solo
     la guarda ~90 días → sirve de refuerzo a corto plazo, no de prueba permanente). Regla igual:
     **sellar, `git push` y que OTS selle, todo ANTES del saque.**
   La rama `main` va **protegida: sin force-push y con historial lineal**, para que no se pueda
   reescribir la historia.

## Datos que entran en cada decisión (modelo casero)

Alineaciones y rotaciones, forma y H2H, localía, bajas, banco, y contexto físico: **tiempo,
humedad, punto de rocío, viento y tipo de césped (natural/sintético)**. Base estadística propia.

## Cálculo

- **Escala de stake por confianza**: baja 1 u · media-baja 1,5 · media 2 · media-alta 2,5 · alta 3.
- **Neto**: acierto = stake × (cuota − 1); fallo = −stake; nula = 0.
- **Cuota registrada** = la disponible **en el momento del sello** (así el CLV compara contra el cierre).
- **CLV** = cuota sellada × prob. justa del **cierre de Pinnacle a la MISMA línea** − 1. `> 0` = batió
  el cierre. La prob. justa se calcula **sin margen** (de-vig) con la cuota del lado contrario cuando
  se aporta; si no, se usa `1/cierre` (con margen, aproximado) y queda marcado. **Siempre se lee junto
  al ROI** (ver más abajo).
- **Staking casi plano (a propósito).** En la práctica la inmensa mayoría de picks van a **1 u**,
  alguno a 1,5 y **rara vez (casi nunca) 2**. Es deliberado: así el resultado depende de **acertar el
  pick**, no de "haber acertado con el tamaño de la apuesta". Hace el registro más fácil de auditar.

## Alcance y prudencia

- Foco en **Pro D2** (donde la señal apareció y donde el mercado es más blando/ineficiente).
- Otras ligas pueden registrarse, pero **URC y Top 14 no han mostrado ventaja**: se tratan aparte.
- **Conclusiones solo con volumen** (objetivo ≥ 50 picks de Pro D2 fuera de muestra).
- **Precio**: conseguir mejor cuota pesa tanto como el modelo; se busca el mejor precio disponible.

## Lo que pide un sindicato serio (y cómo lo cubrimos)

Un sindicato no se fía de un número bonito; pide pruebas concretas. Qué guardamos y cómo se presenta:

1. **Que la cuota existía de verdad.** En cada sello van **cuota, casa, selección, línea exacta y
   hora**. Cuando es posible, además la **foto del mercado de Pinnacle en ese mismo minuto**
   (`pin_sello` = cuota de Pinnacle a nuestra misma selección/línea al sellar). *Pendiente: enganchar
   la captura externa automática (OddsPapi / The Odds API) desde las sesiones de cuotas, para que ese
   snapshot lo firme una fuente de fuera y no solo nosotros.*
2. **Límite y liquidez.** `limite` = cuánto se podía jugar a ese precio (límite de la casa o dinero en
   Betfair). Una ventaja en mercados de 200–500 € vale poco; se enseña, no se esconde.
3. **CLV bien medido.** Contra el **cierre SIN MARGEN de Pinnacle y a la MISMA línea** (`revelar.py`
   lo de-viga con la cuota del lado contrario). Se da **media, % que bate el cierre y, SIEMPRE, junto
   al ROI**. Lección propia que no olvidamos: en fútbol medimos **CLV +4,9 % con ROI −4,7 %** (n=243)
   → **el CLV solo NO es prueba de ganancia**. Van juntos siempre.
4. **Muestra.** Para un sindicato, con menos de ~**300–500 picks** no hay nada que defender (el ≥50 de
   arriba es para nuestra propia confianza en la señal, no para vender). Se da **n, ROI, IC95, p** y el
   resultado **quitando el mejor 5 %** (que no dependa de cuatro golpes de suerte).
5. **Antelación al saque.** Se guarda **cuántos minutos antes del saque** se selló cada pick. No es lo
   mismo batir el cierre metiéndola 3 días antes en línea blanda que a 1 hora del saque.
6. **Todo declarado antes** (esta metodología): stake casi plano, rango de cuotas, ligas y mercados.
   **Nada de borrar picks ni de picks "de prueba"** (la cadena + OTS lo impiden).
7. **Lo que de verdad hacen: período de prueba EN VIVO.** El histórico solo sirve para que acepten la
   prueba; luego reciben los picks **en tiempo real** (API o Telegram privado) y miden SU propio CLV y
   su precio conseguido. Por eso importan la **latencia de envío** y que los picks sean **exclusivos**:
   publicarlos en abierto antes del saque mata su valor. El commit-reveal encaja justo por eso (no
   enseña el pick hasta después del partido).
