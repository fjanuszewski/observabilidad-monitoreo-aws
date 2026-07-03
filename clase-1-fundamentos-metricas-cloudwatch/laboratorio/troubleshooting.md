# Troubleshooting y escenarios de exploración — Clase 1

Guía de diagnóstico para el laboratorio de fundamentos, métricas y monitoreo de EC2
con CloudWatch. Cubre los problemas frecuentes y los escenarios de investigación
propuestos.

---

## Problemas frecuentes

### 1. El agente de CloudWatch no publica métricas del SO

**Síntoma:** el namespace `CWAgent` está vacío o no muestra `mem_used_percent` /
`disk_used_percent` para tu `InstanceId`.

**Causas típicas:**
- El IAM instance profile no tiene `CloudWatchAgentServerPolicy` (falta permiso
  para `PutMetricData` y para leer la config en SSM).
- El agente está detenido o nunca arrancó (UserData falló).

**Diagnóstico:**
```bash
# Conectarse sin SSH
aws ssm start-session --target <INSTANCE_ID> --region us-east-1

# Estado del agente (debe decir "running")
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a status

# Log del agente
sudo tail -n 100 /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log
```

---

### 2. Confundir métricas del hipervisor con las del SO

**Síntoma:** buscás `mem_used_percent` o `disk_used_percent` en el namespace
`AWS/EC2` y no aparecen.

**Explicación:** EC2 **nunca** emite memoria ni uso de disco por filesystem de forma
nativa. El hipervisor no ve dentro del SO invitado. Esas métricas viven en el
namespace **`CWAgent`** y solo existen si el agente está corriendo y configurado.
Lo que sí emite el hipervisor: `CPUUtilization`, `NetworkIn/Out`,
`DiskReadOps/WriteOps`, `StatusCheckFailed`, etc.

---

### 3. La instancia no aparece en Systems Manager / Session Manager

**Síntoma:** no podés iniciar sesión desde SSM; la instancia no figura en
*Fleet Manager* / *Session Manager*.

**Causas típicas:**
- Falta `AmazonSSMManagedInstanceCore` en el rol de la instancia.
- Falta salida a internet (o VPC endpoints de SSM) — revisá la ruta al IGW.
- El SSM Agent no está corriendo todavía (esperá 2–3 minutos tras el arranque).

Sin esto no se puede diagnosticar el agente ni recuperar la config desde
Parameter Store.

---

### 4. Configuración del agente inválida o no encontrada en SSM

**Síntoma:** el agente no carga la config y no publica métricas.

**Causas típicas:** JSON malformado, nombre del parámetro mal referenciado en el
UserData, o región incorrecta.

**Diagnóstico:**
```bash
# Salida del UserData (bootstrap del primer arranque)
sudo cat /var/log/cloud-init-output.log

# Confirmar que el parámetro existe y ver su contenido
aws ssm get-parameter \
  --name /observabilidad/obs-clase-1/cloudwatch-agent-config \
  --region us-east-1 --query Parameter.Value --output text
```

---

### 5. Falta de datos por resolución / retención o zona horaria

**Síntoma:** parece que "faltan" datapoints.

**Causas típicas:**
- Esperar métricas cada 1 minuto cuando el monitoreo detallado de EC2 no está
  habilitado (default 5 minutos para `AWS/EC2`).
- Interpretar mal la agregación de alta resolución (los datos de 1 s se agregan
  tras 3 horas).
- Seleccionar un rango de tiempo o timezone equivocado en la consola, que "oculta"
  datapoints existentes.

**Solución:** ampliá el rango temporal, ajustá el período (Statistic/Period) y
verificá el timezone del gráfico.

---

### 6. Errores o costos inesperados con PutMetricData

**Síntoma:** throttling de la API o proliferación de métricas.

**Causas típicas:**
- Exceder el rate de `PutMetricData` (throttling).
- Dimensiones de alta cardinalidad: cada combinación
  `namespace + nombre + dimensiones` cuenta como una métrica única y facturable.

**Solución:** limitá la cardinalidad de dimensiones; para volúmenes altos usá
**Embedded Metric Format (EMF)**, que embebe métricas en logs y evita llamadas
síncronas.

---

### 7. El stack queda en ROLLBACK_COMPLETE

**Síntoma:** la creación falla y CloudFormation revierte.

**Solución:** abrí **Events**, buscá el primer error (arriba del rollback) y corregí
el parámetro o permiso indicado. Borrá el stack fallido antes de reintentar.

---

## Escenario de investigación (guiado)

**Objetivo:** comparar las métricas del SO (`mem_used_percent`, `disk_used_percent`)
con las del hipervisor (`CPUUtilization`); luego detener el agente y diagnosticar por
qué dejan de llegar las métricas del SO usando SSM Session Manager y los logs del
agente.

### Paso 1 — Comparar SO vs hipervisor

En **CloudWatch › Metrics**, poné en el mismo gráfico:
- `CWAgent` → `mem_used_percent`
- `AWS/EC2` → `CPUUtilization`

Observá que ambas conviven pero provienen de fuentes distintas: una la publica el
agente desde dentro del SO, la otra la emite el hipervisor.

### Paso 2 — Generar carga (opcional) y observar CPUUtilization

Desde una sesión de Session Manager:
```bash
# Estresar 1 core durante 120 segundos (Ctrl-C para cortar)
timeout 120 bash -c 'while true; do :; done'
```
Mirá subir `CPUUtilization` en `AWS/EC2` en los minutos siguientes.

### Paso 3 — Detener el agente

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a stop
```

Esperá 5–10 minutos y volvé a mirar el gráfico combinado.

**Resultado esperado:** las series de `CWAgent` (`mem_used_percent`,
`disk_used_percent`) **dejan de recibir puntos nuevos**, mientras que
`CPUUtilization` (`AWS/EC2`) **sigue llegando**. Conclusión: las métricas del SO
dependen del agente; las del hipervisor no.

### Paso 4 — Diagnosticar con los logs del agente

```bash
sudo tail -n 50 /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log
```
El log confirma que el agente fue detenido. En un caso real de fallo, este log
(junto con `/var/log/cloud-init-output.log`) muestra la causa raíz: config
inválida, permisos faltantes o el proceso caído.

### Paso 5 — Reanudar el agente

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config -m ec2 -s \
  -c ssm:/observabilidad/obs-clase-1/cloudwatch-agent-config
```

Tras 3–5 minutos, las métricas del SO vuelven a aparecer en `CWAgent`.

---

## Escenarios de exploración adicionales

- **Alta resolución:** editá la config en Parameter Store bajando
  `metrics_collection_interval` a `10` y recargá el agente con `fetch-config`.
  Observá el cambio de granularidad.
- **Metric math:** creá una métrica derivada (por ejemplo, promedio móvil de
  `mem_used_percent`) en el editor de métricas.
- **Metrics Insights:** en la pestaña **Query** probá
  `SELECT AVG(mem_used_percent) FROM CWAgent GROUP BY InstanceId`.
- **Detección de anomalías:** activá anomaly detection sobre `CPUUtilization` y
  mirá cómo se entrena la banda esperada.
