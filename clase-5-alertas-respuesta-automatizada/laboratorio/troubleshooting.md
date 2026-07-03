# Troubleshooting y exploración · Clase 5

Problemas frecuentes del cierre end-to-end (alarmas → EventBridge → SSM
Automation → SNS → dashboard), más escenarios para experimentar. Varios de estos
errores son **reproducibles a propósito** para practicar diagnóstico.

## Problemas frecuentes

### 1. No llega el email de las alarmas
**Síntoma:** la alarma pasa a `ALARM` pero no recibís nada.
**Causa más común:** la **suscripción SNS quedó `PendingConfirmation`**: al crear
el stack, AWS manda un correo de confirmación que hay que aceptar.
**Solución:** revisá spam, abrí el email de *AWS Notifications* y hacé clic en
*Confirm subscription*. Verificá el estado con:
```bash
aws sns list-subscriptions-by-topic --topic-arn <AlertTopicArn> --region us-east-1
```
Si `SubscriptionArn` dice `PendingConfirmation`, todavía no está activa.

### 2. La alarma de anomalía nunca dispara (o dispara siempre al principio)
**Síntoma:** `…-cpu-anomalia` se queda en `INSUFFICIENT_DATA` o marca anomalía
apenas se crea. **Causa:** la detección de anomalía necesita **historia** para
entrenar la banda (idealmente algunas horas/días); recién creada casi no tiene
línea base. **Solución:** dale tiempo a que acumule datos, o ajustá el ancho de
banda en `ANOMALY_DETECTION_BAND(m1, N)` (N más alto = banda más ancha = menos
sensible). Para el lab, la **alarma compuesta** exige además que la de métrica
esté en `ALARM`, lo que evita falsos positivos tempranos.

### 3. La alarma compuesta no pasa a ALARM aunque la CPU está alta
**Síntoma:** `…-cpu-alta` está en `ALARM` pero la compuesta sigue en `OK`.
**Causa:** la regla es `ALARM(cpu-alta) AND ALARM(cpu-anomalia)`: si la de
anomalía aún no considera el pico como anomalía (poca historia), la compuesta no
dispara. **Solución/decisión de diseño:** es el comportamiento buscado (reduce
ruido). Si querés que dispare solo con el umbral, cambiá el `AlarmRule` a
`ALARM(cpu-alta)` o usá `OR` en lugar de `AND`.

### 4. El runbook de SSM Automation no se ejecuta al saltar la alarma
**Síntomas y causas:**
- La regla de EventBridge apunta al ARN de la alarma **compuesta**; si la que
  saltó fue la de métrica sola, no matchea. Es intencional.
- **Permisos:** el rol `EventBridgeInvokeRole` necesita `ssm:StartAutomationExecution`
  y `iam:PassRole` sobre el rol de Automation. Están en la plantilla; si editaste
  el runbook, revisá que el ARN siga coincidiendo.
- **Verificá** la métrica de invocaciones/fallos de la regla y las ejecuciones:
```bash
aws ssm describe-automation-executions \
  --filters Key=DocumentNamePrefix,Values=<stack>-remediar-cpu --region us-east-1
```

### 5. El runbook arranca pero el RunCommand falla en la instancia
**Síntoma:** la Automation queda en `Failed` en el paso `RemediarCPU`.
**Causas típicas:**
- La instancia **no está registrada en SSM** (agente SSM o rol
  `AmazonSSMManagedInstanceCore`): mirá *Systems Manager › Fleet Manager*.
- Sin salida a internet / endpoints de SSM: revisá la ruta a IGW y el Security
  Group (salida abierta). **Solución:** confirmá que la instancia aparece como
  *Managed* antes de simular el incidente.

### 6. El widget de logs del dashboard aparece vacío
**Síntoma:** el widget de tipo *log* no muestra filas. **Causas:** (a) el
CloudWatch agent todavía no empezó a enviar `/var/log/obs-app.log`; (b) el log
group aún no tiene streams. **Solución:** esperá 2–3 min tras el arranque; el
cron de *latido* escribe una línea por minuto. Verificá:
```bash
aws logs describe-log-streams --log-group-name /observabilidad/<stack>/app --region us-east-1
```

### 7. El dashboard no muestra la métrica de memoria
**Causa:** `CWAgent/mem_used_percent` la publica el agente; si el agente no
arrancó (config de SSM mal referenciada, o `dnf install` falló), no hay datos.
**Solución:** conectate por Session Manager y corré
`amazon-cloudwatch-agent-ctl -a status`; si no está *running*, re-aplicá la
config `fetch-config -c ssm:<parámetro>`.

