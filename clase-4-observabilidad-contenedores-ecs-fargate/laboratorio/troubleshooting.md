# Troubleshooting y exploración · Clase 4

Problemas frecuentes del laboratorio de observabilidad de contenedores (ECS +
Fargate) y escenarios para experimentar. Varios de estos síntomas son
**reproducibles a propósito** para practicar diagnóstico correlacionando
métricas de Container Insights con logs.

## Problemas frecuentes

### 1. La tarea no arranca: se queda en PENDING o entra en loop de reinicio
**Síntoma:** el servicio nunca llega a `runningCount == 1`, o la tarea arranca y
se detiene una y otra vez. **Causas típicas:**
- **No hay salida a Internet:** Fargate no puede bajar la imagen pública. En este
  lab la tarea corre con `AssignPublicIp: ENABLED` en una subred con ruta
  `0.0.0.0/0` al Internet Gateway. Sin IP pública ni IGW (o con una subred
  privada sin NAT) el pull falla con `CannotPullContainerError`.
- **Execution role sin permisos:** el pull de imagen y la creación de log streams
  los hace el **execution role** (`AmazonECSTaskExecutionRolePolicy`). Revisá que
  el rol exista y esté asociado en la task definition.
**Dónde mirar:** `ECS › Cluster › Servicio › Tasks › (tarea detenida) › Stopped
reason`, y los eventos del servicio en la pestaña **Events**.

### 2. No aparecen logs de la app en `/<prefijo>/app`
**Síntoma:** el log group de la app está vacío aunque la tarea corre.
**Causas típicas:**
- **Task role sin permisos de Logs:** FireLens/Fluent Bit corre dentro de la
  tarea y usa el **task role** para escribir en CloudWatch. Debe tener
  `logs:CreateLogStream` y `logs:PutLogEvents` sobre el log group de la app.
- **Log group inexistente y `auto_create_group: "false"`:** la plantilla ya crea
  el log group, pero si lo borrás a mano Fluent Bit no lo recrea. Volvé a crearlo
  o poné `auto_create_group: "true"`.
- **El sidecar log_router no está sano:** si el contenedor FireLens no arranca,
  la app no tiene a quién entregar sus logs. Revisá `/<prefijo>/firelens`.

### 3. FireLens (Fluent Bit) falla o descarta registros
**Síntoma:** el log group de diagnóstico `/<prefijo>/firelens` muestra errores de
salida (throttling, `AccessDenied`, región equivocada). **Solución:**
- Verificá que las `Options` de salida del contenedor `app`
  (`region`, `log_group_name`) apunten al log group y región correctos.
- Confirmá los permisos del **task role** (ver punto 2).
- `enable-ecs-log-metadata: "true"` agrega metadatos de ECS (cluster, task ARN) a
  cada registro; si lo quitás perdés parte de la correlación infra ↔ log.

### 4. No hay métricas en Container Insights
**Síntoma:** el cluster no aparece o no muestra datos en Container Insights.
**Causas típicas:**
- **Container Insights no habilitado:** el cluster debe tener
  `containerInsights = enhanced` (o al menos `enabled`). Revisá
  `ECS › Cluster › (…)` o el setting del cluster.
- **Todavía no hay datos:** las métricas tardan **unos minutos** en aparecer tras
  el primer arranque de la tarea. Esperá 3–5 min.
- **Estás mirando el nivel equivocado:** enhanced expone métricas por cluster,
  servicio, **tarea** y **contenedor**; asegurate de bajar al nivel de tarea/
  contenedor para ver el CPU/memoria de cada uno.

### 5. Container Insights "enhanced" factura más de lo esperado
**Síntoma:** costo de CloudWatch más alto que un lab trivial. **Causa:** enhanced
observability emite muchas más métricas (por contenedor) que el modo estándar y
se factura por observación. **Solución:** para practicar, dejá el lab corriendo
**pocas horas** y limpiá; si solo necesitás lo básico, cambiá el cluster a
`containerInsights = enabled` (estándar).

### 6. El stack queda en ROLLBACK_COMPLETE / CREATE_FAILED
**Causas habituales:**
- **Colisión de nombres IAM:** el `NombrePrefijo` genera nombres de rol que ya
  existen. Cambiá el prefijo.
- **CIDR inválido o solapado:** ajustá `CidrVpc` / `CidrSubred`.
- **Falta `CAPABILITY_NAMED_IAM`:** la plantilla nombra roles; sin esa capability
  el deploy falla. **Solución:** abrí **Events**, buscá el primer error (arriba
  del rollback) y corregí el parámetro/capability indicado.

