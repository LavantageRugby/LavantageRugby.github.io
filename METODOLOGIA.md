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

2. **La prueba de la HORA no es la fecha del commit de git.** Esa fecha la pone el autor y se puede
   falsear. La prueba real de que el pick existía antes del saque es la **hora de PUSH que registra
   GitHub** (queda en el historial de la plataforma y **no es reescribible**). Por eso la regla es:
   **sellar y hacer `git push` ANTES del saque.** Además la rama `main` va **protegida: sin
   force-push y con historial lineal**, para que no se pueda reescribir la historia. (Refuerzo
   opcional futuro: sello OpenTimestamps anclado a Bitcoin.)

## Datos que entran en cada decisión (modelo casero)

Alineaciones y rotaciones, forma y H2H, localía, bajas, banco, y contexto físico: **tiempo,
humedad, punto de rocío, viento y tipo de césped (natural/sintético)**. Base estadística propia.

## Cálculo

- **Escala de stake por confianza**: baja 1 u · media-baja 1,5 · media 2 · media-alta 2,5 · alta 3.
- **Neto**: acierto = stake × (cuota − 1); fallo = −stake; nula = 0.
- **Cuota registrada** = la disponible **en el momento del sello** (así el CLV compara contra el cierre).
- **CLV** = cuota sellada × prob. implícita del **cierre de Pinnacle** − 1. `> 0` = batió el cierre.
  (El de-vig fino de Pinnacle se aplica en el cálculo agregado; aquí se guarda el dato base.)

## Alcance y prudencia

- Foco en **Pro D2** (donde la señal apareció y donde el mercado es más blando/ineficiente).
- Otras ligas pueden registrarse, pero **URC y Top 14 no han mostrado ventaja**: se tratan aparte.
- **Conclusiones solo con volumen** (objetivo ≥ 50 picks de Pro D2 fuera de muestra).
- **Precio**: conseguir mejor cuota pesa tanto como el modelo; se busca el mejor precio disponible.