### 8. El stack queda en ROLLBACK_COMPLETE
**Causas habituales:** email inválido en `NotificationEmail` (rechazado por el
`AllowedPattern`), o falta `CAPABILITY_NAMED_IAM` al desplegar por CLI.
**Solución:** abrí **Events**, buscá el primer error (arriba del rollback) y
corregí el parámetro/capacidad indicado.

## Escenario de investigación (obligatorio)

**Incidente a simular:** un pico sostenido de **alto uso de CPU** en la instancia
dispara la cadena completa de respuesta.

### Paso 1 — Provocar el incidente
Desde Session Manager (o con `aws ssm send-command`, ver el Output
`SimularIncidenteCommand`), ejecutá dentro de la instancia:
```bash
/usr/local/bin/simular-incidente.sh &
```
Estresa la CPU al 100 % durante ~5 minutos y deja un `WARN` en
`/var/log/obs-app.log`.

### Paso 2 — Seguir la propagación de la alarma
En **CloudWatch › Alarms** (o `AlarmsConsoleUrl`):
1. `…-cpu-alta` pasa a `ALARM` (2 períodos de 1 min sobre el umbral).
2. `…-cpu-anomalia` marca el valor fuera de la banda.
3. Cuando **ambas** están en `ALARM`, `…-cpu-compuesta` pasa a `ALARM`.

### Paso 3 — Confirmar las dos reacciones
- **SNS:** llega el email de la alarma compuesta al destinatario suscripto.
- **EventBridge → SSM Automation:** se arranca el runbook `…-remediar-cpu`.
```bash
aws ssm describe-automation-executions \
  --filters Key=DocumentNamePrefix,Values=<stack>-remediar-cpu \
  --query "AutomationExecutionMetadataList[0].[AutomationExecutionStatus,ExecutionStartTime]" \
  --region us-east-1
```

### Paso 4 — Verificar la remediación
El runbook detiene la carga (`pkill stress-ng`) y escribe
`ACTION auto-remediacion…` en el log. La CPU baja, la compuesta vuelve a `OK` y
SNS envía el aviso de recuperación (acción `OK`).

### Paso 5 — Investigar en el dashboard y con Logs Insights
En el **dashboard unificado** vas a ver el pico de CPU, la banda de anomalía, el
estado de las alarmas y las líneas de log del incidente y de la remediación.
Cruzá con Logs Insights:
```
fields @timestamp, @message
| filter @message like /incidente|auto-remediacion/
| sort @timestamp desc
| limit 50
```

### Runbook operativo (documentar)
Dejá escrito, como práctica de operación en producción:
1. **Detección:** alarma compuesta `…-cpu-compuesta` en `ALARM`.
2. **Notificación:** email SNS al equipo on-call.
3. **Respuesta automática:** EventBridge → SSM Automation detiene la carga.
4. **Verificación:** dashboard + Logs Insights; confirmar retorno a `OK`.
5. **Escalamiento:** si la CPU no baja tras la remediación, revisar la instancia
   por Session Manager y considerar reinicio o scale-out.
6. **Post-incidente:** revisar umbrales, ancho de banda de anomalía y si el
   `AND` de la compuesta atrasó la detección.

## Escenarios de exploración

- **Cambiá el `AlarmRule` de la compuesta** de `AND` a `OR` y observá cómo baja
  la latencia de detección a costa de más ruido.
- **Ajustá `CpuAlarmThreshold`** (por ejemplo a 40 %) y mirá cómo dispara antes.
- **Ampliá/achicá la banda de anomalía** cambiando el `2` en
  `ANOMALY_DETECTION_BAND(m1, 2)` y compará falsos positivos.
- **Sumá un segundo target a EventBridge:** además del runbook, publicá a SNS o a
  una función Lambda para notificar a Slack/PagerDuty (o AWS Chatbot).
- **Agregá `TreatMissingData` distinto** (`breaching` vs `notBreaching`) y forzá
  datos faltantes deteniendo el agente; observá el efecto en el estado.
- **Extendé el runbook** con un paso que reinicie la instancia
  (`aws:changeInstanceState`) y practicá una remediación más agresiva.
- **Compará Logs Insights vs Athena** para el análisis: Logs Insights para lo
  reciente en CloudWatch Logs, Athena para lo archivado en S3 (Clase 3).