## Escenario de investigación (obligatorio)

**Objetivo:** explorar Container Insights a nivel de **tarea y contenedor**
(CPU/memoria), **forzar reinicios** del contenedor y **correlacionar** el pico de
métricas con los logs del contenedor para hallar la causa.

### Paso 1 — Línea base en Container Insights
En **CloudWatch › Container Insights › Performance monitoring**, elegí
`ECS Clusters` → tu cluster, y bajá al nivel de **Tasks** y **Containers**. Anotá
el uso normal de **CPU** y **memoria** del contenedor `app` (bajo, es un httpd
ocioso que solo imprime una línea cada 5 s).

### Paso 2 — Correlacionar con los logs
En la misma vista, seguí los logs de la app en `/<prefijo>/app` (o
`aws logs tail /<prefijo>/app --follow`). Vas a ver las líneas JSON `INFO` y, cada
10 iteraciones, una `WARN` ("latencia elevada simulada"). Esos son los logs que
FireLens ruteó desde el contenedor.

### Paso 3 — Forzar un reinicio del contenedor
Provocá que la tarea se reinicie para generar un evento observable:

```bash
# Opción A (recomendada): parar la tarea; el servicio (desiredCount=1) la recrea.
TASK_ARN=$(aws ecs list-tasks --cluster <prefijo>-cluster \
  --service-name <prefijo>-svc --query "taskArns[0]" --output text --region us-east-1)
aws ecs stop-task --cluster <prefijo>-cluster --task "$TASK_ARN" \
  --reason "lab: forzar reinicio para investigar" --region us-east-1

# Opción B: forzar un nuevo despliegue del servicio (reemplaza la tarea).
aws ecs update-service --cluster <prefijo>-cluster --service <prefijo>-svc \
  --force-new-deployment --region us-east-1
```

Para un pico de recursos más marcado, podés redeplegar el stack subiendo
`DesiredCount` momentáneamente o cambiando la imagen `ImagenApp`.

### Paso 4 — Correlacionar el pico con los logs y hallar la causa
1. En Container Insights, observá el **quiebre en las métricas** de la tarea: la
   tarea vieja desaparece, aparece una **nueva tarea** con su propio CPU/memoria
   arrancando desde cero (spike de arranque).
2. En el **seguimiento de despliegues (deployment tracking)** del servicio vas a
   ver el evento de reemplazo de tarea.
3. Alineá el **timestamp del reinicio** con los logs: en `/<prefijo>/app` la
   secuencia (`seq`) se **reinicia desde 1** cuando arranca la tarea nueva. Ese
   corte en la secuencia es la huella del reinicio en los logs, correlacionada
   con el spike de arranque en las métricas.

**Conclusión del análisis de causa raíz:** el pico de métricas coincide con el
arranque de una tarea nueva; los logs (secuencia reiniciada + metadatos de ECS
que agrega FireLens) confirman *qué* tarea/contenedor se reinició y *cuándo*. Esa
es la mecánica de correlación **infraestructura ↔ servicio ↔ log** que después
extendés a trazas con ADOT / Application Signals / X-Ray.

## Escenarios de exploración

- **Estándar vs enhanced:** cambiá el cluster a `containerInsights = enabled` y
  compará qué métricas desaparecen (perdés el detalle por contenedor). Volvé a
  `enhanced` para el resto del lab.
- **Rompé FireLens a propósito:** quitá `logs:PutLogEvents` del task role y mirá
  cómo el log group de la app deja de recibir eventos mientras `/<prefijo>/firelens`
  registra el `AccessDenied`. Es el patrón clásico de "las métricas están pero los
  logs no llegan".
- **Sumá WARN/ERROR:** editá el `Command` del contenedor `app` para emitir más
  líneas `WARN`/`ERROR` y usá **Logs Insights** para contar por `level`:
  ```
  fields @timestamp, level, msg
  | filter level = "WARN"
  | stats count() by bin(1m)
  ```
- **awslogs vs FireLens:** cambiá el log driver del contenedor `app` de
  `awsfirelens` a `awslogs` (driver directo a CloudWatch) y compará ventajas:
  `awslogs` es más simple; FireLens permite rutear a S3, OpenSearch o terceros y
  transformar registros.
- **APM (siguiente paso):** agregá un sidecar **ADOT collector** y activá
  **CloudWatch Application Signals** para empezar a ver trazas correlacionadas con
  estas métricas y logs (introducción del Módulo 4).
