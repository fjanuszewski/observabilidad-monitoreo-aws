# Troubleshooting y escenarios de exploración · Clase 2

Problemas frecuentes del pipeline de logs y escenarios para practicar diagnóstico.
Todos aplican al stack que despliega `template.yaml`.

---

## Escenario de investigación (el troubleshooting central)

**Objetivo:** generar líneas `ERROR` en la app de EC2, ver la alarma pasar a `ALARM`
y usar Logs Insights para localizar y contar los errores por período.

1. **Conectarte a la instancia por Session Manager** (sin SSH ni puertos abiertos):
   ```bash
   aws ssm start-session --target <INSTANCE_ID> --region us-east-1
   ```
2. **Inyectar errores** en el archivo que vigila el agente:
   ```bash
   for i in $(seq 1 10); do
     echo "$(date -u +%FT%TZ) ERROR request id=demo-$i status=500 msg='forced error'" \
       | sudo tee -a /var/log/app/app.log
   done
   ```
3. **Ver la alarma pasar a `ALARM`** (1–2 minutos):
   ```bash
   aws cloudwatch describe-alarms \
     --alarm-names obs-clase-2-errores-obs-clase-2 \
     --query "MetricAlarms[0].StateValue" --output text --region us-east-1
   ```
   Si configuraste `NotificationEmail` y confirmaste la suscripción SNS, llega el correo.
4. **Localizar y contar con Logs Insights** (CloudWatch › Logs › Logs Insights, log group
   `/obs/clase-2/app`, acotá el rango de tiempo primero):
   ```
   fields @timestamp, @message
   | filter @message like /ERROR/
   | stats count(*) as errores by bin(1m)
   | sort errores desc
   ```
5. **(Opcional) Live Tail** para ver los errores en streaming mientras los generás
   (solo en log groups clase STANDARD).

---

## Problemas frecuentes

### 1. La alarma nunca sale de `INSUFFICIENT_DATA` o no dispara
- **Causa:** un metric filter solo emite un dato cuando hay coincidencias; sin errores la
  métrica no publica ceros por sí sola.
- **Solución:** la plantilla ya usa `DefaultValue: 0` en la `MetricTransformation` y
  `TreatMissingData: notBreaching` en la alarma. Confirmá que la app esté generando ERROR
  y esperá uno o dos períodos de 60 s. Si cambiaste el patrón, revisá que siga contando.

### 2. El `FilterPattern` no matchea lo que esperás
- **Causa:** la sintaxis de patrones de metric filters distingue mayúsculas/minúsculas y
  difiere entre logs sin estructura (términos y frases) y JSON (`{ $.campo = "valor" }`).
  `ERROR` no matchea `error`.
- **Solución:** ajustá el `FilterPattern` del recurso `ErrorMetricFilter` y volvé a
  desplegar. Probá el patrón en **Logs › Metric filters › Test pattern** antes.

### 3. Los logs de EC2 no aparecen en el log group
- **Causa:** casi siempre el agente de CloudWatch mal configurado (ruta de archivo
  incorrecta, agente no corriendo) o el rol de la instancia sin permisos.
- **Solución:** entrá por SSM y revisá:
  ```bash
  sudo cat /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log
  ls -l /var/log/app/app.log
  sudo systemctl status app-logger.service
  ```
  El rol de la instancia debe tener `CloudWatchAgentServerPolicy`. Dale 3–5 minutos tras
  el `CREATE_COMPLETE`.

### 4. Costos por retención indefinida
- **Causa:** por defecto un log group guarda los logs para siempre; sin `RetentionInDays`
  el almacenamiento crece sin control.
- **Solución:** este lab fija `RetentionInDays` (7 por defecto). Ajustalo a tu política
  (1 día a 3653 días / 10 años) y/o usá `LogGroupClass=INFREQUENT_ACCESS` para logs poco
  consultados.

### 5. Datos sensibles ya escritos o no enmascarados
- **Causa:** una data protection policy solo enmascara eventos ingeridos **después** de
  aplicarla (no reescribe lo ya almacenado), y quien tenga `logs:Unmask` sigue viendo el
  valor real.
- **Solución:** aplicá la política antes de ingerir datos sensibles y controlá quién tiene
  el permiso `logs:Unmask`. (Este lab no la incluye por defecto; es un ejercicio del
  Módulo 4.)

### 6. Errores de cifrado con KMS al crear/asociar la clave
- **Causa:** si la key policy no autoriza al principal `logs.<region>.amazonaws.com`
  (`kms:GenerateDataKey`/`Decrypt`) con la condición de `SourceArn`/`EncryptionContext`
  correcta, la asociación falla o el log group deja de ingerir.
- **Solución:** la plantilla ya incluye esa key policy (statement `AllowCloudWatchLogs`
  con `ArnLike` sobre el ARN del log group). Si cambiás el `LogGroupName`, la condición se
  actualiza sola vía `Fn::Sub`. Verificá la key policy antes que los permisos IAM del
  usuario.

### 7. Consultas de Logs Insights lentas, truncadas o costosas
- **Causa:** escanean por rango de tiempo y volumen; sin acotar el período o sin filtrar
  temprano, tardan o se cortan.
- **Solución:** acotá el time range (por ejemplo, últimos 30 min), usá `filter` temprano y
  `stats`/`limit` para reducir el resultado.

### 8. El stack queda en `ROLLBACK_COMPLETE`
- **Causa:** algún recurso falló al crearse.
- **Solución:** abrí **CloudFormation › Events** y buscá el primer error (arriba del
  rollback). Causas típicas: no aceptar `CAPABILITY_NAMED_IAM`, `NotificationEmail` con
  formato inválido, o falta de VPC por defecto en la región.

---

## Escenarios de exploración

- **Retención:** redesplegá con `RetentionInDays=1` o `=30` y compará el log group.
- **Clase de log:** con `LogGroupClass=INFREQUENT_ACCESS` el stack no crea metric filter ni
  alarma (esa clase no los soporta); comprobá que igual podés consultar con Logs Insights.
- **Cifrado KMS:** `EnableKmsEncryption=true` y verificá la KMS key asociada al log group.
- **Umbral:** subí `ErrorThreshold` a 5 y observá cuántos errores hacen falta para disparar.
- **Patrón:** cambiá el `FilterPattern` a `"status=500"` y compará el conteo con `"ERROR"`.
- **Notificación:** completá `NotificationEmail`, confirmá la suscripción SNS y forzá un
  error para recibir el correo; luego observá la acción `OK` cuando la métrica baja.
